#!/usr/bin/env python3
"""Enumerate the vitals ArtAssetIDs the *installed* client actually knows.

The skinning pack is a snapshot.  `reference/pack_manifest.tsv` came from the
Unofficial Update 46.2 pack, and the live client has moved on -- U46.2 has no
`U47_rivals`, `U48_feasts`, `U49_frozen` or `U50_neighbors_*` frames, and this
skin silently did not blank any of them.  A cosmetic frame whose ID is not
covered looks exactly like "the skin is broken".

So the second source of truth is the client itself.  `client_general.dat`
stores these names length-prefixed: one byte holding the length, then exactly
that many ASCII bytes.  That is an exact test, not a guess -- a candidate is
accepted only when the preceding byte equals its length, which throws away the
neighbouring record's bytes that a plain `strings` sweep drags in.

    python3 tests/scan_client.py [--dat PATH]

Writes two files, one name per line:

  reference/live_asset_ids.txt     vitals ArtAssetIDs the client knows.  T12
                                   fails on anything in scope and unblanked.
  reference/live_element_ids.txt   which of the dictionary's UI element IDs the
                                   client still has.  T13 fails on a named
                                   element that is gone -- the failure that is
                                   silent *and* total, because one stale ID
                                   aborts the whole panel override.

Re-run both after a game update.
"""

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))

DAT_CANDIDATES = [
    "~/Games/lotro/drive_c/Program Files (x86)/StandingStoneGames/"
    "The Lord of the Rings Online/client_general.dat",
    "~/.local/share/Steam/steamapps/common/Lord of the Rings Online/"
    "client_general.dat",
]

# Only the families this skin reasons about.  Everything else in the dat is
# noise for our purposes -- and the mini / pet / floaty families are picked up
# deliberately, so T12 can tell "new and out of scope" from "new and missed".
FAMILY = re.compile(
    r"(vitals|level_background|icon_pvp_rank|_stars_opponent|pvp_rank_half_star"
    r"|opponent_progress_overlay|selection_inanimate|Icon_LockTarget)", re.I)

RUN = re.compile(rb"[A-Za-z0-9_]{6,120}")

CHUNK = 32 * 1024 * 1024
MAXLEN = 80


def find_dat(explicit):
    if explicit:
        return os.path.expanduser(explicit)
    for cand in DAT_CANDIDATES:
        path = os.path.expanduser(cand)
        if os.path.isfile(path):
            return path
    return None


def dictionary_element_ids():
    """Every Element ID the U46.2 dictionary lists, across all panels."""
    path = os.path.join(HERE, "reference", "SkinDictionary.txt")
    raw = open(path, encoding="utf-8", errors="replace").read()
    root = ET.fromstring("<root>" + raw + "</root>")
    return {e.get("ID") for e in root.iter("Element") if e.get("ID")}


def scan(path, elements):
    """Every length-prefixed ASCII name of interest in the file.

    Returns (asset ids, element ids).  Only names in one of the two wanted
    sets are kept, so the whole 800 MB file costs very little memory.
    """
    found = set()
    found_elements = set()
    overlap = 2 * MAXLEN
    with open(path, "rb") as fh:
        prev = b""
        while True:
            buf = fh.read(CHUNK)
            if not buf:
                break
            data = prev + buf
            # Names sit inside longer runs of name-ish bytes, because the
            # neighbouring records' length and type bytes are themselves often
            # printable -- a name is as likely to be in the middle of a run as
            # at either end.  So walk every byte of every run as a candidate
            # length prefix and accept the name it claims when the arithmetic
            # works out.  (Testing only run suffixes was tried first and lost
            # about a third of the names: `selection_inanimate_backdrop` and
            # dozens of plates went missing because the next record happened to
            # begin with a printable byte.)
            for m in RUN.finditer(data):
                run = m.group(0)
                start, end = m.start(), m.end()
                for j in range(max(start - 1, 0), end - 6):
                    n = data[j]
                    if n < 6 or n > MAXLEN or j + 1 + n > end:
                        continue
                    text = data[j + 1:j + 1 + n].decode("ascii")
                    if FAMILY.search(text):
                        found.add(text)
                    if text in elements:
                        found_elements.add(text)
            prev = data[-overlap:]

    # A length byte can match by coincidence one character short of a real
    # name, which is how `player_vitals_backdrop_KharumUbna` turned up next to
    # the real `..._KharumUbnar`.  Drop any name that is another name with
    # exactly one character removed from the end.  Real siblings differ by
    # more than one character (`_mp`, `_vert`, `_32`), so nothing real is lost.
    found = {t for t in found if not any(o[:-1] == t for o in found)}
    return found, found_elements


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dat", help="path to client_general.dat")
    args = ap.parse_args()

    dat = find_dat(args.dat)
    if not dat or not os.path.isfile(dat):
        sys.stderr.write("client_general.dat not found; pass --dat PATH\n")
        return 1

    elements = dictionary_element_ids()
    ids, live_elements = scan(dat, elements)
    if len(ids) < 200 or len(live_elements) < 500:
        sys.stderr.write("only %d asset / %d element names recovered from %s -- "
                         "that is too few, the format has probably changed. "
                         "Not overwriting.\n" % (len(ids), len(live_elements), dat))
        return 1

    for name, values in (("live_asset_ids.txt", ids),
                         ("live_element_ids.txt", live_elements)):
        out = os.path.join(HERE, "reference", name)
        with open(out, "w") as fh:
            for i in sorted(values, key=str.lower):
                fh.write(i + "\n")
        print("  reference/%-22s %d names" % (name, len(values)))
    print("  from %s, against %d dictionary element IDs"
          % (os.path.basename(dat), len(elements)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
