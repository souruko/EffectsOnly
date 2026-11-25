#!/usr/bin/env python3
"""Validate the EffectsOnly skin before the client ever sees it.

The client reports nothing useful.  A malformed file vanishes from the in-game
dropdown; a misspelled ArtAssetID is silently ignored; a missing FileName draws
an opaque checkerboard grid over the panel.  Every one of those costs a full
client restart to discover, so they are all checked here instead.

    python3 tests/validate_skin.py [skin_dir] [--probe]

`--probe` validates a diagnostic rung instead of the real skin.  A probe maps
assets to a deliberately bogus FileName to draw the client's checkerboard grid,
which is the free way to prove an ArtAssetID is live -- so the checks about
replacement files existing, matching size and being transparent are skipped for
it.  Everything about the file itself is still checked.

Exit status is 0 only if every check passes.
"""

import os
import re
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
# Deliberate artwork, not blanks: the rebuilt toolbar backing (make_toolbar.py).
# Exempt from T7/T8/T11 and checked by T15 instead.  EffectsOnly dropped the
# toolbar in 2.5.0; this stays for sibling skins that still carry it (Barefoot).
from make_toolbar import ART, ELEMENT_W, ELEMENT_H  # noqa: E402
DEFAULT_SKIN = os.path.dirname(HERE)
XSD = os.path.expanduser(
    "~/.vscode/extensions/lunarwtr.lotro-api-1.0.18/resources/xsds/lotro-skin.xsd")

# Assets that belong to these panels but are deliberately NOT blanked, each
# with the reason.  Printed in full on every run, so trimming the skin can
# never quietly hide a gap.
DEFERRED = {
    "black_translucent":
        "bar backing (VitalsBg / OpponentsVitals_BG) -- SHARED with the crafting "
        "panel and others. Blanking it would change unrelated UI. Opt-in only.",
    "black_translucent2":
        "second bar-backing variant, same sharing problem as black_translucent.",
    "PlayerVitals_Animations":
        "not an ArtAssetID -- an animated asset array. Animated assets cannot be "
        "mapped at all. No lever exists short of moving the element.",
    "OpponentVitals_Animations":
        "same: animated array, unmappable.",
    "<morale bar fill>":
        "no such asset exists. Never granted by SSG; XP bar fills exist "
        "(xpbar_blue_fill), there is no vitals equivalent.",
    "<power bar fill>":
        "no such asset exists, same reason.",
    "<all text>":
        "names, level digits and the morale/power numbers are glyphs, not "
        "textures. Mapping cannot reach them.",
    "<both portraits>":
        "a live render of the character or target head, not a skin asset.",
}

# Prefixes that must NEVER appear: blanking these would strip party, pet,
# target-of-target or over-the-head frames, which are out of scope.
FORBIDDEN = [
    ("mini", "fellowship / party frames"),
    ("pet_vitals", "pet frame"),
    ("target_vitals", "target-of-target frame"),
    ("floaty", "over-the-head bars"),
    ("black_translucent", "shared with the crafting panel -- see DEFERRED"),
]


class Checks:
    def __init__(self):
        self.failed = 0
        self.ran = 0

    def ok(self, tid, name, detail=""):
        self.ran += 1
        print("  %-5s PASS  %s%s" % (tid, name, ("  -- " + detail) if detail else ""))

    def fail(self, tid, name, detail):
        self.ran += 1
        self.failed += 1
        print("  %-5s FAIL  %s\n            %s" % (tid, name, detail))

    def skip(self, tid, name, why):
        print("  %-5s SKIP  %s  -- %s" % (tid, name, why))


def read_tga_header(path):
    """Return (width, height, bpp, descriptor) from an uncompressed TGA."""
    with open(path, "rb") as fh:
        head = fh.read(18)
    if len(head) < 18:
        raise ValueError("truncated TGA header")
    fields = struct.unpack("<BBBHHBHHHHBB", head)
    return fields[8], fields[9], fields[10], fields[11]


def tga_all_transparent(path):
    """True if every pixel's alpha byte is zero."""
    w, h, bpp, _desc = read_tga_header(path)
    if bpp != 32:
        return False, "%d bpp, not 32 -- no alpha channel" % bpp
    with open(path, "rb") as fh:
        fh.seek(18)
        data = fh.read()
    expected = w * h * 4
    if len(data) < expected:
        return False, "pixel data short: %d bytes, expected %d" % (len(data), expected)
    opaque = sum(1 for i in range(3, expected, 4) if data[i] != 0)
    if opaque:
        return False, "%d of %d pixels are not fully transparent" % (opaque, w * h)
    return True, ""


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


T4_NAME = "every <PanelFile> element path resolves (live client where read_layout covers it, else U46.2)"


def load_dictionary_paths():
    """{PanelFileID: {(ancestor, ..., id), ...}} from the U46.2 dictionary.

    Paths are recorded at every depth, so a lookup also checks nesting and not
    just the name.
    """
    path = os.path.join(HERE, "reference", "SkinDictionary.txt")
    raw = open(path, encoding="utf-8", errors="replace").read()
    root = ET.fromstring("<root>" + raw + "</root>")

    def walk(elem, prefix):
        here = prefix + (elem.get("ID"),)
        yield here
        for child in elem.findall("Element"):
            for sub in walk(child, here):
                yield sub

    out = {}
    for pf in root.findall("PanelFile"):
        paths = set()
        for top in pf.findall("Element"):
            paths.update(walk(top, ()))
        out[pf.get("ID")] = paths

    # The live client beats the snapshot.  read_layout.py recovers the real
    # tree of the vitals panels from the dat; for those panels the U46.2
    # paths are WRONG (two wrapper levels were added after it), so they are
    # replaced outright rather than merged.
    live = os.path.join(HERE, "reference", "live_layout.xml")
    if os.path.exists(live):
        lroot = ET.fromstring("<root>" + open(live, encoding="utf-8").read() + "</root>")
        for pf in lroot.findall("PanelFile"):
            paths = set()
            for top in pf.findall("Element"):
                paths.update(walk(top, ()))
            out[pf.get("ID")] = paths
            LIVE_PANELS.add(pf.get("ID"))
    return out


LIVE_PANELS = set()


def element_paths(panelfile):
    """Every (ancestor, ..., id) tuple used inside a <PanelFile>."""
    def walk(elem, prefix):
        here = prefix + (elem.get("ID"),)
        yield here
        for child in elem.findall("Element"):
            for sub in walk(child, here):
                yield sub

    for top in panelfile.findall("Element"):
        for p in walk(top, ()):
            yield p


def load_pack_manifest():
    path = os.path.join(HERE, "reference", "pack_manifest.tsv")
    if not os.path.isfile(path):
        return None
    ids = set()
    with open(path) as fh:
        for line in fh:
            if line.strip():
                ids.add(line.split("\t")[0])
    return ids


def load_live_ids(name, skin):
    """Names the installed client knows -- see tests/scan_client.py.

    A skin carrying its own `tests/reference/` wins over this one's, which is
    what lets selftest.py hand the validator a doctored client scan instead of
    having to uninstall the game to prove T12 and T13 fire.
    """
    for path in (os.path.join(skin, "tests", "reference", name),
                 os.path.join(HERE, "reference", name)):
        if os.path.isfile(path):
            return {l.strip() for l in open(path) if l.strip()}
    return None


# The client scan can only see names of 6+ characters made of [A-Za-z0-9_],
# because shorter ones match noise and anything with a space is not a single
# run of name bytes.  An element ID outside that shape is unverifiable, not
# missing, so T13 has to pass it rather than accuse it.
SCANNABLE = re.compile(r"^[A-Za-z0-9_]{6,80}$")


# Which of the client's asset IDs belong to the two panels this skin owns.
# Every one of the shipped assets.tsv rows matches this, and nothing else does
# -- it is what lets T12 ask "is anything live, in scope and unblanked?".
# `_mini` is excluded here rather than in FORBIDDEN because the party frames
# share the `player_vitals_` prefix.
IN_SCOPE = re.compile(
    r"^(?:player|opponent|opponenet)_vitals(?!.*_mini)"
    r"|^swarm_vitals|^monster_vitals_lowrescover$|^level_background"
    r"|^icon_pvp_rank_\d+(?:_monsterplayer)?_32$"
    r"|^pvp_.*_opponent(?:_monsterplayer_stars)?$"
    r"|^opponent_progress_overlay_(?:left|center|right)$"
    r"|^selection_inanimate_backdrop$|^Icon_LockTarget$")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    probe = "--probe" in sys.argv[1:]
    skin = os.path.abspath(args[0] if args else DEFAULT_SKIN)
    definition = os.path.join(skin, "SkinDefinition.xml")
    c = Checks()

    print("EffectsOnly validation%s -- %s\n"
          % (" (probe rung)" if probe else "", skin))

    if not os.path.isfile(definition):
        print("  no SkinDefinition.xml at %s" % definition)
        return 1

    raw = open(definition, encoding="utf-8").read()

    # T1 -- well-formed XML at all.  A parse failure means the skin will not
    # even appear in the in-game dropdown.
    try:
        root = ET.fromstring(raw)
        c.ok("T1", "SkinDefinition.xml parses")
    except ET.ParseError as exc:
        c.fail("T1", "SkinDefinition.xml parses", str(exc))
        return 1

    # T2 -- schema validation.  Note xmllint alone is not sufficient overall:
    # PanelFileID is an xs:union with an open xs:string member, so the schema
    # accepts any string there.  It still catches structural errors.
    if os.path.isfile(XSD):
        proc = subprocess.run(["xmllint", "--noout", "--schema", XSD, definition],
                              capture_output=True, text=True)
        if proc.returncode == 0:
            c.ok("T2", "validates against lotro-skin.xsd")
        else:
            c.fail("T2", "validates against lotro-skin.xsd",
                   proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else "xmllint failed")
    else:
        c.fail("T2", "validates against lotro-skin.xsd", "xsd not found at %s" % XSD)

    # T3 -- no XML comments.  The client's parser walks child nodes and appears
    # not to be node-type aware; no known-good community skin has comments.
    if "<!--" in raw:
        c.fail("T3", "no XML comments",
               "found <!-- ; the client's parser may abort on a comment node. "
               "Put prose in README.md")
    else:
        c.ok("T3", "no XML comments")

    mappings = root.findall("Mapping")
    panelfiles = root.findall("PanelFile")

    # T4 -- every element path in a <PanelFile> must resolve in the U46.2
    # dictionary at exactly the depth it is used.
    #
    # This is the check that matters most, because the failure mode it guards
    # is silent and total: one stale element ID aborts the ENTIRE panel
    # override, reverting the whole panel to stock. Reproduced in this project
    # -- 4 elements worked, the same 4 plus 13 more reverted everything. The
    # engine carries `Failed to convert [%s] to a valid UIElementID!` and
    # `Failed to add [%s] as a panel override` and surfaces neither.
    #
    # Depth matters as much as the name: element IDs are not unique across the
    # dictionary (VitalsParent exists in both vitals panels, RageMeter in both,
    # and AvatarPanel even nests a PlayerScaledLevel inside an element of the
    # same name). The engine resolves a duplicate to the first match top-down,
    # so the containing chain is what says which one is meant.
    if not panelfiles:
        c.ok("T4", T4_NAME,
             "no panel overrides -- mappings only")
    else:
        try:
            known = load_dictionary_paths()
        except Exception as exc:
            known = None
            c.fail("T4", T4_NAME,
                   "could not read reference/SkinDictionary.txt: %s" % exc)
        if known is not None:
            bad, total = [], 0
            for pf in panelfiles:
                pid = pf.get("ID")
                if pid not in known:
                    bad.append("unknown PanelFile ID %s" % pid)
                    continue
                for path in element_paths(pf):
                    total += 1
                    if path not in known[pid]:
                        bad.append("%s > %s" % (pid, " > ".join(path)))
            if bad:
                c.fail("T4", T4_NAME,
                       "%d bad path(s) -- EACH ONE ABORTS THE WHOLE PANEL: %s"
                       % (len(bad), "; ".join(bad[:4])))
            else:
                c.ok("T4", T4_NAME,
                     "%d element(s) across %d panel(s)" % (total, len(panelfiles)))

    # T5 -- no duplicate ArtAssetID.  Schema-enforced, but catch it locally.
    ids = [m.get("ArtAssetID") for m in mappings]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        c.fail("T5", "no duplicate ArtAssetID", ", ".join(dupes))
    else:
        c.ok("T5", "no duplicate ArtAssetID", "%d unique" % len(ids))

    # T6 -- every FileName resolves.  A missing file draws an opaque
    # checkerboard grid in-game, which is worse than shipping nothing.
    missing = []
    for m in mappings:
        fn = (m.get("FileName") or "").replace("\\", "/")
        if not os.path.isfile(os.path.join(skin, fn)):
            missing.append("%s -> %s" % (m.get("ArtAssetID"), fn))
    if probe:
        c.skip("T6", "every FileName resolves to a real file",
               "a probe maps to a bogus file on purpose (%d of %d)"
               % (len(missing), len(mappings)))
    elif missing:
        c.fail("T6", "every FileName resolves to a real file",
               "%d missing (checkerboard grid in-game): %s"
               % (len(missing), ", ".join(missing[:5])))
    else:
        c.ok("T6", "every FileName resolves to a real file")

    asset_rows = load_assets()
    assets = {a: (w, h) for a, _s, _p, w, h, _src in asset_rows}
    inferred = {a for a, _s, _p, _w, _h, src in asset_rows if src != "measured"}

    # T7 -- every blank matches its asset's native size.  Oversizing is the one
    # thing reported to misbehave.
    wrong = []
    for m in mappings:
        aid = m.get("ArtAssetID")
        fn = (m.get("FileName") or "").replace("\\", "/")
        path = os.path.join(skin, fn)
        if aid in ART or aid not in assets or not os.path.isfile(path):
            continue
        want_w, want_h = assets[aid]
        try:
            got_w, got_h, _bpp, _d = read_tga_header(path)
        except ValueError as exc:
            wrong.append("%s: %s" % (aid, exc))
            continue
        if (got_w, got_h) != (want_w, want_h):
            wrong.append("%s: blank is %dx%d, asset is %dx%d"
                         % (aid, got_w, got_h, want_w, want_h))
    if probe:
        c.skip("T7", "every blank matches its asset's native size",
               "no replacement files in a probe")
    elif wrong:
        c.fail("T7", "every blank matches its asset's native size",
               "%d wrong: %s" % (len(wrong), "; ".join(wrong[:4])))
    else:
        # An inferred size is not a measured one.  The stock TGA for an asset
        # added after the skinning pack was published is not on disk here, so
        # its size comes from its family (every vitals plate is 273x124) rather
        # than from a header.  Said out loud, never silently.
        c.ok("T7", "every blank matches its asset's native size",
             "%d of %d sizes inferred from family, not measured"
             % (len(inferred), len(assets)) if inferred else "")

    # T8 -- every replacement is fully transparent.  This enforces the scope
    # decision: nothing opaque, ever.  An opaque texture would occlude what is
    # drawn behind it, which is a different skin.
    opaque = []
    for fn in sorted({(m.get("FileName") or "").replace("\\", "/") for m in mappings
                      if m.get("ArtAssetID") not in ART}):
        path = os.path.join(skin, fn)
        if not os.path.isfile(path):
            continue
        clear, why = tga_all_transparent(path)
        if not clear:
            opaque.append("%s: %s" % (fn, why))
    if probe:
        c.skip("T8", "every replacement is fully transparent",
               "a probe wants the client's opaque checkerboard")
    elif opaque:
        c.fail("T8", "every replacement is fully transparent", "; ".join(opaque))
    else:
        c.ok("T8", "every replacement is fully transparent")

    # T9 -- every ArtAssetID is known either to the U46.2 pack manifest or to
    # the installed client.  A typo here is silently ignored by the client, so
    # it would look like "the skin does nothing" with no way to tell which
    # entry was at fault.
    #
    # Both sources are needed.  The pack is a snapshot and the client has moved
    # on past it; the client scan is exact but not exhaustive (it recovers
    # around 90% of the names the pack lists, so a name it misses must not be
    # read as proof the asset is gone).  An ID in either one is real.
    pack = load_pack_manifest()
    live = load_live_ids("live_asset_ids.txt", skin)
    if pack is None:
        c.fail("T9", "every ArtAssetID is known", "pack_manifest.tsv missing")
    else:
        vocabulary = pack | (live or set())
        unknown = [i for i in ids if i not in vocabulary]
        if unknown:
            c.fail("T9", "every ArtAssetID is known",
                   "%d in neither the U46.2 manifest nor the live client: %s"
                   % (len(unknown), ", ".join(unknown[:6])))
        else:
            c.ok("T9", "every ArtAssetID is known",
                 "%d from U46.2 + %d live" % (len(pack), len(live or ())))

    # T10 -- nothing out of scope crept in.  Blanking a party, pet,
    # target-of-target or over-the-head asset is collateral damage.
    bad = []
    for i in ids:
        for frag, what in FORBIDDEN:
            if frag.lower() in i.lower():
                bad.append("%s (%s)" % (i, what))
    if bad:
        c.fail("T10", "no out-of-scope asset blanked",
               "%d: %s" % (len(bad), ", ".join(bad[:6])))
    else:
        c.ok("T10", "no out-of-scope asset blanked")

    # T11 -- SkinDefinition.xml is generated; it must not have drifted from
    # what build_skin.py produces from assets.tsv.
    expected_ids = sorted(assets, key=str.lower)
    ids = [i for i in ids if i not in ART]
    if probe:
        c.skip("T11", "SkinDefinition.xml matches assets.tsv",
               "a probe names a deliberate subset (%d of %d)"
               % (len(ids), len(expected_ids)))
    elif ids != expected_ids:
        only_file = [i for i in ids if i not in assets]
        only_tsv = [i for i in expected_ids if i not in set(ids)]
        c.fail("T11", "SkinDefinition.xml matches assets.tsv",
               "in XML only: %s | in TSV only: %s"
               % (only_file[:4] or "-", only_tsv[:4] or "-"))
    else:
        c.ok("T11", "SkinDefinition.xml matches assets.tsv")

    # T12 -- nothing the live client knows is left unblanked.  This is the
    # check the skin shipped without, and it cost a round of "the plate is
    # still there" with no way to tell why: the skin was built from the U46.2
    # manifest, the client had moved on to U50, and the four frame families
    # added in between (U47 rivals, U48 feasts, U49 frozen, U50 neighbors) were
    # simply not in it.  An uncovered cosmetic frame looks identical to a
    # broken skin.
    #
    # Only additions are reported.  The scan is exact but incomplete, so an ID
    # the client scan missed must never be taken as a reason to delete a row.
    if probe:
        c.skip("T12", "every live in-scope asset is blanked",
               "a probe names a deliberate subset")
    elif live is None:
        c.skip("T12", "every live in-scope asset is blanked",
               "reference/live_asset_ids.txt missing -- run tests/scan_client.py")
    else:
        uncovered = sorted(i for i in live if IN_SCOPE.match(i) and i not in set(ids))
        in_scope = sum(1 for i in live if IN_SCOPE.match(i))
        if uncovered:
            c.fail("T12", "every live in-scope asset is blanked",
                   "%d live and unblanked -- each one still draws its frame: %s"
                   % (len(uncovered), ", ".join(uncovered[:6])))
        else:
            c.ok("T12", "every live in-scope asset is blanked",
                 "%d in-scope IDs in the installed client" % in_scope)

    # T13 -- every element named in a <PanelFile> still exists in the installed
    # client.  T4 asks the same question of the U46.2 dictionary, which is a
    # snapshot; this one asks the client in front of us.  It is the check that
    # guards the worst failure mode in this whole system -- one stale element
    # ID aborts the entire panel override, silently, reverting the panel to
    # stock with nothing reported.
    #
    # Treat anything tied to a removed game feature as a prime suspect:
    # PlayerVoiceChat, PlayerSendingData and PlayerVoiceChatSquelched are still
    # in the dictionary although in-game voice chat is long gone.
    live_elements = load_live_ids("live_element_ids.txt", skin)
    named = sorted({eid for pf in panelfiles for path in element_paths(pf)
                    for eid in [path[-1]]})
    if not panelfiles:
        c.ok("T13", "every named element exists in the installed client",
             "no panel overrides")
    elif live_elements is None:
        c.skip("T13", "every named element exists in the installed client",
               "reference/live_element_ids.txt missing -- run tests/scan_client.py")
    else:
        checkable = [e for e in named if SCANNABLE.match(e)]
        gone = [e for e in checkable if e not in live_elements]
        if gone:
            c.fail("T13", "every named element exists in the installed client",
                   "%d gone -- EACH ONE ABORTS THE WHOLE PANEL: %s"
                   % (len(gone), ", ".join(gone)))
        else:
            c.ok("T13", "every named element exists in the installed client",
                 "%d checked, %d unverifiable by shape"
                 % (len(checkable), len(named) - len(checkable)))

    # T14 -- every element named in a <PanelFile> carries X, Y, Width and
    # Height.  "Name the ancestor, leave it untouched" is false: the client
    # builds an element named without geometry at size zero.  Its children
    # still draw, but the mouse cannot reach them and anything laid out
    # against the parent's size collapses -- 2.0.0 broke both effect trays
    # this way (debuffs under buffs, no tooltips) until the next restart.
    # Confirmed in-game 2026-11-24.  Restate the stock values from
    # reference/live_layout.xml instead.
    bare = []
    for pf in panelfiles:
        for el in pf.iter("Element"):
            if any(el.get(k) is None for k in ("X", "Y", "Width", "Height")):
                bare.append("%s:%s" % (pf.get("ID").replace("ID_UISkin_", ""), el.get("ID")))
    if bare:
        c.fail("T14", "every named element restates X/Y/Width/Height",
               "%d without -- built at size 0, breaks mouse + layout of everything inside: %s"
               % (len(bare), ", ".join(bare[:5])))
    else:
        c.ok("T14", "every named element restates X/Y/Width/Height",
             "no panel overrides" if not panelfiles else "")

    # T15 -- the rebuilt toolbar art.  The client does not stretch a mapped
    # texture, so each one must exist, be 32-bit, and be exactly the size of
    # the ToolbarFieldMain override that draws it -- otherwise the strip, the
    # lifted bar frame and the buttons drift apart.
    art_maps = {m.get("ArtAssetID"): (m.get("FileName") or "").replace("\\", "/")
                for m in mappings if m.get("ArtAssetID") in ART}
    fm = [e for pf in panelfiles for e in pf.iter("Element") if e.get("ID") == "ToolbarFieldMain"]
    bad = []
    if art_maps:
        if len(fm) != 1:
            bad.append("expected one ToolbarFieldMain override, found %d" % len(fm))
        else:
            want = (int(fm[0].get("Width")), int(fm[0].get("Height")))
            if want != (ELEMENT_W, ELEMENT_H):
                bad.append("ToolbarFieldMain is %dx%d, make_toolbar says %dx%d"
                           % (want + (ELEMENT_W, ELEMENT_H)))
            for aid, fn in sorted(art_maps.items()):
                path = os.path.join(skin, fn)
                if not os.path.isfile(path):
                    bad.append("%s: %s missing" % (aid, fn))
                    continue
                w, h, bpp, _d = read_tga_header(path)
                if (w, h) != want or bpp != 32:
                    bad.append("%s: %s is %dx%d/%dbpp, element is %dx%d" % ((aid, fn, w, h, bpp) + want))
    if not art_maps:
        c.ok("T15", "rebuilt toolbar art matches its element", "no toolbar art in this skin")
    elif bad:
        c.fail("T15", "rebuilt toolbar art matches its element", "; ".join(bad))
    else:
        c.ok("T15", "rebuilt toolbar art matches its element",
             "%d texture(s), %dx%d" % (len(art_maps), ELEMENT_W, ELEMENT_H))

    print("\n  DEFERRED -- in these panels, deliberately not blanked:")
    for aid, why in sorted(DEFERRED.items()):
        print("    %-28s %s" % (aid, why))

    print("\n  %d checks, %d failed" % (c.ran, c.failed))
    return 1 if c.failed else 0


if __name__ == "__main__":
    sys.exit(main())
