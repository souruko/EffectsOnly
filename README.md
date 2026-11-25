# EffectsOnly

*Renamed from `BlankVitals` on 2026-11-24 (2.1.0). In the history sections below, `EffectsOnly`
means this skin throughout, except where the text speaks of "the previous `EffectsOnly`" or the
occluder-based skin of 2026-11-15 — that was an earlier, different skin, now in the Trash.*

Strips the **player vitals** (`ID_UISkin_AvatarPanel`) and **target vitals**
(`ID_UISkin_OpponentPanel`) panels down to **just their buff/debuff trays**. Everything else on
both plates goes: names, bars, numbers, portraits, level, rank and leader icons, the animated layer
(the elite/nemesis rank flames, the ring and eye), the open-tapping marker, the lock-on reticle and
the chest/door plate. The morale and power bars are meant to come from a plugin (`Gristle`).

Version 2.5.0. Built 2026-11-25. The two vitals plates only, exactly as confirmed in 2.1.0; the toolbar override is gone (2.5.0).

Two mechanisms, both checked offline before the client sees them:

- **31 elements moved off-screen** by two `<PanelFile>` overrides — 16 on the player plate, 15 on
  the target — written against the **live client's element tree**, not the U46.2 dictionary.
- **326 `<Mapping>` entries** blanking every frame texture to a transparent TGA, kept as belt and
  braces: anything a move misses is still drawn invisible.

The two backdrop elements (`AvatarPanel_BG`, `OpponentPanel_BG`) are deliberately **left in place**
— their texture is already blank, so they are invisible, but they keep the frame's hit region. The
panels can still be clicked, dragged and right-clicked for the portrait menu.

## 2.5.0: toolbar removed, vitals only

The `ID_UISkin_Toolbar` override and the two `letterbox_bottom*` mappings are gone, and so are
`toolbar_bottom*.tga`. The toolbar, the main quickslot bar and the XP bar are fully stock again. The
vitals half is byte-for-byte the same as 2.4.2. `tests/build_skin.py` no longer writes the toolbar
and `run_all.sh` no longer runs `make_toolbar.py`; it would still write its art into this folder, so do
not run it. The validator keeps `make_toolbar.py`'s constants and **T15** for the **`Barefoot`**
skin, a copy of 2.4.2 made the same day that still carries the toolbar. The full 2.4.2 folder,
toolbar tooling included, is kept in `~/lotro/skinBackups/EffectsOnly_v2_4_2/`. The sections from
2.4.2 back to 2.3.0 below are history.

## 2.4.2: main bar below the left-edge bars

The free-standing bars were moved in-game to x=78, with rows at y 1052–1086 and 1090–1121. The main
bar now sits under them at screen (78, 1125), field-local (78, 185). That is the same 4 px gap as
between their rows and the same 35 px slot pitch, so all three share one grid, and the bar ends at
y=1160, just above the chat tabs. 2.4.1's toolbar shrink turned out to be the game's
`ToolbarUIScale`: a full-width field cannot be scaled past the screen. It was fixed in-game.

## 2.4.1: toolbar centred, field full width

`ToolbarField` is now the full screen width (X=0, 2560x500). The client appears to keep the toolbar
centred whatever X the skin sets, and a full-width field sits in the same place either way. The
closed-up strip is then placed so its middle is exactly the screen's middle (art x 982–1579,
centre 1280.5). `FDX` is computed from `SH_L`/`SH_R`.

This also fixes a 2.4.0 bug: the two XP-bar middle caps were not named, so they kept their stock
field-local position when the field grew and landed near (397, 1127). They now move with the strip.

## 2.4.0: main bar beside the free-standing bars, page toggle on the seam

The main quickslot bar sits at screen (3, 945), directly above the two free-standing bars at the
left edge (their tops are at y=984 on a 2560x1440 screen), left-aligned with them. Its page toggle
(`Toolbar_Quickslot_Page`, with its tutorial highlight) is centred on the seam where the two halves
of the strip meet (strip-local x=528).

The bar is a child of `ToolbarField`. Per 2.1.0, a child gets the mouse only inside its parent's
bounds, so the field grows to reach the bar: X=0, Y=9999 (clamped to the bottom), 1792x500, which
puts its top at y=940. Every other child shifts by (+768, +300) to compensate, so nothing else moves
on screen. All positions are in `tests/build_skin.py` (`QS_SCREEN`, `PAGE_STRIP`, `FIELD_*`).
`BAR_FRAME` cannot be combined with this, and the build refuses.

| What you see | Means |
| --- | --- |
| bar at the left, slots click and drag normally, toggle on the seam pages the bar | works |
| bar there but its slots do not respond | the field's X/Y are not honoured as assumed. Report it |
| world / chat / the left bars stop taking clicks inside x<1792, y>940 | the enlarged field swallows clicks. Shrink it and test whether the bar works outside its parent |

## 2.3.2: the quickslot bar without a frame

The lifted recess frame around the quickslot bar is off (`BAR_FRAME = False` in
`tests/make_toolbar.py`), by request: the bar floats bare above the strip. With the frame off,
`ToolbarFieldMain` keeps its stock place and size (1024x90 at y=110) and the rebuilt texture is
native size. The strip and the XP trough are unchanged from 2.3.1. Set `BAR_FRAME = True` and run
`tests/run_all.sh` to bring the frame back.

## 2.3.1: the toolbar keeps its backing art

2.3.0's split worked in-game, but it dropped the backing art: `ToolbarFieldMain` was collapsed to
1x1. That art is one 1024x90 texture, `letterbox_bottom` (monster play: `letterbox_bottom_mc`),
with the 12-cell recess painted into its middle. `tests/make_toolbar.py` now rebuilds it from the
stock art:

- The strip loses the recess (x 318–745, 427 px). The left part moves +210 and the right part −217,
  so the two curls that flanked the recess meet beside the auto-attack ring. The buttons move by the
  same amounts, so they stay on their sockets.
- The XP trough is rebuilt around its centre plate, which stays put because the LevelMeter mid caps
  do.
- The recess itself is lifted above the strip as the quickslot bar's frame. The left curl is the
  right one mirrored, because in the stock art the left curl is fused into the auto-attack ring.

`ToolbarFieldMain` grows upward to carry both: 1024x154 at y=46. The texture is exactly that size,
because the client does not stretch. `build_skin.py` imports every offset from `make_toolbar.py`, so
the art and the elements cannot drift apart. **T15** checks the texture against its element.
T7/T8/T11 exempt these two deliberate artwork mappings.

Source art: `tests/reference/art/letterbox_bottom*.tga`, from the **U50.2** UI skin art pack. The
lotrointerface download 1204 now serves U50.2 (dated 2026-11-21) instead of U46.2, and it also
ships a U50.2 `SkinDictionary.txt`. **This skin now ships SSG-derived artwork** (the two
`toolbar_bottom*.tga`), unlike the blanks, so keep that in mind before redistributing it.

## 2.3.0: main quickslot bar split from the toolbar

A third override, `ID_UISkin_Toolbar`, computed by `toolbar_entries()` in `tests/build_skin.py` from
the live toolbar tree. `read_layout.py` now reads the toolbar too, and that needed one fix: the name
table parser had missed every element name whose length byte is itself a printable character (e.g.
65 = `A`). That dropped one toolbar element and shifted the child counts. The vitals trees were
unaffected.

- `Toolbar_Quickslot` (420x35) is centred above the strip at (304, 45). Its page arrows
  (`Toolbar_Quickslot_Page`) keep their stock offset at its right end.
- The left block (menu, bag buttons, auto-attack eye, class pips) moves +210 and the right block
  (right buttons, store) moves -210. That closes the 420 px gap and keeps the strip centred.
- The XP bar (`LevelMeter` and its full-width children) narrows by 420 and its end caps follow. The
  centre caps stay.
- `ToolbarFieldMain`, the backing image: collapsed to 1x1 in 2.3.0, rebuilt in 2.3.1 (above).
- `ToolbarField` must be named with geometry (T14). It is restated as X=768 (centred for 2560 px)
  and Y=9999, which the client clamps to the bottom edge, per forum reports. The dictionary's 0,568
  is a 1024x768 position.
- Everything stays inside ToolbarField's 1024x200, so nothing loses the mouse.

| What you see | Means |
| --- | --- |
| bar above, strip closed up, bottom centre | works |
| toolbar not at the bottom / not centred | the field's X/Y are honoured differently. Adjust `SCREEN_W` or the Y |
| parts unmoved | the toolbar children are attachment-positioned. Try `Detach="1"` on ToolbarField |

## 2.2.0 tried wider effect trays, and 2.2.1 takes them back out

2.2.0 widened both trays to 253 and 254 px, and grew their wrappers so the mouse could reach the
new space. **They still wrapped at 8 icons** (in-game, 2026-11-24). Both tray records in the client
layout carry a fixed property `0x10002B4C = 8`, almost certainly the icons-per-row count. A skin
can set only `X`, `Y`, `Width`, `Height` and `Detach`, so the count is out of reach. 2.2.1 is 2.1.0
again. More icons per row, or debuffs in a tray of their own, would need a plugin-drawn tray built
on `Turbine.UI.Lotro.EffectDisplay`.

## 2.1.0: name an element, give it its geometry

2.0.0 hid both plates but broke both effect trays: debuffs drew underneath the buffs instead of in
their own row, and hovering an effect showed no tooltip. It happened only when the client *started*
with the skin, and stayed broken until the next restart even after switching to no skin, because
panels are built once at startup with the override applied.

**Cause: every ancestor in the override was named without X/Y/Width/Height.** The old convention
here was "ancestors are named but left untouched". That is false. The client builds an element named
without geometry at **size zero**. Its children still draw, because they are not clipped to the
parent, but the mouse can never reach them (no tooltips), and anything laid out against the parent's
size collapses (the debuff row lands on the buff row). Both trays live inside such a wrapper
(`PanelParent`, `OpponentPanelParent`).

Isolated over three probe restarts (`ZZProbeEffects`, since deleted):

1. Hiding by 1x1 collapse in place instead of moving: still broken. So the large offsets are not
   the cause. Incidentally, `Width="1" Height="1"` hides every element completely, bars and text
   included.
2. No mappings, and a single element hidden through `PanelParent`: still broken.
3. The full hiding with every ancestor restating its stock geometry: **both trays correct**.

`build_skin.py` now writes every ancestor with its stock geometry from `live_layout.xml`. **T14**
fails any named element without all four attributes, and the selftest has a matching fault.

## 2.0.0: why every geometry override failed before, and what changed

**Every `<PanelFile>` this project wrote before 2026-11-24 named a path the live client does not
have.** The engine (`UIUserSkin::ParseNodeIntoSkinOverride`) walks the override's `<Element>` tree
against its own layout and, on the first element that does not match, drops the *whole* panel
override (`Failed to add [%s] as a panel override`) without telling anyone.

The paths came from the U46.2 dictionary, and the client has since added two wrapper levels to
both plates. `tests/read_layout.py` reads the real tree straight out of the game files (read-only;
see its docstring for the format) and writes `tests/reference/live_layout.xml`:

```
AvatarPanel > VitalsParent > ViewportParent > PlayerPortrait
                           > PanelParent    > PlayerName, VitalsField, AvatarPanel_BG,
                                              PlayerEffectDisplay(_Spacer), ... (18)
OpponentPanel > VitalsParentOpponent > OpponentDisplayParent
                  > OpponentViewportParent > OpponentPortrait > Target_Image
                  > OpponentPanelParent    > Opponent_SelectionField (frame, 11 children)
                                           > OpponentOpenTapping, ..._BigBattlesMedalImageField
                                           > OpponentEffectDisplay
              > InanimateObject_SelectionField
  > LockOnOverlay
```

That one fact explains every in-game result recorded below:

| Observed | Real cause |
| --- | --- |
| `AvatarPanel > VitalsParent` moves (dt192, `ZZTestHideAll`) | depth 1 never changed — the path is still right |
| `PlayerName`, the level, every `VitalsParent` child "ignores geometry" | they now live under `PanelParent`; the path skipped it |
| the entire target panel ignores every override, at every depth | `OpponentPanelParent` / `OpponentViewportParent` skipped; dt192 also named `VitalsParent` and `HiddenDragBox_*`, which the live target panel does not have |
| `EffectsOnly` 1.2.0: flames and canary both unmoved | same — `OpponentPanelParent` missing from the chain |

So the long-standing rules "only a container can be hidden", "geometry is dead below
`VitalsParent`" and "the target frame is attachment-positioned" were all the same wrong path seen
from different angles. The portrait also moved: it is no longer inside `Opponent_SelectionField`
but in its own `*ViewportParent` sibling.

**T4 now resolves every path against `live_layout.xml`** for these two panels, and the selftest has
a fault for exactly this mistake (a U46.2-valid path that skips the wrapper). Re-run after every
game update, in this order:

```sh
python3 tests/scan_client.py     # asset + element IDs the client knows
python3 tests/read_layout.py     # the live element tree; merges the wrapper IDs into the scan
sh     tests/run_all.sh
```

Offsets: each element moves up *and* left by 2000 from its stock spot, stock Width/Height kept. It
stays hidden unless the panel itself sits more than ~1700 px right **and** down.

**Confirmed in-game 2026-11-24** — both plates gone, rank flames included, both buff trays kept. If it ever regresses after a patch, read it like this:

| What you see | Means |
| --- | --- |
| only the two buff trays (plus your mouse-over / click region where the frames were) | works |
| one whole panel back to stock (bars, name, portrait) | an element on *that* panel did not match, which voids the whole override. Re-run `read_layout.py`; check whether the game patched |
| the frame art gone but bars/name/portrait still there on one panel | that panel's override was dropped, the mappings still applied — same cause as above |

---

*Everything below records the 1.x investigation. Its conclusions about geometry are superseded by
the section above; the facts about mappings, assets and draw order still hold.*

## The ring and the eye

After version 1.1.0 was confirmed working, a glowing gold ring with an eye at the top was still
drawn around the target's portrait — the one piece of frame art that survived. Two separate causes
were found, and 1.2.0 addresses both.

### Cause 1: the reference was four updates out of date

`pack_manifest.tsv` comes from the Unofficial Update **46.2** Skinning Pack, which is still the
newest one published. **The installed client is on Update 50.** Everything SSG added in between was
invisible to this skin, and an uncovered cosmetic frame looks exactly like a broken skin.

Reading the names straight out of `client_general.dat` turned up **31 in-scope ArtAssetIDs that do
not exist in U46.2 at all**, on both panels:

| Family | |
| --- | --- |
| `U47_rivals_FP` / `_MP` | Update 47 |
| `U48_feasts_FP` / `_MP` | Update 48 |
| `U49_frozen_FP` / `_MP` | Update 49 |
| `U50_neighbors_bree` / `_lothlorien` / `_shire` / `_thorin` | Update 50 — note the target-panel twins spell it `u50`, lower case |
| `19_years` / `19_years_mp` | the 2026 anniversary frame |
| `legserv_ang_barter` / `legserv_ang_instance` / `legserv_lvl_fifteen` | newer legendary-server frames |
| `umbar_swashbucklers` | plural; U46.2 has the singular |

`tests/scan_client.py` does that extraction and **T12 now fails the build if the client knows an
in-scope asset this skin does not blank**, so a game update can never quietly reopen this hole.

The client stores these names length-prefixed — one byte holding the length, then exactly that many
ASCII bytes — so each candidate can be confirmed by arithmetic instead of guessed at. A plain
`strings` sweep is not good enough on its own: it drags in the neighbouring record's bytes, which is
how a phantom `player_vitals_backdrop_KharumUbna` appeared one character short of the real
`..._KharumUbnar`. Names also sit in the *middle* of a run of printable bytes as often as at the
end, so every byte position has to be tried; testing only the ends of runs lost about a third of
them, `selection_inanimate_backdrop` among them.

### Cause 2: the animated layer, which no mapping can reach

Measuring the screenshot against the dictionary placed the ring exactly, and ruled everything else
out. Scale is 1:1 — the bars measure 164px, which is `CurrentOpponentPowerMeter`'s stock width to
the pixel — so `Opponent_SelectionField`'s origin sits at screen (-25, 27), and from there:

| Element | Where it would be | |
| --- | --- | --- |
| the ring | x 190…257, y 35…103 | measured |
| `OpponentPortrait` / `OpponentPanel_COVER_LOWRES` | x 195…257, y 46…108 | too low by 11px, and both are blanked |
| `OpponentLevel_BG` | x 195…260, y 105…137 | far too low |
| `OpponentPanel_BG` | x 6…279, y 27…151 | contains it — but this is the plate, and the bars show no plate art at all |
| **`OpponentVitals_Animations`** | **x 3…280, y 26…130** | **contains it, and is the only thing left** |

That it is not a plate is independently visible: the ring is a ~2px hairline, while every one of
the 126 stock portrait rings is a thick ornate band — and all 126 come attached to a bar frame that
is not on screen. The level number landing within 3px of its predicted spot confirms the mapping
itself.

`OpponentVitals_Animations` draws an **animated asset array**. Animated assets cannot be mapped at
all, so moving the element is the only lever that exists. That is what the `<PanelFile>` blocks do,
applying both mechanisms at once — a modest off-screen offset *and* a collapse to 1×1. Neither
`*Vitals_Animations` element has children, so collapsing them cannot strand anything.

### The canary, and how to read the result

The 1.1.0 text move failed in a way that could not be interpreted, because every element it named
was one that failed. So this build moves **`OpponentLevel_HWField` up 30px** alongside the
experiment: same panel, same depth, same mechanism, plainly visible on every target. Its new spot
is inside the circle the ring used to draw, which is where it wants to be anyway.

| Ring | Level number | What it means |
| --- | --- | --- |
| gone | moved up | Solved. Keep the level where it is or set it back to Y=82 |
| gone | did not move | Solved by a new mapping from cause 1, not by the override. Drop the `<PanelFile>` blocks |
| **still there** | **moved up** | The override was live, so the ring is **not** `OpponentVitals_Animations`. Re-open the identification — and say what else is on screen |
| still there | did not move | Geometry does not reach this depth on the target panel either. The remaining lever is moving `Opponent_SelectionField`, which takes the bars and the name with it |

The player half (`PlayerVitals_Animations`) is a direct child of `VitalsParent`, which is the exact
depth proven dead twice over, so it is expected to fail. It costs nothing and it is the control.

Worth checking while you are there: **does the same ring appear around your own portrait?** If it
does, it is your equipped cosmetic vitals frame and not an enemy-rank decoration, and picking a
plain frame in-game removes it with no skin work at all.

## What goes, and what stays

**Gone** — every static texture these two panels draw:

| | |
| --- | --- |
| player vitals plate | all 120 variants: base, VIP, anniversary years 1–19, supporter tiers, festival, expansion, legendary-server, the U47–U50 families and monsterplay twins |
| target vitals plate | all of them, across mob rank (normal, signature, elite, elite master, swarm, scion) and the friendly-NPC `_good` set, plus the same cosmetic family |
| both portrait covers | `player_vitals_lowrescover`, `monster_vitals_lowrescover` |
| level plate | `level_background` and its `_rare` / `_red` / `_scion` / `_portrait_borders` siblings — shared between the two panels, which is fine, both are in scope |
| PVP rank insignia | `icon_pvp_rank_*_32` (15 ranks × monsterplay twins) and `pvp_*_stars_opponent*` (20) |
| open-tapping marker | `opponent_vitals_open_tapped`, `_contributing`, `_engaged` |
| target progress overlay | `opponent_progress_overlay_left` / `_center` / `_right` |
| inanimate-object plate | `selection_inanimate_backdrop` — the chest / door / crafting-station frame |
| lock-on reticle | `Icon_LockTarget` |

**Still on screen afterwards.** This is the honest list, and none of it is a bug:

| What | Why it cannot be reached |
| --- | --- |
| player and target **name**, **class**, **level digits**, morale/power **numbers** | text glyphs, not textures. A `<Mapping>` cannot touch a glyph |
| the **morale and power bar fills** | **no such asset exists.** Verified against the complete U46.2 manifest: 4704 ArtAssetIDs, no vitals bar fill among them. It was requested of SSG and never granted — XP bar fills do exist (`xpbar_blue_fill`), there is no vitals equivalent |
| both **portrait images** | a live render of the character or target head, not a skin asset |
| the **animated layer** — the ring and the eye | `PlayerVitals_Animations` / `OpponentVitals_Animations` are animated asset *arrays*, and animated assets cannot be mapped at all. 1.2.0 moves the elements instead; see *The ring and the eye* |
| the **bar backing** | `black_translucent`, deliberately left alone — see below |

So the result is **frameless vitals**: bars, numbers, names and portraits with no chrome around them.

### One thing that works the opposite way round to how it sounds

Measured in-game 2026-11-15 (recorded in the previous `EffectsOnly` skin): the player's name, bars,
portrait and rank icon are drawn **behind** `player_vitals_backdrop` and show through the transparent
windows in that texture. The backdrop is the **last** element in the player panel, so it paints over
them.

Blanking that texture therefore leaves them *more* exposed, not less. This skin does that knowingly —
hiding them would need either an **opaque** replacement (occlusion, which is what `EffectsOnly` did)
or moving `VitalsParent`, which takes the buff tray with it. Both are out of scope by design.

A consequence worth knowing: **a blanked texture leaves its hit region intact.** Both panels stay
clickable and draggable exactly where their frames used to be.

## Pulling the text in — tried on the player panel, does not work there

**Tested in-game 2026-11-17: the name and level number did not move.** That override is reverted;
`OVERRIDES` in `tests/build_skin.py` carries the attempted values as a comment. The target panel is
a different shape and is being asked the same question again in 1.2.0 — see *The canary*.

| Element | Stock | Tried | Result |
| --- | --- | --- | --- |
| `PlayerName` | 87, 3 | 87, 14 | did not move |
| `PlayerLevel_HWField` | 32, 82 | 58, 46 | did not move |
| `PlayerScaledLevel_HWField` | 32, 82 | 58, 46 | did not move |

This was a clean test: the skin was live (the blanking worked in the same screenshot), offsets were
small and in-range, `Width`/`Height` were restated at stock, only three elements were named, and
every path resolved against U46.2 at its exact depth. It independently reproduces the earlier
`ZZTestNudge` result, which had been written off as possibly confounded by a stale element ID. It
was not.

> **Geometry does not apply to children of `VitalsParent`, at any offset.** Only `VitalsParent`
> itself responds — and moving that takes the buff tray with it.

So the leftover text cannot be repositioned by a skin. The levers that remain are a plugin drawing
its own replacement text, or moving `VitalsParent` wholesale and giving up the stock buff tray.

**One variable is still untested on this panel, and the failed test could not see it.** Every
override confirmed to work on this panel is *one* wrapper deep (`AvatarPanel > VitalsParent`); the
attempt above was
two. The test also carried no canary, so "nothing moved" could not be told apart from "the override
never applied". `../ZZProbeDepth/` is the control that settles both in one restart — it moves
`VitalsParent` (known-good) and `PlayerName` (the question) together.

### What was intended, for whoever retries it

With the frame gone the remaining text is scattered across empty space — the name floating high, the
level digits orphaned in the bottom-left corner. The intent was to pull both in towards the bars:
the name down 11 so it sits on the bars rather than above them, and the level number up 36 and right
26 so it sits immediately left of the bars, vertically centred on the pair.

Coordinates are `VitalsParent`-local. For reference in the same space, the bar backing `VitalsBg` is
at X=88 Y=37 W=175 H=27 — the bar block spans x 88…263, centre x 175 y 50 — and the buff tray starts
at Y=74. `LAYOUT` in `tests/build_skin.py` takes `(ID, X, Y, W, H, stockX, stockY)` tuples and
emits the override with its containing chain; re-run `tests/run_all.sh` after editing.

Horizontal centring was deliberately left alone: `PlayerName` is 191 wide at X=87, so its centre is
already x 182 against the bar block's 175. It was never off-centre; it was just too high.

Nothing was harmed by the attempt — `<Mapping>` entries live outside `<PanelFile>`, so the blanking
was unaffected by the override being ignored.

### Deliberately not blanked

- **`black_translucent` / `black_translucent2`** — the bar backing (`VitalsBg` / `OpponentsVitals_BG`).
  This is the one asset that would de-chrome the bars themselves, but it is **shared with the
  crafting panel and others**, so blanking it changes unrelated UI. Adding the two IDs to
  `tests/reference/assets.tsv` and re-running `tests/run_all.sh` is all it takes, if that trade is
  worth it.
- **Party, pet, target-of-target and over-the-head frames.** `player_vitals_backdrop_mini` (and the
  ~100 other `*_mini_*` variants), `pet_vitals_backdrop_mini`, `target_vitals_backdrop_mini`,
  `floaty_vitals_overlay`. Each has its own ID, so those frames are untouched — and T10 fails the
  build if one ever creeps in.

`tests/validate_skin.py` carries this as a `DEFERRED` table, printed in full on every run, so
trimming the skin can never quietly hide a gap.

## How it is built

`tests/reference/assets.tsv` is the single source of truth: 326 rows of **ArtAssetID → stock file →
panel → native width × height → whether that size was measured or inferred**. 295 of them were
derived from the *Unofficial Update 46.2 Skinning Pack*'s own `SkinDefinitions.xml` — the complete
4704-entry asset manifest — filtered to these two panels, with every size measured from the stock
TGA headers. The other 31 postdate that pack and came from the client itself; their stock art is not
on disk here, so their size is **inferred** from the family (every vitals plate is 273×124) and T7
says so out loud on every run rather than letting it pass as measured.

```sh
python3 tests/scan_client.py     # re-read the installed client after a game update
python3 tests/make_blanks.py     # 13 transparent TGAs, one per distinct native size
python3 tests/build_skin.py      # SkinDefinition.xml, 326 mappings, sorted
sh     tests/run_all.sh          # regenerate + validate everything, then selftest
```

`scan_client.py` is the one that keeps this honest across game updates. It writes
`reference/live_asset_ids.txt` and `reference/live_element_ids.txt` from `client_general.dat`, and
T12 and T13 check the skin against them. It is not run by `run_all.sh`, because it depends on the
game being installed at a findable path — run it by hand after an update.

`SkinDefinition.xml` is **generated** — edit the TSV, not the XML. T11 fails if the two drift apart.

Sizes match each asset's native dimensions. A 1×1 blank is documented to work (it is the client's own
size-probing trick) but oversizing is the one thing reported to misbehave, so matching removes the
variable:

```
blank_21x24  blank_24x24  blank_30x30  blank_32x32  blank_34x78  blank_36x36  blank_47x36
blank_60x24  blank_62x31  blank_63x63  blank_229x65  blank_273x124  blank_273x125
```

### Conventions this file follows

- **No XML comments in `SkinDefinition.xml`.** The client's parser walks child nodes and its own
  error strings (`Error getting children nodes in UILOverride`) suggest it is not node-type aware; no
  known-good community skin contains comments. A skin that fails to parse simply vanishes from the
  in-game dropdown with nothing reported. All prose lives here instead.
- **The `<PanelFile>` blocks name as few elements as possible — one on the player panel, two on the
  target panel.** One stale element ID silently aborts an *entire* panel override (reproduced — 4
  elements worked, the same 4 plus 13 more reverted the whole panel to stock). The engine carries
  `Failed to convert [%s] to a valid UIElementID!` and `Failed to add [%s] as a panel override` and
  surfaces neither. A longer list is not forbidden, it is just likelier to contain a bad name. All
  nine names in this build, wrappers included, were confirmed present in the installed client (T13).
- **Two `<PanelFile>` blocks with the same ID are a schema error.** Override a panel once, listing
  every element inside that one block.
- **Mappings are immune to that.** They live outside panel overrides, so a bad ArtAssetID is ignored
  in isolation and poisons nothing — which is why a 326-entry mapping list is no riskier than a
  6-entry one, and why the geometry experiment cannot damage the blanking.
- **Ancestors are named *with their stock geometry* (T14).** The parser walks children, so the
  containing chain has to be spelled out — and an element named without X/Y/Width/Height is built
  at size zero (see *2.1.0*). Element IDs are not unique across the dictionary
  (`VitalsParent` exists in both vitals panels; `AvatarPanel` even nests a `PlayerScaledLevel` inside
  an element of the same name) and the engine resolves a duplicate to the first match top-down — the
  chain is what says which one is meant.
- **Never restate geometry that does not need to change**, and never use a large offset: `-10000` is
  out of range and is accepted for hit-testing but ignored for drawing, which looks exactly like
  "the override was applied but ignored".
- `FileName` resolves relative to the skin folder.

## Tests

`sh tests/run_all.sh` — 13 checks on this skin, 7 on each `ZZ*` probe rung, then 13 injected faults
proving the checks still fire.

| | |
| --- | --- |
| T1 | `SkinDefinition.xml` parses |
| T2 | validates against `lotro-skin.xsd` |
| T3 | no XML comments |
| T4 | every `<PanelFile>` element path resolves in U46.2 **at exactly that nesting depth** — the one failure that is silent *and* total |
| T5 | no duplicate ArtAssetID |
| T6 | every `FileName` resolves to a real file — **a missing one draws an opaque checkerboard in-game** |
| T7 | every blank matches its asset's native size, and says how many of those sizes are inferred rather than measured |
| T8 | every replacement is fully transparent — scope enforcement |
| T9 | every ArtAssetID is known to the U46.2 manifest **or** to the installed client — catches a typo the client would silently ignore |
| T10 | no out-of-scope asset blanked (party, pet, target-of-target, over-the-head, `black_translucent`) |
| T11 | `SkinDefinition.xml` has not drifted from `assets.tsv` |
| T12 | **nothing the live client knows is left unblanked** — the check this skin shipped without, and the reason a frame survived version 1.1.0 |
| T13 | every element named in a `<PanelFile>` still exists in the live client — the snapshot dictionary cannot see a retirement |

T9 needs both sources and neither alone: the pack is frozen at U46.2 while the client is on U50, and
the client scan is exact but not exhaustive. For the same reason **T12 only ever reports additions**
— a name the scan happens to miss must never be read as licence to delete a row.

`xmllint` alone is not enough: `PanelFileID` is an `xs:union` with an open `xs:string` member, so the
schema accepts any string there.

`tests/selftest.py` breaks a throwaway copy thirteen ways — a comment, a stale element ID, a broken
containing chain, an unknown panel ID, a duplicate asset ID, a deleted blank, a wrong-sized blank, an
opaque blank, a typo'd asset ID, a party-frame asset, a silently dropped mapping, a live asset left
unblanked, and an element retired by the client — and requires the matching check to catch each one.
It also keeps a positive control, because a suite made only of faults can pass by rejecting
everything.

## Installing and verifying in-game

1. **Unload the plugins that draw their own vitals or target UI first.** A skin overrides the *game's*
   panels only; it cannot touch a window a plugin draws in Lua. On `ewrson/Orcrist` these autoload:
   **`PrimePlugin`**, **`Potato`**, **`VitalTarget`**, **`Gristle`**. `/plugins unload <name>` takes
   effect immediately and needs no restart. A visible target frame is **not** evidence the stock panel
   is still there.
2. **Fully restart the client.** Relogging does not reload a skin.
3. Ctrl-O → UI Settings → *Current User Skin* → `EffectsOnly` → Accept.
4. Confirm it took: `grep -i skin UserPreferences.ini` must return something. The game writes no skin
   key until one is picked, so an empty result means it is still on the default skin no matter how
   many restarts happened.

What to check, since the cosmetic variants are the likeliest thing to be incomplete:

- **Your own frame**, on the character whose cosmetic frame is actually active.
- Targets: **normal mob, signature, elite, elite master, swarm**, a **friendly NPC**, a **chest or
  door** (`selection_inanimate_backdrop`), and **a player** (PVP rank insignia).
- In and out of combat — the animated layer is what 1.2.0 tries to move, so this is the rung-5
  result — at partial morale, under a temporary morale buff, and under dread.

### If plates are still on screen

Four causes, and they look identical:

1. **The skin was never selected** — `grep -i skin UserPreferences.ini` is empty.
2. **The file failed to parse**, so it is not in the dropdown to select at all. Run `tests/run_all.sh`.
3. **A cosmetic variant is active whose ID is not covered.** This was the cause once already, when
   the skin was built from a U46.2 manifest against a U50 client. Run `python3 tests/scan_client.py`
   and then `sh tests/run_all.sh`: T12 names anything the client knows and this skin does not blank.
4. **An ArtAssetID is wrong** — silently ignored. T9 checks both the manifest and the client, so
   this is now unlikely.

`ZZProbeVitals` (removed 2026-11-25, its job done) distinguished 4 from 1 and 2 in one restart: it maps six primary IDs to a missing
file, so each live ID draws the client's opaque checkerboard. **Run it alone** — the grid covers
whatever is behind it, and an earlier round of conclusions in this project was wrong for exactly that
reason.

## Status

| Rung | | |
| --- | --- | --- |
| 1 | `ZZProbeVitals` — checkerboard liveness on the six primary IDs | **Confirmed 2026-11-17.** Grid drawn over the player panel; level digits and buff icons on top of it |
| 2 | this skin, blanking only | **Confirmed 2026-11-17.** Player plate, border, portrait ring, portrait cover and level plate all gone |
| 3 | the `<PanelFile>` text move | **Failed 2026-11-17** — nothing moved. Reverted; see *Pulling the text in* |
| 3b | `ZZProbeDepth` — the canary the failed test lacked | **Superseded 2026-11-24, probe deleted** — its own path skipped `PanelParent`. Answered by 2.0.0 instead |
| 4 | cosmetic-variant confirmation, and the target panel against each mob rank | **Partly done 2026-11-17.** The target panel blanks correctly on a level 160 mob; the ring and eye survived, which is what 1.2.0 addresses |
| 5 | version 1.2.0 — the 31 U47–U50 assets, and the `*Vitals_Animations` move with its canary | **Failed 2026-11-24** — rank flames still drawn, canary level number did not move. Geometry does not reach children of `Opponent_SelectionField` (row 4 of the canary table). No game option toggles the animation either (client strings searched). Next: `../ZZProbeTarget/` |
| 5b | `ZZProbeTarget` — which target-panel depth obeys geometry | **Failed 2026-11-24 — nothing moved at any depth** (wrong path, see 2.0.0; probe deleted). Every `ID_UISkin_OpponentPanel` override tried in this project has now done nothing, while target-panel `<Mapping>`s work. Leading suspect: the live client has six vitals wrapper elements absent from the U46.2 dictionary, allocated as one batch (IDs 0x10004DB9–DBE): `Vitals_Viewport_Parent`, `Vitals_Core_Parent`, `ViewportParent`, `PanelParent`, `OpponentViewportParent`, `OpponentPanelParent`. If the target tree now nests through them, every chain written from the dictionary is wrong and the whole override is silently dropped. Resolved the same day: the layout is in `client_local_English.dat` (file 0x22000033) and `read_layout.py` recovers it |
| 6 | version 2.0.0 — 31 elements moved via the live tree, mappings kept | **Confirmed 2026-11-24.** Both plates gone, rank flames included. But both trays broke: debuffs under buffs, no tooltips |
| 7 | `ZZProbeEffects` rungs 1–3 → version 2.1.0, ancestors restate geometry | **Confirmed 2026-11-24.** Plates gone, trays split correctly, tooltips work |

One full client restart per rung. Rung 4 still matters in full: the cosmetic families and the other
mob ranks have not been exercised.

## Provenance

`tests/reference/` holds the U46.2 `SkinDictionary.txt` (the element tree — the VS Code extension's
copy is ~U32/2022 vintage and its coordinates have drifted) and `pack_manifest.tsv`, the 4704-entry
asset manifest. Both come from the *Unofficial Update 46.2 Skinning Pack* on lotrointerface, which
is **still the newest pack published** — there is no U47+ pack to upgrade to, which is exactly why
`live_asset_ids.txt` and `live_element_ids.txt`, read from the installed client, now sit beside
them. **No SSG artwork is included in this skin** — every TGA here is a blank generated by
`make_blanks.py`, so unlike an occluder-based skin there is nothing here that would be a problem to
redistribute.

Measured along the way, correcting the older notes: `player_vitals_backdrop` is **273 × 124**, not
273 × 125. Only `player_vitals_legendary_gondor` and `opponent_vitals_legendary_gondor` are 273 × 125.
