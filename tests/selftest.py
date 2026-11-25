#!/usr/bin/env python3
"""Prove validate_skin.py's checks actually fire.

A validator that passes on a broken skin is worse than no validator: it buys
false confidence at the price of a client restart.  So each check gets a
deliberately broken copy of the skin and must fail on it, naming the right test.

    python3 tests/selftest.py
"""

import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VALIDATE = os.path.join(HERE, "validate_skin.py")


def run_validator(skin_dir):
    proc = subprocess.run([sys.executable, VALIDATE, skin_dir],
                          capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def failing_tests(output):
    return set(re.findall(r"(T\d+)\s+FAIL", output))


def clone():
    tmp = tempfile.mkdtemp(prefix="blankvitals-selftest-")
    dest = os.path.join(tmp, "EffectsOnly")
    shutil.copytree(ROOT, dest, ignore=shutil.ignore_patterns(".git"))
    return tmp, dest


def edit_definition(skin, fn):
    path = os.path.join(skin, "SkinDefinition.xml")
    raw = open(path, encoding="utf-8").read()
    open(path, "w", encoding="utf-8").write(fn(raw))


# -- the injected faults -------------------------------------------------------

def fault_comment(skin):
    edit_definition(skin, lambda r: r.replace(
        "<opt>", "<opt>\n\t<!-- the client's parser may abort on this -->", 1))


def inject_panelfile(skin, panel_id, inner):
    """Replace (or add) the skin's <PanelFile> for `panel_id`.

    Replace, not append: the schema rejects two <PanelFile> blocks carrying the
    same ID, and the shipped skin now overrides both vitals panels.  Appending
    a second one would fail T2 before the fault under test ever got looked at,
    which is how the positive control broke the first time this was tried.
    """
    pattern = re.compile(
        r'\t<PanelFile ID="%s">.*?\t</PanelFile>\n' % re.escape(panel_id), re.S)
    edit_definition(skin, lambda r: pattern.sub("", r).replace(
        "</opt>",
        '\t<PanelFile ID="%s">\n%s\n\t</PanelFile>\n</opt>' % (panel_id, inner), 1))


# The live client nests everything on the player plate under PanelParent
# (see read_layout.py).  The old fixture -- AvatarPanel > VitalsParent >
# PlayerName, straight from U46.2 -- was itself a path the client rejects.
GOOD_INNER = (
    '\t\t<Element ID="AvatarPanel" X="2" Y="2" Width="280" Height="300">\n'
    '\t\t\t<Element ID="VitalsParent" X="0" Y="20" Width="300" Height="300">\n'
    '\t\t\t\t<Element ID="PanelParent" X="0" Y="0" Width="300" Height="300">\n'
    '\t\t\t\t\t<Element ID="%s" X="87" Y="14" Width="191" Height="36"></Element>\n'
    '\t\t\t\t</Element>\n'
    '\t\t\t</Element>\n'
    '\t\t</Element>'
)


def fault_bad_element_id(skin):
    # A single stale element ID silently aborts the WHOLE panel override.
    inject_panelfile(skin, "ID_UISkin_AvatarPanel", GOOD_INNER % "PlayerNmae")


def fault_broken_chain(skin):
    # Right ID, wrong depth: PlayerName hoisted out of VitalsParent. The name
    # does exist in this panel, so only a depth-aware check catches it.
    inject_panelfile(skin, "ID_UISkin_AvatarPanel",
                     '\t\t<Element ID="AvatarPanel">\n'
                     '\t\t\t<Element ID="PlayerName" X="87" Y="14" Width="191" Height="36">'
                     '</Element>\n'
                     '\t\t</Element>')


def fault_unknown_panel(skin):
    inject_panelfile(skin, "ID_UISkin_AvatarPanelX", GOOD_INNER % "PlayerName")


def fault_valid_panelfile_passes(skin):
    """Not a fault: a correct override must NOT be rejected."""
    inject_panelfile(skin, "ID_UISkin_AvatarPanel", GOOD_INNER % "PlayerName")


def fault_duplicate(skin):
    path = os.path.join(skin, "SkinDefinition.xml")
    raw = open(path, encoding="utf-8").read()
    first = re.search(r"\t<Mapping [^\n]*\n", raw).group(0)
    open(path, "w", encoding="utf-8").write(raw.replace(first, first + first, 1))


def fault_missing_file(skin):
    os.remove(os.path.join(skin, "blank_273x124.tga"))


def fault_wrong_size(skin):
    # rewrite one blank at the wrong dimensions
    path = os.path.join(skin, "blank_62x31.tga")
    header = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, 10, 10, 32, 0x08)
    with open(path, "wb") as fh:
        fh.write(header)
        fh.write(bytes(4) * 100)


def fault_opaque(skin):
    path = os.path.join(skin, "blank_32x32.tga")
    header = struct.pack("<BBBHHBHHHHBB", 0, 0, 2, 0, 0, 0, 0, 0, 32, 32, 32, 0x08)
    with open(path, "wb") as fh:
        fh.write(header)
        fh.write(bytes((255, 0, 255, 255)) * 32 * 32)


def fault_bad_asset_id(skin):
    edit_definition(skin, lambda r: r.replace(
        'ArtAssetID="player_vitals_backdrop"',
        'ArtAssetID="player_vitals_backdropp"', 1))


def fault_out_of_scope(skin):
    edit_definition(skin, lambda r: r.replace(
        "</opt>",
        '\t<Mapping ArtAssetID="player_vitals_backdrop_mini" '
        'FileName="blank_273x124.tga"></Mapping>\n</opt>', 1))


def fault_dropped_mapping(skin):
    edit_definition(skin, lambda r: re.sub(
        r'\t<Mapping ArtAssetID="swarm_vitals_scion"[^\n]*\n', "", r, count=1))


def fault_live_asset_unblanked(skin):
    # The real-world shape of this: a game update ships a new cosmetic frame
    # and the skin, built from a frozen manifest, never hears about it. The
    # uncovered plate then draws, and looks exactly like a broken skin. Dropping
    # one of the assets only the live client knows about reproduces it.
    #
    # T11 fires too, and must: both checks read the shipped assets.tsv, so any
    # dropped mapping also drifts from it. T12 is the one that would still speak
    # up if the TSV itself were the thing left behind.
    edit_definition(skin, lambda r: re.sub(
        r'\t<Mapping ArtAssetID="opponent_vitals_backdrop_U49_frozen_FP"[^\n]*\n',
        "", r, count=1))


def fault_u46_path(skin):
    # The exact mistake every override in this project made before 2026-11-24:
    # a path that is valid in the U46.2 dictionary but skips the PanelParent
    # wrapper the live client added since.  The client drops the whole panel.
    inject_panelfile(skin, "ID_UISkin_AvatarPanel",
                     '\t\t<Element ID="AvatarPanel">\n'
                     '\t\t\t<Element ID="VitalsParent">\n'
                     '\t\t\t\t<Element ID="PlayerName" X="87" Y="14" Width="191" Height="36"></Element>\n'
                     '\t\t\t</Element>\n'
                     '\t\t</Element>')


def fault_bare_ancestor(skin):
    # 2.0.0's mistake: a wrapper named without geometry.  Valid path, valid
    # IDs -- but the client builds it at size zero and the effect tray inside
    # loses its mouse and its row layout.
    inject_panelfile(skin, "ID_UISkin_AvatarPanel",
                     '\t\t<Element ID="AvatarPanel" X="2" Y="2" Width="280" Height="300">\n'
                     '\t\t\t<Element ID="VitalsParent">\n'
                     '\t\t\t\t<Element ID="PanelParent" X="0" Y="0" Width="300" Height="300">\n'
                     '\t\t\t\t\t<Element ID="PlayerName" X="87" Y="3" Width="1" Height="1"></Element>\n'
                     '\t\t\t\t</Element>\n'
                     '\t\t\t</Element>\n'
                     '\t\t</Element>')


def fault_dead_element(skin):
    # A game update retires an element the skin names. T4 cannot see it -- the
    # dictionary is a snapshot and still lists it -- so only T13, which asks
    # the installed client, has a chance. Simulated by taking the element back
    # out of the clone's copy of the client scan, since every element the skin
    # really names is still live.
    inject_panelfile(skin, "ID_UISkin_AvatarPanel", GOOD_INNER % "PlayerName")
    path = os.path.join(skin, "tests", "reference", "live_element_ids.txt")
    kept = [l for l in open(path) if l.strip() != "PlayerName"]
    open(path, "w").writelines(kept)


CASES = [
    ("XML comment present",            fault_comment,       "T3"),
    ("stale element ID in override",   fault_bad_element_id, "T4"),
    ("broken containing chain",        fault_broken_chain,  "T4"),
    ("unknown PanelFile ID",           fault_unknown_panel, "T4"),
    ("U46.2 path, live tree differs",  fault_u46_path,      "T4"),
    ("wrapper named without geometry", fault_bare_ancestor, "T14"),
    ("duplicate ArtAssetID",           fault_duplicate,     "T5"),
    ("replacement file missing",       fault_missing_file,  "T6"),
    ("blank at the wrong size",        fault_wrong_size,    "T7"),
    ("an opaque replacement",          fault_opaque,        "T8"),
    ("misspelled ArtAssetID",          fault_bad_asset_id,  "T9"),
    ("out-of-scope asset blanked",     fault_out_of_scope,  "T10"),
    ("a mapping silently dropped",     fault_dropped_mapping, "T11"),
    ("a live asset left unblanked",    fault_live_asset_unblanked, "T12"),
    ("element gone from the client",   fault_dead_element,  "T13"),
]


def main():
    print("selftest -- each fault must be caught by the named check\n")

    code, output = run_validator(ROOT)
    if code != 0:
        print("  the unmodified skin does not validate -- fix that first\n")
        print(output)
        return 1
    print("  %-32s clean skin passes" % "baseline")

    # Positive control. A suite made only of faults can pass by rejecting
    # everything, so prove T4 still accepts a correct panel override -- the
    # check has to be able to say yes.
    tmp, skin = clone()
    try:
        fault_valid_panelfile_passes(skin)
        code, output = run_validator(skin)
        if code == 0:
            print("  %-32s a VALID override is accepted\n" % "positive control")
        else:
            print("  %-32s a valid override was REJECTED by %s\n"
                  % ("positive control", ",".join(sorted(failing_tests(output))) or "?"))
            print(output)
            return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failures = 0
    for name, inject, expect in CASES:
        tmp, skin = clone()
        try:
            inject(skin)
            code, output = run_validator(skin)
            fired = failing_tests(output)
            if code == 0:
                print("  %-32s NOT CAUGHT (validator passed)" % name)
                failures += 1
            elif expect not in fired:
                print("  %-32s caught by %s, expected %s"
                      % (name, ",".join(sorted(fired)) or "nothing", expect))
                failures += 1
            else:
                others = sorted(fired - {expect})
                extra = ("  (also %s)" % ",".join(others)) if others else ""
                print("  %-32s caught by %s%s" % (name, expect, extra))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    print("\n  %d cases, %d not caught" % (len(CASES), failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
