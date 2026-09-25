# Handoff: Strontia pop-out page with lessons for middle schoolers

Written 2026-09-25 by the session that built everything else in `teams/team-tbd/`. Two agents
use this: a **builder** (sections 1 to 7) and then a **verifier** (section 8). Read it fully first,
then `AGENTS.md` (repo root), `teams/team-tbd/README.md`, and `teams/team-tbd/FINDINGS.md`.

## 0. What already exists (do not rebuild)

- `analysis/clean_sonde.py → grid_sonde.py → storm_trace.py → autoresearch/prepare.py →
  analysis/fill_best.py → analysis/build_profile_json.py` regenerate everything (see README).
  Outputs land in `analysis/out/` (gitignored) and `map/strontia-profile.json`.
- `map/design-storm-water-system-3d.html`: a copy of the repo's 3D map with a `DATA_ROOT`
  constant, a Strontia depth panel (`renderProfile()` etc., marked "Team addition") on the
  `dam-strontia` marker, and a chat window (also marked "Team addition").
- `chat_server.py`: serves the repo like `serve.py` (same port 8765, bound to 127.0.0.1) plus
  `POST /api/chat`, which runs `claude -p` (the user's Claude Code login, **no API key**), no tools,
  grounded in FINDINGS.md, analysis/QC.md, README.md, glossary.md, analysis/out/storm_numbers.json.
  Streams server-sent events `{"text": ...}`, `{"error": ...}`, `{"done": true}`.
- Chat features already built and liked by the user: 52 suggested questions (`CHAT_QUESTIONS`, by
  topic), 5 random starters from 5 different topics, an "Explore next:" random unasked question
  with a ↻ reroll after each answer, no auto-sent first question, no provisional or tap-water
  disclaimers appended to answers (instruction in `chat_server.py`).

## 1. The ask (user's words, condensed)

1. A **pop out**: open the Strontia Springs Dam panel in its own window.
2. Make it **educational**: walk someone through how everything is interrelated ("notice how
   temperature affects oxygen because ...").
3. Audience: **middle school, ages 13 to 16**.
4. **Questions with 2 to 3 choices.** Reveal the answer either way; if right, give positive
   encouragement ("Good job!", "Nice thinking!").
5. **A lesson list** (visible menu of lessons).
6. **Lessons only on the pop-out page.** The map panel stays as is, plus a button to pop out.

Defaults chosen by the previous session (the user was told and may override):
- A bonus lesson "Data detective" is included (last in the list).
- The chat on the pop-out page speaks at a 13 to 16 reading level; the map's chat is unchanged.

## 2. Deliverables

1. `map/strontia.html`: the pop-out page, two modes: **Lessons** (default) and **Explore**.
2. A pop-out button on the map panel: "↗ Open in its own window" →
   `window.open("strontia.html", "strontia")`. Place it next to "Ask Claude about this picture".
3. `analysis/build_lessons.py` → `map/strontia-lessons.json`: every lesson number and every
   highlight region, computed. **No hand-typed numbers in lesson text** (repo rule: never invent
   numbers). Text templates live in the script and are filled from computed values, the way
   `build_profile_json.py` builds its `findings`.
4. `map/strontia-profile.json` gains `odo_pct_sat` (dissolved oxygen, % saturation). It is not in
   `grid_best.npz`; take it from `grid.npz` (linear fill) and note that in the script docstring.
5. Shared front-end code so the two pages do not diverge: move the chat code (JS + CSS) and the
   heatmap drawing primitives out of the map page into files under `map/` (for example
   `map/team-chat.js`, `map/team-chat.css`, `map/strontia-core.js`) and load them from both pages.
   The map page must behave exactly as before (regression-test it, section 8).
6. `chat_server.py`: accept `"audience": "young"` in the request body and use a second system
   prompt variant (same documents, plus: "The viewer is 13 to 16 years old. Use short sentences
   and everyday words, explain any science word, one idea at a time, friendly tone, under about
   120 words unless asked for more."). Build both variants at startup.
   Lesson context: the pop-out page sends the current lesson title and step in `context`.
7. README: add the pop-out page, the lessons, `build_lessons.py` in the regenerate order (after
   `build_profile_json.py`), and the new files in the file table. Update `.gitignore` only if a
   new generated artifact is not meant to be committed (`map/*.json` are committed).

## 3. Page design (`map/strontia.html`)

Match the map's dark look: reuse its CSS variables (`--panel-bg`, `--panel-ink`, `--panel-ink-2`,
`--panel-line`), the blue sequential ramp `PROFILE_RAMP`, the hatch for "no reading", fonts.
Title `<title>Strontia Springs, by depth</title>`. It must work at phone width (390 px): no
horizontal scroll, lesson list collapses (e.g. a select or a scrollable row).

**Lessons mode**
- Left: lesson list (numbered, title, a ✓ when finished). Progress saved in `localStorage`
  wrapped in try/catch (must work when storage throws).
- Main: lesson card with steps: **Look** (visual + highlight + one sentence telling them where to
  look) → **Question** (2 to 3 choice buttons) → **Reveal** (right: "Good job!"/"Nice thinking!"
  style praise + explanation; wrong: kind "Not quite, here is what happened" + explanation; always
  show the correct answer) → **Why it happens** (general-knowledge explanation, labelled "Why") →
  Next lesson. Back/Next buttons. Randomise praise from a small list.
- Each lesson has "Ask Claude about this" which opens the chat with the lesson context (do not
  auto-send a question; the user explicitly does not want that).
- Reading level: short sentences, everyday words, analogies (label analogies as comparisons).

**Explore mode**
- Stacked heatmaps on one time axis: temperature, dissolved oxygen (mg/L), oxygen % saturation,
  turbidity, specific conductance. **Linked crosshair**: hovering/touching one shows the same
  time and depth on all, with a readout listing every value at that point. Storm / whole-season
  toggle as on the map panel. Gage turbidity strip and plant TOC strip in the storm view.

**Visuals lessons need**: heatmaps with a highlight rectangle (time range × depth range, from
the JSON), and small line charts (daily medians by depth band). One axis per chart; no dual-axis
charts (load the `dataviz` skill before writing chart code).

## 4. Lessons (content spec; numbers must come from `build_lessons.py`)

Values below were computed by the previous session and are for **cross-checking only**. Sources:
`analysis/out/sonde_clean.csv` (use `cast_kind == "full"` for depth-band statistics),
`analysis/out/storm_numbers.json`, `analysis/out/storm_casts.csv`, `data/USGS_South_Platte.csv`,
`data/SouthPlatteFlow.csv`, `data/FoothillsInfluent.csv`.

| # | Title (kid voice) | Look at | Question (answer first) | Numbers to show |
|---|---|---|---|---|
| 1 | How to read the water scan | temperature heatmap, season | "Near-white means the water is…" **warmer** / colder / muddier | axis explanation only |
| 2 | Warm water floats | temperature, season, highlight July top layer | "In July, where is the warmest water?" **top** / middle / bottom | July monthly median surface (1–3 m) 18.44 °C vs deep (≥40 m) 14.63; biggest daily gap 7.6 °C on May 15; stratified from Apr 7 (gap 5.3 °C) to the end |
| 3 | Warm water holds less oxygen | line charts, monthly (or daily) surface temp, DO mg/L, DO % sat | "As the water warmed from April to July, the oxygen in it…" went up / **went down** / stayed the same | surface temp 9.87 → 18.44 °C, DO 9.28 → 7.59 mg/L, % sat ~82 → ~81 (flat). Twist: the water stayed about as "full" as it could be; warm water just holds less (like a warm soda going flat, labelled as a comparison) |
| 4 | The bottom is cut off from the air | % saturation heatmap, highlight ≥40 m | "Why is deep water less full of oxygen (~70%) than the top (~81%)?" **far from the air and the layers stop mixing** / fish breathe it all / the sensor is broken | deep % sat monthly 70.3, 70.2, 72.6, 70.7, 74.8 (Apr–Aug); surface ~81–82; lowest deep daily median DO 6.5 mg/L (Jul 18); lowest single reading 5.9 mg/L. Good news: it never ran out |
| 5 | Cold river water sinks | line chart Aug 1–12: deep temp, deep DO, river temp | "In early August the river was colder than all the lake water. Where did it go?" top / middle / **bottom** | deep temp 15.70 (Aug 4) → 14.29 (Aug 11); deep DO 6.94 → 8.09 mg/L (Aug 9); river 15.1 → 13.1 °C; flow 469 → 582 cfs |
| 6 | Follow the storm's mud | turbidity storm heatmap + gage strip, highlight the layer | "Where did the river's mud show up in the lake?" top / **middle** / bottom | gage peak 329 FNU at 01:45 Aug 15; lake peak 23.1 NTU at 13 m, 12:06 Aug 16, 34 h later; layer ~8–18 m; river 16.0 °C vs reservoir that warm at ~5 m |
| 7 | The muddy layer sinks and fades | turbidity storm heatmap, highlight Aug 16–19 | "Over the next days the muddy layer…" vanished at once / **sank deeper and faded** / rose to the top | peak depth by day 7.5, 12, 13, 14, 20, 21 m (Aug 14–19); peak NTU by day 6.0, 19.6, 23.1, 17.5, 10.4, 8.0; still there Aug 19 |
| 8 | Mud and rainwater travel together | specific conductance storm heatmap, same highlight | "The muddy layer had fewer dissolved minerals. Why?" **it's rainwater, which has few minerals** / the mud ate them / the sensor got muddy | layer 6–12 µS/cm below normal; river 296.5 → 280 µS/cm |
| 9 | What reaches the water plant | TOC strip | "The plant's organic carbon jumped on Aug 16. Can we be sure the storm caused it?" yes, definitely / **probably, but we need more information** / no | TOC 2.0 → 2.5 mg/L on Aug 16; a jump that size in 0.7% of 448 summer day-to-day changes; the intake depth is unknown (the missing clue) |
| Bonus | Data detective | ORP or chlorophyll season heatmap with dotted service lines | "Every depth changed at the same moment on Jun 16. Most likely?" the whole lake changed instantly / **someone cleaned or adjusted the sensor** / a fish bumped it | service dates Apr 28, May 4, May 14, May 18, Jun 16, Jul 20, Aug 18; conductivity-not-corrected story (correlation 0.98 → 0.00) optional |

Highlight regions must be computed (e.g. July × 0–3 m from the thermocline stats; the storm layer
from `storm_casts.csv` time span and median layer top/bottom; deep band ≥40 m; early-August window).
General-knowledge explanations (warm water is less dense; warm water holds less dissolved gas;
oxygen enters from the air and from algae in sunlight; decomposers use oxygen at depth; mud
settles) must be marked as "Why" / general knowledge, never presented as findings from the data.
Don't claim anything about tap-water safety.

## 5. Constraints and repo rules

- Work only in `teams/team-tbd/`. Never edit `data/`, `scripts/`, `figures/`, `reference/`, the
  root `design-storm-water-system-3d.html`, or root `serve.py`.
- Denver Water data terms travel with derived data: `map/DATA-TERMS.md` exists; add a short
  attribution line on the new page (copy the map panel's `terms` field from the profile JSON).
- Numbers only from scripts. Say "provisional" once on the page (footer), not on every answer.
- Do not commit or push. Do not publish anything outside the repo.
- Keep the map page's existing behaviour identical apart from the pop-out button.

## 6. Environment gotchas (these cost the previous session time)

- Python: `teams/team-tbd/.venv/bin/python` (pandas etc.). System python has no pandas.
- **The user's chat server is running on port 8765** (a background task of the main session).
  **Do not kill it.** Test your changes on another port:
  `python3 teams/team-tbd/chat_server.py 8767` (from the repo root; run it in the background with
  the sandbox disabled, because it spawns `claude` which needs network and the keychain). The
  main session restarts 8765 after you finish.
- The Claude-in-Chrome extension is attached to a **Windows machine that cannot reach this Mac**.
  Use local headless Chrome through Playwright instead: a venv exists at
  `/private/tmp/claude-502/-Users-msmith-Downloads-ddd-temp-design-storm-2026/eb71962f-0b72-463f-9690-bbeac2adbedb/scratchpad/pwenv/`
  (`pwenv/bin/python`, `channel="chrome"`, args `--use-angle=swiftshader
  --enable-unsafe-swiftshader`). Example scripts in the same folder: `check_profile.py`,
  `check_chat.py`, `qs.py`. Running them needs the sandbox disabled (network to localhost).
- `annotateGlossary(el)` rewrites `el.innerHTML`: call it before drawing canvases or attaching
  handlers inside that element, and only on prose elements (not buttons).
- Each chat call runs `claude -p` and costs the user's Claude Code usage: keep chat tests to a
  handful of questions.
- The chat server builds its system prompt at startup: restart your test server after edits.

## 7. Builder: definition of done

- All deliverables in section 2 exist; `build_lessons.py` runs from a clean `analysis/out/`
  after the existing pipeline, and its output is byte-identical on a second run.
- Every number in `strontia-lessons.json` text traces to a computed value (print a table of
  value → source in the script's stdout).
- `strontia.html` works at 1400 px and 390 px: every lesson loads, choices reveal feedback
  (right and wrong paths), progress ✓ persists across reload, Explore crosshair is linked.
- Map page regression: same panel, same chat behaviour, pop-out button opens the new page.
- No console errors on either page (the known DWR CORS error on the dam's live storage chart is
  pre-existing and acceptable).
- Write `HANDOFF-lessons-REPORT.md` next to this file: what was built, file list, commands, test
  evidence (paths to screenshots), anything skipped or uncertain, and questions for the user.

## 8. Verifier: checklist

Do not trust the report; check.
1. Regenerate: run the full pipeline (README order) plus `build_lessons.py`; confirm the JSON is
   reproduced and `git status` shows changes only under `teams/`.
2. Numbers: for every lesson, recompute each quoted number independently (your own short script
   from the CSVs, not the builder's code) and compare. List any mismatch.
3. Content: every "Why" explanation is labelled as general knowledge; no finding is overstated
   (e.g. the TOC link must stay "probably"); reading level fits 13 to 16; no tap-water claims.
4. Questions: each has 2 or 3 choices, exactly one correct, correct answer revealed on both paths,
   praise shown only when right.
5. UI (headless Chrome, 1400 px and 390 px): lesson list, Back/Next, progress persistence with
   storage working and with storage throwing, Explore linked crosshair, pop-out button on the map,
   chat opens without auto-sending, chat on the pop-out answers at a young reading level (one or
   two questions only).
6. Map page regression: dam panel, both views, parameter chips, hover readout, chat, tour and
   storm replay still work.
7. Write `HANDOFF-lessons-VERIFY.md`: pass/fail per item with evidence, fixes you made (keep them
   small; list them), and **open questions for the user** where the spec was unclear.
