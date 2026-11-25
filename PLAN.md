# Plan — `EffectsOnly`

A fresh skin that replaces as many art assets as possible on the **player vitals**
(`ID_UISkin_AvatarPanel`) and **target vitals** (`ID_UISkin_OpponentPanel`) panels with **transparent
blank TGAs**.

Scope decided 2026-11-17:

- **`<Mapping>` only.** Nothing opaque. No occluders.
- **No `<PanelFile>` at all.** No geometry, no offsets, no resizing — nothing moves.
- **Maximum asset coverage** on the two vitals panels.
- Both stock buff/debuff effect trays stay.

The `ui/skins/` tree is empty — this is a clean build. The previous skin (`EffectsOnly`) is in
`~/.local/share/Trash/files/EffectsOnly/` and is the record of what was already proven in-game; this
plan reuses its findings and its blank-TGA generator, and discards its occluder approach.

---

## Status — implemented 2026-11-17

**Phases 1–4 are done and fully validated offline. Phase 5 (in-game) is the only part remaining, and
it cannot be done outside the client.**

| Phase | State |
| --- | --- |
| §2 prerequisite — acquire the ArtAssetID list | **Done.** The pack ships its own `SkinDefinitions.xml`: the complete **4704-entry** manifest, better than the filename sweep this plan assumed. It and the U46.2 `SkinDictionary.txt` are in `tests/reference/` |
| §3 asset inventory | **Done.** 295 assets in scope — 105 player, 155 target, 35 shared. Every native size measured from the stock TGA headers. `tests/reference/assets.tsv` |
| §4 cosmetic-variant sweep | **Done.** Enumerated from the manifest rather than from memory, and far larger than the 60–100 estimated |
| §5 generate + assemble | **Done.** 13 transparent blanks; `SkinDefinition.xml` with 295 mappings and no `<PanelFile>` |
| §6 validation | **Done.** 11 checks pass; `selftest.py` proves every one fires against 9 injected faults |
| §7 in-game verification | **Not started.** One client restart per rung. `../ZZProbeVitals/` is built and ready as rung 1 |

Operating detail now lives in `README.md`; this file is kept as the record of how the approach was
decided. Where reality differed from the plan as written:

- **The filename sweep was unnecessary.** The pack's own `SkinDefinitions.xml` is an authoritative
  ArtAssetID list, so §3's regex sweep became a filter over real data instead of a guess.
- **`_mini` turned out to be the dangerous prefix.** Over 100 `player_vitals_backdrop_mini*` and
  `player_vitals_mini_*` assets are the **fellowship** frames. They match a naive `player_vitals_*`
  rule, and blanking them would have silently stripped party frames. T10 now fails the build if one
  reappears.
- **Four asset families the plan did not anticipate** are in scope and now covered:
  `pvp_*_stars_opponent*` (20 — the target's rank insignia), `opponent_vitals_open_tapped*` (3),
  `opponent_progress_overlay_*` (3), and `level_background`'s `_rare` / `_red` / `_scion` /
  `_portrait_borders` siblings (4).

---

## 0. What this skin will and will not remove

A transparent blank removes **artwork**. It cannot remove text, dynamic renders, or anything that has
no art asset behind it. That is the whole boundary, and it is measured, not assumed.

**Gone** — every static plate, frame, border, cover, backing and rank icon on both panels:

- the player vitals plate and its whole cosmetic-variant family
- the player portrait cover and level plate
- the PVP rank icons (player and monsterplay)
- the target vitals plates for every mob rank, plus the friendly-NPC variants
- the target portrait cover and level plate
- the chest/door/crafting-station plate and foreground
- the lock-on reticle

**Still on screen afterwards:**

| What | Why it survives |
| --- | --- |
| player name, target name, class | text glyphs, not textures |
| level digits (both panels) | glyphs, and they draw in front of the plate anyway |
| **morale and power bar fills** | **no bar-fill asset exists.** Not in the 2007 dictionary, not in a modern 2761-entry skin. It was requested of SSG and never granted — XP bar fills exist (`xpbar_blue_fill`), there is no vitals equivalent |
| morale / power numbers | glyphs |
| both portrait images | a live render of the character or target head, not a skin asset |
| the combat animation glow | `PlayerVitals_Animations` / `OpponentVitals_Animations` are **animated** asset arrays, and animated assets cannot be mapped at all |

So the result is **frameless vitals**: bars, numbers, names and portraits floating with no chrome
around them.

One thing to expect that runs against intuition, confirmed in-game 2026-11-15: the player's name,
bars, portrait and rank are drawn **behind** `player_vitals_backdrop` and show through the
transparent windows in it. Blanking that texture therefore makes them *more* exposed, not less — in
the earlier investigation a transparent blank in place of that asset is exactly what brought them
back after an opaque test had hidden them. Nothing here will hide them; only an opaque replacement or
a container move could, and both are out of scope by decision.

Also note: **a blanked texture leaves its hit region intact.** Both panels stay clickable and
draggable exactly where their frames used to be.

## 1. What is already settled — do not spend restarts re-testing it

| Fact | Status |
| --- | --- |
| A bad **ArtAssetID** is silently ignored and poisons nothing | Proven. This is why a Mapping-only skin can be aggressive — see §3 |
| A bad **element ID** silently aborts an entire panel override | Proven. Irrelevant here: no `<PanelFile>` is used |
| A **missing `FileName`** draws an opaque checkerboard grid | Proven. Useful as a deliberate probe (§6), never acceptable shipped |
| `<Mapping>` is **global**, not panel-scoped | Confirmed in the schema. Blanking a shared asset changes every panel using it — see §3 |
| Mapping cannot remove **text** | Proven |
| **Animated** assets cannot be mapped | Proven |
| There is no morale-bar or power-bar fill asset | Researched exhaustively |
| Player, fellowship, pet, target-of-target and over-the-head bars each have their **own** asset ID | Confirmed. Party and raid frames are safe |
| `player_vitals_backdrop` is **273 × 124** | Measured today. The old notes say 273 × 125; the U46.2 dictionary agrees with 124 |
| `OpponentPanel`'s container is `VitalsParentOpponent`, not `VitalsParent` | Confirmed in U46.2. Irrelevant here, but it is why every published target-panel skin looks broken |

Verified fresh today: `<Mapping>` is a top-level child of `<opt>`, and the schema enforces **one
Mapping per ArtAssetID** — no duplicates.

## 2. Blocking prerequisite — re-acquire the ArtAssetID list

**There is no ArtAssetID list anywhere on this machine.** Checked today: `grep -c ArtAssetID` returns
**0** for the VS Code extension's `SkinDictionary.xml`, for `SkinDictionary-extra.xml`, and for the
U46.2 `SkinDictionary.txt`. Those dictionaries carry element IDs and geometry only. Asset IDs exist
only as the **filenames** of the TGAs in the Unofficial Update 46.2 Skinning Pack — which is also the
only source for each asset's native size.

Without it this skin cannot be written. There is nothing to guess from.

What survives locally:

- **U46.2 `SkinDictionary.txt`** — recovered from Trash to the session scratchpad as
  `SkinDictionary_U46.txt`. Copy it to `tests/reference/`. Needed for the element tree, not for assets.
- **A partial native asset set** at `~/Downloads/PrimePlugins/Vitals/Images/Vitals/` — 62 TGAs, of
  which the real ones are `player_vitals_backdrop.tga` (273×124), `player_vitals_lowrescover.tga`
  (63×63), `opponent_vitals_backdrop_mp.tga` (273×124), `player_vitals_legendary_isengard.tga`, and
  ~20 cosmetic backdrops. The rest are PrimePlugins' own joke portraits. Enough to start; not enough
  to enumerate the cosmetic family or the opponent covers.

Download with the cookie-jar form — the `download.php?...` form hits a Cloudflare challenge and 403s:

```sh
curl -c jar -b jar -L -O \
  https://www.lotrointerface.com/downloads/download1204-UnofficialUpdate46SkinningPack
```

Tooling is all present: `magick`, `convert`, `python3` with numpy 2.5.4 + Pillow 13.0.0, `xmllint`,
`curl`.

## 3. Phase 1 — asset inventory, erring on the side of more

Because a misspelled or dead ArtAssetID is **silently ignored and cannot poison anything**, the right
strategy for "as much as possible" is to blank every asset plausibly belonging to these two panels
rather than to hand-pick a minimal set. A 150-entry Mapping list is no riskier than a 10-entry one.

Build `tests/reference/assets.tsv` from the pack recording **ArtAssetID → native WxH → which element
it draws → in or out**, then sweep the pack filenames for anything matching:

```
player_vitals_*      opponent_vitals_*     opponenet_vitals_*   (sic — real typo, see §4)
*_vitals_backdrop*   level_background      icon_pvp_rank_*
swarm_vitals*        inanimate*            lockon* / lock_on*
```

Known starting points:

**Player side**

| ArtAssetID | Element | Native size |
| --- | --- | --- |
| `player_vitals_backdrop` | `AvatarPanel_BG` — frame, border *and* portrait ring, one texture | 273 × 124 (measured) |
| the cosmetic family (§4) | same element, when a cosmetic frame is active | 273 × 124 |
| `player_vitals_lowrescover` | `AvatarPanel_COVER_LOWRES` | 63 × 63 (measured) |
| `level_background` | `PlayerLevel_BG` — **and** `OpponentLevel_BG`; no opponent equivalent exists | 62 × 31 (to confirm) |
| `icon_pvp_rank_*_32` | `PlayerPVP_RankDisplay` — 15 ranks plus `_monsterplayer_` twins | 32 × 32 |

**Target side**

| ArtAssetID | Element | Note |
| --- | --- | --- |
| `opponent_vitals_backdrop` | `OpponentPanel_BG` | 273 × 124 (measured via the `_mp` twin) |
| `_signature` / `_elite` / `_elitemaster` / `swarm_vitals` | same element, per mob rank | all needed, or an elite still draws a frame |
| `opponent_vitals_backdrop_*_good` | friendly-NPC rank plates | |
| opponent lowres cover | `OpponentPanel_COVER_LOWRES` | asset ID not yet known — find it in the pack |
| inanimate plate + foreground | `InanimateObjectPanel_BG`, `InanimateObjectForeground` | the chest / door / crafting-station plate |
| lock-on reticle | `LockOnOverlay` | sits directly under `OpponentPanel` |

### Three exclusions, and why

- **`black_translucent`** — the bar backing (`VitalsBg` / `OpponentsVitals_BG`). It is **shared with
  the crafting panel and others**, so blanking it changes unrelated UI. Left out by default, but it
  *is* in-scope art for these panels, so it is flagged as a deliberate opt-in: say the word and it
  goes in, accepting the crafting-panel side effect. Worth knowing it is the one asset that would
  visibly de-chrome the bars themselves.
- **`PlayerVitals_Animations` / `OpponentVitals_Animations`** — animated arrays, unmappable. Not a
  choice.
- **`player_vitals_backdrop_mini`** (fellowship), **`pet_vitals_backdrop_mini`**,
  **`target_vitals_backdrop_mini`** (target-of-target), **`floaty_vitals_overlay`** (over-the-head).
  Out of scope — the request is the self and target panels, and these have their own IDs, so party,
  pet and raid frames stay untouched.

### One thing not to blank by accident

The effect trays must stay. If the sweep turns up any effect-slot chrome (a tray border, slot
backing, or timer ring asset), **leave it out** — blanking it would strip the buff icons' framing.
`PlayerEffectDisplay` / `OpponentEffectDisplay` icons are per-effect game icons, not skin assets, so
the icons themselves are not at risk; only their chrome would be.

## 4. Phase 2 — the cosmetic-variant sweep

Which plate actually draws depends on account state. There is a large family —
`player_vitals_backdrop_VIP`, `_1_year` … `_22_years`, `_u42_base`, `_U45_malice_FP`,
`player_vitals_legendary_*`, festival and expansion variants, each with an `_mp` monsterplay twin.
**Blanking the base ID alone looks like a no-op if the character displays a cosmetic frame.**

- Case is inconsistent *on purpose* (`_VIP` but `_u42_base`) — reproduce it exactly.
- Some real IDs contain **typos that must be reproduced** (`opponenet_vitals_legendary_isengard`).
- Enumerate from the pack's filenames, not from memory. Expect 60–100 entries from this family alone,
  and a total Mapping count of roughly 100–150.
- Confirm on the character whose frame is actually active before calling this done.

## 5. Phase 3 — generate the blanks, and assemble

Recover **`tests/make_blanks.py`** from Trash. It writes uncompressed 32-bit BGRA TGAs, bottom-left
origin — a known-good writer, keep it as-is. `make_frame.py` from the old skin is **not used**: it
builds occluders, which are out of scope.

- One transparent blank **per distinct native size**, named for it: `blank_273x124.tga`,
  `blank_63x63.tga`, `blank_62x31.tga`, `blank_32x32.tga`, and whatever else §3 turns up.
- **Native size, always.** Oversizing is the one thing reported to misbehave, so no shared 1×1 blank.
- Fully transparent (alpha 0) everywhere. No exceptions — that is the point of this version.

```
ui/skins/EffectsOnly/
  SkinDefinition.xml          # <opt>: SkinName + ~100-150 <Mapping>. No <PanelFile>.
  EffectsOnly.skincompendium  # carries a second copy of the version — keep in step
  README.md                   # all prose lives here
  blank_*.tga
  tests/{run_all.sh,validate_skin.py,selftest.py,make_blanks.py,reference/,fixture/}
```

- **No XML comments in `SkinDefinition.xml`.** The client's parser walks child nodes and appears not
  to be node-type aware (`Error getting children nodes in UILOverride`); no known-good community skin
  contains comments. A file that fails to parse vanishes from the in-game dropdown with no error at
  all.
- `FileName` resolves relative to the skin folder, uses Windows backslashes, and `..\` traversal
  works.
- Never map the same ArtAssetID twice — schema-enforced, but catch it locally first.

## 6. Phase 4 — validation before the client ever sees it

Recover `tests/` from Trash and adapt. The element-path checks are largely moot without a
`<PanelFile>`, so the suite shifts to the Mapping side:

Keep: schema validation against `xsds/lotro-skin.xsd`, and `selftest.py`'s injected faults proving
the checks still fire.

Add or rewrite:

- **Every `<Mapping FileName>` resolves to a file that exists.** A missing file draws an opaque
  checkerboard in-game; shipping one would be worse than shipping nothing.
- **Every blank's pixel dimensions match the asset's native size** from `assets.tsv`.
- **Every blank is fully transparent** — a one-line alpha check that enforces the scope decision, so
  no opaque texture can creep back in.
- **No duplicate ArtAssetID.**
- `DEFERRED` — the honest inventory of what this skin does not handle (the §0 survivors, plus
  `black_translucent`), printed in full on every run so trimming can never quietly hide a gap.

## 7. Phase 5 — in-game verification

**One full client restart per rung. Relogging does not reload a skin.**

Before interpreting anything:

1. **Rule out plugin-drawn UI.** A skin overrides the game's panels only. On `ewrson/Orcrist` these
   autoload and draw their own vitals or target UI: **`PrimePlugin`**, **`Potato`**, **`VitalTarget`**,
   **`Gristle`**. `/plugins unload <name>` takes effect immediately with no restart — do it first. A
   visible target frame is not evidence the stock panel is still there.
2. **Confirm the skin is actually selected.** Ctrl-O → UI Settings → *Current User Skin* → Accept. The
   game writes no skin key until one is picked — `grep -i skin UserPreferences.ini` returns **0 hits
   right now**, so the client is on the default skin regardless of how many restarts happen.

Rungs:

| Rung | What | Note |
| --- | --- | --- |
| 1 | **Liveness probe.** Map the 5–6 primary IDs to a deliberately bogus `FileName` → a checkerboard confirms each ID resolves on this client | **Run alone.** The grid is opaque and covers the very things you would otherwise be looking at. One earlier round of conclusions was wrong for exactly this reason |
| 2 | The full transparent-blank sweep | Expect: all plates, covers, borders and rank icons gone; names, level digits, bars, numbers, portraits and the combat glow remain (§0) |
| 3 | Cosmetic-variant verification | On the character with the active cosmetic frame |

Coverage for rungs 2–3 — vary one axis at a time; an earlier five-cell matrix came back uniformly
negative because every cell shared one bad assumption:

- Targets: normal mob, signature, elite, elite master, swarm, friendly NPC, **a chest or door**
  (`InanimateObject_SelectionField`), **a player** (PVP rank icon), and a Beorning if available
  (`RageMeter`).
- Player: in and out of combat (the animation glow), full and partial morale, under a temporary morale
  buff, and under dread.

## 8. Three failure modes that all look identical

Plates still on screen means one of:

1. **The skin was never selected** — `grep -i skin UserPreferences.ini` is empty.
2. **The file failed to parse**, so it is not in the dropdown to select at all.
3. **An ArtAssetID is wrong** — silently ignored. Or the active plate is a **cosmetic variant** whose
   ID was not in the list (§4), which is by far the likeliest cause here.

Rung 1's checkerboard probe distinguishes 3 from 1 and 2 in a single restart.

## 9. Open questions for the build

1. ~~What is the opponent lowres-cover ArtAssetID?~~ **Resolved: `monster_vitals_lowrescover`,
   63 × 63.** Covered.
2. ~~Is `level_background` really 62 × 31?~~ **Resolved: yes, measured.** Four siblings also exist
   (`_rare`, `_red`, `_scion`, `_portrait_borders`) and are all covered.
3. **Still open — your call:** blank `black_translucent` too? It is the bar backing on both panels,
   and the only asset that would de-chrome the bars themselves, at the cost of changing the crafting
   panel and anything else sharing it. Left out by default (§3). Adding `black_translucent` and
   `black_translucent2` to `tests/reference/assets.tsv`, dropping them from `FORBIDDEN` in
   `validate_skin.py`, and re-running `tests/run_all.sh` is the whole change.
4. **Still open — after rung 2:** is frameless-but-visible bars the look you want? If the floating
   bars and name turn out to be the problem rather than the chrome, the only levers that reach them
   are an opaque replacement (occlusion) or a container move — both out of scope here, and the
   second would mean revisiting the effect-tray decision.
