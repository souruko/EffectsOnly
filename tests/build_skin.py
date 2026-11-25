#!/usr/bin/env python3
"""Generate SkinDefinition.xml from reference/assets.tsv.

`assets.tsv` is the single source of truth for what this skin blanks.  It was
derived from the Unofficial Update 46.2 Skinning Pack's own
`SkinDefinitions.xml` -- the complete 4704-entry ArtAssetID manifest -- filtered
to the two vitals panels, with every native size measured from the stock TGA
headers.  Regenerating by hand is not viable at this size; edit the TSV and
re-run this.

The file is written with NO XML comments.  The client's parser walks child nodes
and its own error strings (`Error getting children nodes in UILOverride`)
suggest it is not node-type aware; no known-good community skin contains
comments, and a skin that fails to parse simply vanishes from the in-game
dropdown with no error reported.  All prose lives in README.md instead.

OVERRIDES below move every non-effect element of both vitals plates
off-screen, using the live element tree (see read_layout.py).  The mappings
stay as belt and braces: anything a move misses is still drawn transparent.

    python3 tests/build_skin.py
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SKIN_NAME = "EffectsOnly"

# The geometry overrides: (PanelFileID, path, X, Y, W, H, stock X, stock Y).
#
# Paths are the LIVE client's element tree, recovered from the dat by
# read_layout.py into reference/live_layout.xml -- NOT the U46.2 dictionary.
# Since U46.2 the client wraps both plates in two extra levels:
#
#   AvatarPanel > VitalsParent > ViewportParent (portrait) / PanelParent (the rest)
#   OpponentPanel > VitalsParentOpponent > OpponentDisplayParent
#                 > OpponentViewportParent (portrait) / OpponentPanelParent (the rest)
#
# Every override this project wrote before 2026-11-24 skipped those wrappers,
# and one unmatched element makes the engine drop the whole panel override.
# That -- not attachment positioning, not offset range, not depth -- is why
# geometry "did nothing" on children of VitalsParent and on the entire target
# panel.  T4 now resolves every path against the live tree.
#
# What moves: everything on both plates except the effect trays.  Names, bars,
# numbers, portraits, level, rank, leader/PVP icons, the animated layer (the
# rank flames / ring and eye -- unmappable, so moving is the only lever), the
# open-tapping marker, the lock-on reticle and the chest/door plate.
#
# What stays: PlayerEffectDisplay (+ its _Spacer -- never override one without
# the other) and OpponentEffectDisplay, untouched; and the two backdrop
# elements AvatarPanel_BG / OpponentPanel_BG, left in place because their
# texture is already blanked by the mappings above -- invisible, but they keep
# the frame's hit region, so the panels can still be clicked, dragged and
# right-clicked for the portrait menu.
#
# Off-screen means up AND left by 2000 from the plate: hidden unless the panel
# itself sits more than ~1700 px right *and* down.  Width/Height stay stock.
OFF = -2000
P = ("AvatarPanel", "VitalsParent")
PP = P + ("PanelParent",)
O = ("OpponentPanel", "VitalsParentOpponent")
OD = O + ("OpponentDisplayParent",)
OP = OD + ("OpponentPanelParent",)
OS = OP + ("Opponent_SelectionField",)

PLAYER_GONE = [
    (P,  "ViewportParent",            0,  0, 300, 300),
    (PP, "PlayerLevel_HWField",      32, 82,  38,  17),
    (PP, "PlayerName",               87,  3, 191,  36),
    (PP, "PlayerVitals_Animations",   2,  0, 277, 104),
    (PP, "PlayerScaledLevel_HWField", 32, 82, 38,  17),
    (PP, "AvatarPanel_COVER_LOWRES", 19, 19,  62,  62),
    (PP, "LoE_VitalsField",          64, 58, 224,  40),
    (PP, "PlayerLevel_BG",           19, 76,  65,  32),
    (PP, "PlayerLeaderIcon",         74, 68,  16,  16),
    (PP, "PlayerVoiceChatSquelched", 71, 11,  20,  20),
    (PP, "PlayerAssistantIcon",      74, 68,  16,  16),
    (PP, "PlayerVoiceChat",          71, 11,  20,  20),
    (PP, "PlayerSendingData",        71, 11,  20,  20),
    (PP, "PlayerPVP_Info",           -4, -3,  34,  98),
    (PP, "VitalsBg",                 88, 37, 175,  27),
    (PP, "VitalsField",              96, 33, 164,  42),
]
TARGET_GONE = [
    (OD, "OpponentViewportParent",            0,  0, 300, 300),
    (OS, "OpponentVitals_Animations",        28, -1, 277, 104),
    (OS, "OpponentLevel_HWField",           232, 82,  38,  17),
    (OS, "OpponentPanel_COVER_LOWRES",      221, 20,  62,  62),
    (OS, "OpponentLevel_BG",                220, 78,  65,  32),
    (OS, "OpponentsVitals_BG",               44, 37, 176,  32),
    (OS, "OpponentPVP_RankDisplay",         274, -3,  32,  32),
    (OS, "OpponentVitalsField",              44, 33, 168,  42),
    (OS, "OpponentClass",                   211, 72,  20,  20),
    (OS, "OpponentName",                      2,  3, 216,  36),
    (OS, "OpponentLevelHiddenSkull",        220, 79,  65,  32),
    (OP, "OpponentOpenTapping",              12, 37,  36,  36),
    (OP, "OpponentDisplay_BigBattlesMedalImageField", 0, 40, 32, 32),
    (O,  "InanimateObject_SelectionField",   40,  1, 228,  84),
    (("OpponentPanel",), "LockOnOverlay",   278, 33,  31,  31),
]


def gone(entries):
    return [(chain + (eid,), x + OFF, y + OFF, w, h, x, y)
            for chain, eid, x, y, w, h in entries]


# Wider effect trays were tried in 2.2.0 and DO NOT WORK: the trays still
# wrapped at 8.  Both tray records in the client layout carry a fixed property
# 0x10002B4C = 8 (bytes `4c 2b 00 10 4c 2b 00 10 08 00 00 00`), almost
# certainly the icons-per-row count, and a skin can set only X / Y / Width /
# Height / Detach.  Widening the tray (and its wrappers, for the mouse) changed
# nothing visible, so it was taken back out.  Confirmed in-game 2026-11-24.
# More per row would need a plugin-drawn tray (Turbine.UI.Lotro.EffectDisplay).

# 2.5.0: the toolbar override (2.3.0-2.4.2) was taken out; this skin is the
# two vitals plates only.  The last toolbar build is kept in
# ~/lotro/skinBackups/EffectsOnly_v2_4_2, and the Barefoot skin ships it.


def overrides():
    return [
        ("ID_UISkin_AvatarPanel", gone(PLAYER_GONE)),
        ("ID_UISkin_OpponentPanel", gone(TARGET_GONE)),
    ]


def live_geometry():
    """{path tuple: (X, Y, W, H)} for every element in reference/live_layout.xml."""
    import xml.etree.ElementTree as ET
    raw = open(os.path.join(HERE, "reference", "live_layout.xml"), encoding="utf-8").read()
    geo = {}

    def walk(e, pre):
        p = pre + (e.get("ID"),)
        geo[p] = tuple(int(e.get(k)) for k in ("X", "Y", "Width", "Height"))
        for c in e.findall("Element"):
            walk(c, p)

    for pf in ET.fromstring("<r>" + raw + "</r>").findall("PanelFile"):
        for top in pf.findall("Element"):
            walk(top, ())
    return geo


def all_geo(kids):
    return all(n["_geo"] and all_geo(n["_kids"]) for n in kids.values())


def emit_panel(panel, entries, out):
    """Merge the paths into one tree.

    Every ancestor is written WITH its stock geometry from live_layout.xml.
    An element named without X/Y/Width/Height is not "left untouched": the
    client builds it at size zero.  Children still draw (they are not clipped
    to the parent) but the mouse can never hit them and anything that lays
    itself out against the parent's size collapses -- which is exactly what
    2.0.0 did to both effect trays: debuffs stacked on top of the buffs and no
    tooltips, until the next client restart.  Confirmed in-game 2026-11-24
    (ZZProbeEffects rung 3).  T14 fails any named element without geometry.
    """
    geo = live_geometry()
    entries = list(entries)
    named = {e[0] for e in entries}
    for path, *_ in list(entries):
        for i in range(1, len(path)):
            anc = path[:i]
            if anc not in named:
                named.add(anc)
                entries.append((anc,) + geo[anc] + geo[anc][:2])
    tree = {}
    for path, x, y, w, h, _sx, _sy in entries:
        node = tree
        for eid in path[:-1]:
            node = node.setdefault(eid, {"_geo": None, "_kids": {}})["_kids"]
        node.setdefault(path[-1], {"_geo": None, "_kids": {}})["_geo"] = (x, y, w, h)
    assert all_geo(tree), "an element would be emitted without geometry"

    def walk(kids, depth):
        pad = "\t" * depth
        for eid, n in kids.items():
            attrs = ""
            if n["_geo"]:
                attrs = ' X="%d" Y="%d" Width="%d" Height="%d"' % n["_geo"]
            if n["_kids"]:
                out.append('%s<Element ID="%s"%s>' % (pad, eid, attrs))
                walk(n["_kids"], depth + 1)
                out.append("%s</Element>" % pad)
            else:
                out.append('%s<Element ID="%s"%s></Element>' % (pad, eid, attrs))

    out.append('\t<PanelFile ID="%s">' % panel)
    walk(tree, 2)
    out.append("\t</PanelFile>")


def blank_name(w, h):
    return "blank_%dx%d.tga" % (w, h)


def load_assets():
    path = os.path.join(HERE, "reference", "assets.tsv")
    rows = []
    with open(path) as fh:
        next(fh)
        for line in fh:
            if not line.strip():
                continue
            asset, stock, panel, w, h, size_src = line.rstrip("\n").split("\t")
            rows.append((asset, stock, panel, int(w), int(h), size_src))
    return rows


def main():
    rows = load_assets()

    seen = {}
    for asset, _stock, _panel, _w, _h, _src in rows:
        if asset in seen:
            sys.stderr.write("duplicate ArtAssetID in assets.tsv: %s\n" % asset)
            return 1
        seen[asset] = True

    # Sorted so a regenerated file diffs cleanly against the previous one.
    rows.sort(key=lambda r: r[0].lower())

    out = ['<?xml version="1.0" encoding="UTF-8"?>', "<opt>",
           '\t<SkinName Name="%s"></SkinName>' % SKIN_NAME]
    for asset, _stock, _panel, w, h, _src in rows:
        out.append('\t<Mapping ArtAssetID="%s" FileName="%s"></Mapping>'
                   % (asset, blank_name(w, h)))

    for panel, entries in overrides():
        emit_panel(panel, entries, out)

    out.append("</opt>")

    path = os.path.join(ROOT, "SkinDefinition.xml")
    with open(path, "w") as fh:
        fh.write("\n".join(out) + "\n")

    by_panel = {}
    inferred = 0
    for _a, _s, panel, _w, _h, src in rows:
        by_panel[panel] = by_panel.get(panel, 0) + 1
        inferred += src != "measured"
    print("  SkinDefinition.xml   %d mappings  (%s)  %d size inferred"
          % (len(rows), ", ".join("%s %d" % kv for kv in sorted(by_panel.items())),
             inferred))
    for panel, entries in overrides():
        print("  %s   %d element(s) overridden" % (panel, len(entries)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
