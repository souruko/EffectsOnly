#!/usr/bin/env python3
"""Recover the LIVE UI element tree of the vitals panels from the client.

Why this exists
---------------
A skin's <PanelFile> must spell out the element tree *exactly* as the client
has it.  The engine walks the override against its own layout
(UIUserSkin::ParseNodeIntoSkinOverride); one element that does not match makes
it drop the whole panel override ("Failed to add [%s] as a panel override") and
it reports nothing.

Every skin in this project was written against the U46.2 SkinDictionary, and
the client has since moved on.  Read straight out of the dat, the vitals panels
now nest through wrappers the dictionary has never heard of:

    AvatarPanel > VitalsParent > ViewportParent > PlayerPortrait
                               > PanelParent    > PlayerName, VitalsField, ...
    OpponentPanel > VitalsParentOpponent > OpponentDisplayParent
                  > OpponentViewportParent > OpponentPortrait
                  > OpponentPanelParent    > Opponent_SelectionField, OpponentEffectDisplay, ...

That is why `AvatarPanel > VitalsParent` worked (depth 1 never changed) and
everything deeper -- and the entire target panel -- silently did nothing.

What it reads (read-only; nothing is ever written to the game files)
--------------------------------------------------------------------
* client_local_English.dat -- a Turbine "BT" archive.  Superblock at 0x140
  (block size 0x144, root directory 0x160).  Each directory node: 8-byte
  header, 62 x (size, offset) sub-directory pointers, a file count, then that
  many 32-byte entries (flags, id, offset, size, timestamp, version,
  block size, unused).  File bodies are stored uncompressed after an 8-byte
  header.  UI layouts are the 0x22xxxxxx files; the gameplay HUD is 0x22000033.
* client_general.dat, file 0x230000D1 -- the UIElementID enum: repeated
  (uint32 id, uint8 length, ASCII name).
* Inside a layout, an element record is: id (u32), base element (u32, 0 for a
  concrete element), one flag byte, then X, Y, Width, Height (i32), and the
  bytes `01 00` four bytes after Height.  Records are serialised parent-first
  and the byte immediately before the next record is the previous record's
  child count -- enough to rebuild the tree exactly.  The parse is checked:
  each panel must consume a whole number of records and end on the next
  top-level panel.

    python3 tests/read_layout.py [--dir GAME_DIR]

Writes reference/live_layout.xml in SkinDictionary shape.  validate_skin.py
(T4) prefers it over the U46.2 dictionary for the panels it covers.  Re-run it
after every game update.
"""

import argparse
import mmap
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "reference", "live_layout.xml")

GAME_DIRS = [
    "~/Games/lotro/drive_c/Program Files (x86)/StandingStoneGames/"
    "The Lord of the Rings Online",
    "~/.local/share/Steam/steamapps/common/Lord of the Rings Online",
]

ENUM_UIELEMENTID = 0x230000D1
HUD_LAYOUT = 0x22000033
PANELS = [("ID_UISkin_AvatarPanel", "AvatarPanel"),
          ("ID_UISkin_OpponentPanel", "OpponentPanel"),
          ("ID_UISkin_Toolbar", "ToolbarField"),
          ("ID_UISkin_Toolbar_Quickslot_Extended_Scaler", "Toolbar_Quickslot_Extended_Scaler")]


class Dat:
    def __init__(self, path):
        self.f = open(path, "rb")
        self.m = mmap.mmap(self.f.fileno(), 0, access=mmap.ACCESS_READ)
        if struct.unpack_from("<I", self.m, 0x140)[0] != 0x5442:
            raise ValueError("%s: not a BT archive" % path)
        self.root = struct.unpack_from("<I", self.m, 0x160)[0]

    def find(self, file_id):
        """Walk the directory tree for one file id (iterative, cycle-safe)."""
        stack, seen = [self.root], set()
        while stack:
            off = stack.pop()
            if off in seen:
                continue
            seen.add(off)
            count = struct.unpack_from("<I", self.m, off + 504)[0]
            if count > 61:
                continue
            for i in range(count):
                e = struct.unpack_from("<8I", self.m, off + 508 + 32 * i)
                if e[1] == file_id:
                    start = e[2] + 8
                    return bytes(self.m[start:start + e[3]])
            # B-tree: a node with N entries has N+1 live children; slots past
            # that hold stale pointers.  A leaf (N == 0) has none that matter.
            for i in range(count + 1 if count else 0):
                size, sub = struct.unpack_from("<II", self.m, off + 8 + 8 * i)
                if sub and sub + 2464 <= len(self.m):
                    stack.append(sub)
        raise KeyError("file 0x%08X not found" % file_id)


def element_names(table):
    names = {}
    for mo in re.finditer(rb"[A-Za-z0-9_]{2,}", table):
        # The length byte is itself printable whenever the name is 48-57,
        # 65-90, 95 or 97-122 characters long ('A' = 65), and then the run of
        # name characters starts one byte early.  Try the first few starts;
        # the id's top byte 0x10 is what confirms one.
        for s in range(mo.start(), min(mo.start() + 3, mo.end())):
            if s < 5:
                continue
            length = table[s - 1]
            if 2 <= length <= mo.end() - s:
                v = struct.unpack_from("<I", table, s - 5)[0]
                if v >> 24 == 0x10:
                    names[v] = table[s:s + length].decode()
                    break
    return names


def records(layout, names):
    out = []
    for p in range(5, len(layout) - 31):
        v = struct.unpack_from("<I", layout, p)[0]
        if v not in names or struct.unpack_from("<I", layout, p + 4)[0] != 0:
            continue
        if layout[p + 29:p + 31] != b"\x01\x00":
            continue
        x, y, w, h = struct.unpack_from("<iiii", layout, p + 9)
        # all-zero geometry is data that happens to look like a record (image
        # lists inside LevelMeterFill name Ring2Slot, Auction_* ...); taking
        # them as elements derails the child counts of the toolbar
        if x == y == w == h == 0:
            continue
        if -4000 < x < 4000 and -4000 < y < 4000 and 0 <= w < 5000 and 0 <= h < 5000:
            out.append({"id": names[v], "x": x, "y": y, "w": w, "h": h,
                        "n_prev": layout[p - 1]})
    return out


def build(recs, start):
    pos = start

    def node():
        nonlocal pos
        rec = dict(recs[pos])
        pos += 1
        n = recs[pos]["n_prev"] if pos < len(recs) else 0
        rec["children"] = []
        for _ in range(n):
            if pos >= len(recs):
                raise ValueError("ran out of records under %s" % rec["id"])
            rec["children"].append(node())
        return rec

    tree = node()
    return tree, pos


def to_xml(node, depth):
    pad = "\t" * depth
    head = '%s<Element ID="%s" X="%d" Y="%d" Width="%d" Height="%d">' % (
        pad, node["id"], node["x"], node["y"], node["w"], node["h"])
    if not node["children"]:
        return head + " </Element>"
    body = "\n".join(to_xml(c, depth + 1) for c in node["children"])
    return "%s\n%s\n%s</Element>" % (head, body, pad)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir")
    args = ap.parse_args()
    dirs = [args.dir] if args.dir else GAME_DIRS
    game = next((os.path.expanduser(d) for d in dirs
                 if os.path.exists(os.path.join(os.path.expanduser(d),
                                                "client_local_English.dat"))), None)
    if not game:
        sys.exit("game install not found; pass --dir")

    names = element_names(Dat(os.path.join(game, "client_general.dat")).find(ENUM_UIELEMENTID))
    layout = Dat(os.path.join(game, "client_local_English.dat")).find(HUD_LAYOUT)
    recs = records(layout, names)
    roots = {r["id"] for r in recs}

    blocks = []
    for panel_id, root in PANELS:
        if root not in roots:
            sys.exit("%s not found in layout 0x%08X -- format changed?" % (root, HUD_LAYOUT))
        start = next(i for i, r in enumerate(recs) if r["id"] == root)
        tree, end = build(recs, start)
        print("%-24s %3d elements  (ends before %s)"
              % (panel_id, end - start, recs[end]["id"] if end < len(recs) else "EOF"))
        blocks.append('<PanelFile ID="%s">\n%s\n</PanelFile>' % (panel_id, to_xml(tree, 1)))

    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(blocks) + "\n")
    print("wrote", os.path.relpath(OUT, os.path.dirname(HERE)))

    # scan_client.py only looks for names the U46.2 dictionary already lists,
    # so it can never see the post-U46.2 wrappers (PanelParent, ...).  Every
    # name in these trees came out of the client's own enum, so it is live by
    # construction -- merge them in, or T13 accuses the very elements that
    # make the override work.  Run this AFTER scan_client.py.
    ids_path = os.path.join(HERE, "reference", "live_element_ids.txt")
    have = set()
    if os.path.exists(ids_path):
        have = {l.strip() for l in open(ids_path) if l.strip()}
    found = set(re.findall(r'ID="([^"]+)"', "\n".join(blocks))) - {
        p for p, _r in PANELS}
    added = sorted(found - have)
    if added:
        with open(ids_path, "w") as f:
            f.write("\n".join(sorted(have | found)) + "\n")
    print("live_element_ids.txt: +%d (%s)" % (len(added), ", ".join(added) or "none new"))


if __name__ == "__main__":
    main()
