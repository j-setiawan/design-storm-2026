# Builder report: Strontia pop-out page with lessons

Written 2026-09-25 by the builder session for `HANDOFF-lessons.md`. Nothing is committed.

## What was built

- **Pop-out page** `map/strontia.html` (`<title>Strontia Springs, by depth</title>`), two modes:
  - **Lessons** (default): numbered list with a ✓ per finished lesson (a `<select>` below 820 px),
    and a **Reset progress** link under it (asks once to confirm; added at the user's mid-build
    request). The lesson card has three steps: **Look** (a sentence saying where to look, plus the
    visuals) → **Question** (2 or 3 choices; Next is blocked until they answer) → reveal (right:
    a random praise such as "Good job!" or "Nice thinking!"; wrong: "Not quite, here is what
    happened." Both paths show "The answer: …" and the explanation, and mark the right choice
    and the wrong pick with ✓/✗ and text, not colour alone) → **Why** (labelled "Why it happens ·
    general science, not from this data", plus a "Comparison: …" analogy) → Next lesson.
    Back/Next buttons. "Ask Claude about this" opens the chat and sends nothing. Progress is
    saved in `localStorage`, with every access in try/catch.
  - **Explore**: storm or whole season. Five stacked heatmaps (temperature, DO mg/L, DO %
    saturation, turbidity, specific conductance) on one time axis, a **linked crosshair** drawn
    on every panel, and a sticky readout that lists every value at that time and depth. The storm
    view adds the gage turbidity strip on top and the TOC strip below.
  - Footer: "Readings are provisional" (said once, here), the profile JSON's `terms` text, a
    link to `DATA-TERMS.md` and a link back to the map.
- **Map panel**: an "↗ Open in its own window" button beside "Ask Claude about this picture"
  (the two sit side by side), which runs `window.open("strontia.html", "strontia")`. Nothing else
  on the map changed (see the regression test below).
- **`analysis/build_lessons.py` → `map/strontia-lessons.json`**: 10 lessons (9 plus the bonus
  "Data detective"). All 125 numbers and dates in lesson text are filled in from computed values,
  and the script prints a value → source table. The highlight boxes are computed too: the warmest
  month × top 3 m, ≥40 m × the whole season, the storm layer (layer casts from the gage onset to the
  last cast × the median layer top and bottom), the casts after the reservoir peak × their layer
  extent, and ±2 days around the service event with the largest chlorophyll drop. The daily
  peak-depth dots sit at the mean time of each day's layer casts. The script asserts the premises
  that questions depend on (for example that the river on its coldest day was colder than every
  1 m daily median in the lake).
- **`map/strontia-profile.json`** gains `odo_pct_sat` ("Oxygen saturation", %), taken from
  `grid.npz` (linear fill) because the fill-in experiment did not include it. The
  `build_profile_json.py` docstring says so. All other content is byte-for-byte unchanged (checked
  by diffing the parsed JSON with the new key removed). The file grew from 1.4 MB to 1.67 MB.
- **Shared front-end code**:
  - `map/strontia-core.js`: ramp, scales, `drawHeat` (cached image plus hatch, axes, service
    lines and gage peak; returns the geometry and a `pick()`), highlight boxes, dots, strips, and
    a small line chart with a snapping crosshair.
  - `map/team-chat.js` and `map/team-chat.css`: the chat window, built by
    `TeamChat.mount({...})`. Each page supplies its own questions, context note, texts and
    audience.
  - The map page now loads these files. Its chat questions and `chatContext()` stay in the page.
    In the CSS, `#chat` and `#chat-open` changed from `position: absolute` to `fixed` so they work
    on the scrolling pop-out; on the map this renders identically (the regression test compared
    their bounding boxes).
- **`chat_server.py`**: builds both system prompts at startup (`SYSTEMS`). A request with
  `"audience": "young"` gets the second one: the same documents plus the specified text for
  ages 13 to 16. The pop-out's context note sends the lesson number, title, step, question,
  correct answer, the viewer's answer, and the last hovered value.
- **Kid chat questions** (`KID_QUESTIONS` in `strontia.html`): 19 questions in 6 topics. The
  greeting names the current lesson and refreshes when the lesson changes.
- **Docs**: README (the pop-out section, the chat audience, `build_lessons.py` in the regenerate
  order after `build_profile_json.py`, and the new files in the table). `map/DATA-TERMS.md` now
  also covers `strontia-lessons.json` and the pages. `.gitignore` is unchanged because
  `map/*.json` are committed.

## Files

New: `analysis/build_lessons.py`, `map/strontia.html`, `map/strontia-lessons.json`,
`map/strontia-core.js`, `map/team-chat.js`, `map/team-chat.css`, `HANDOFF-lessons-REPORT.md`.
Changed: `analysis/build_profile_json.py`, `map/strontia-profile.json`,
`map/design-storm-water-system-3d.html`, `chat_server.py`, `README.md`, `map/DATA-TERMS.md`.
Nothing outside `teams/team-tbd/` was touched (`git status`: only `?? teams/` and the existing
`?? __pycache__/`).

## Commands

```
cd teams/team-tbd
# full pipeline from an empty analysis/out/ (about 17 s):
.venv/bin/python analysis/clean_sonde.py && .venv/bin/python analysis/grid_sonde.py && \
.venv/bin/python analysis/storm_trace.py && .venv/bin/python autoresearch/prepare.py && \
.venv/bin/python analysis/fill_best.py && .venv/bin/python analysis/build_profile_json.py && \
.venv/bin/python analysis/build_lessons.py        # prints the value -> source table
# test server (from the repo root): python3 teams/team-tbd/chat_server.py 8767
```

## Test evidence

Test scripts and screenshots are in the session scratchpad
(`/private/tmp/claude-502/-Users-msmith-Downloads-ddd-temp-design-storm-2026/eb71962f-0b72-463f-9690-bbeac2adbedb/scratchpad/`).

- **Reproducibility**: I moved `analysis/out/` aside and ran the full pipeline plus
  `build_lessons.py`. `strontia-lessons.json` (md5 `e93211fd…`) and `strontia-profile.json`
  (md5 `961cee7b…`) came out byte-identical to the previous run, and a second run of
  `build_lessons.py` was identical too. The original `analysis/out/` is kept at
  `scratchpad/out-backup` (it can be deleted).
- **`check_lessons.py`** (headless Chrome, 1400 px and 390 px): 131 checks, 0 failures. Covered:
  every lesson loads; each has 2 or 3 choices; Next is blocked before an answer; right answers
  (even lessons) show praise and the answer; wrong answers (odd lessons) show "Not quite" with
  no praise and the right answer; the Why box is labelled; the heatmap and line-chart hover
  readouts work; ✓ progress survives a reload and the page reopens at the last lesson; there is no
  horizontal scroll in either mode; the Explore readout lists all five values and the crosshair
  pixels are drawn on every panel (heatmaps and strips); the season view works from another
  panel; the chat opens with 5 starters and sends nothing; there are no console errors. With
  `localStorage` throwing, the page works and ✓ lasts for the visit. Screenshots:
  `les-{desk,phone}-NN-{look,reveal}.png`, `les-*-02-why.png`, `les-*-explore-{storm,season}.png`,
  `les-*-chat.png`, `les-desk-03-viewport.png`, `les-desk-09-viewport.png`.
- **`check_reset.py`**: Reset progress needs a second tap to confirm, then clears the ticks and
  answers and returns to lesson 1; after a reload it is still at 0 of 10. Tested at both widths
  with no errors (`reset-390.png`).
- **`check_map_reg.py`**: the old map page (a temporary copy of the pre-change file, since
  deleted) against the new one, at both widths. Identical: the heatmap canvas pixels (storm and
  season), gage and TOC strip pixels, hover readouts, colour key, title, chat intro, header,
  placeholder, fine print, the `chatContext()` string, the starter count, the chat window and
  button positions, and the tour text. The storm replay starts and exits on both pages (the frame
  time differs only because it is animating). No console errors on either page (the DWR CORS
  error did not appear this run). The pop-out button opens `strontia.html` in a popup.
  Screenshots: `reg-*.png`, `map-popout-btn-{1400,390}.png`.
- **Chat**: 2 real calls on port 8767. (1) On the pop-out, lesson 3 answered wrong, then "Why did
  the oxygen go down when the water warmed up?". The request carried `"audience":"young"` and
  the lesson context. The answer was friendly with short sentences, labelled general knowledge,
  and used the soda comparison; it ran to 132 words against the "about 120" target
  (`chat-young-desk.png`). (2) On the map, "What is an interflow?": no `audience` field, and the
  usual adult-level answer.

## Skipped or uncertain

- **Correlation story in the bonus lesson** (optional: conductivity correlation 0.98 → 0.00) was
  left out to keep the lesson short. The bonus uses the service dates and the chlorophyll segment
  medians (0.88 → −0.19 µg/L on Jun 16; a negative value is the clue).
- The deep % saturation question says about **72%** against **82%** (whole-season medians of the
  readings). The handoff said "~70% vs ~81%"; those numbers were never computed as such, so the
  computed ones are used. The monthly deep values (70, 70, 73, 71, 75) match the handoff's
  cross-check.
- **The "coldest lake water" premise** in lesson 5 is checked on the river's coldest day (Aug 9:
  river 13.1 °C against the lake's coldest 1 m daily median of 14.5 °C). The early-August
  explanation is worded as "the team's best explanation, not something the data proves".
- Line charts have a legend when there are 2 series and a hover readout, but no direct labels at
  the line ends (the phone width leaves no room) and no table view.
- Chart titles and highlight labels (e.g. "Top 3 m", "deeper than 40 m", "July, top 3 m") are
  built from the script's band constants and computed values. They are not rows in the
  value → source table; the lesson prose is.
- The young chat does not have `strontia-lessons.json` in its documents (the handoff said "same
  documents"). It therefore quoted the deep-water oxygen numbers from FINDINGS rather than the
  lesson's top-3 m numbers.
- The floating "Ask a question" button can sit over the bottom-right of the card text while
  scrolling (the same behaviour as the map).

## Questions for the user

1. Should the young chat also get `strontia-lessons.json` (or the current lesson's reveal text)
   so its numbers match the lesson on screen?
2. Keep the young answer length target at about 120 words, or tighten the instruction? The one
   test ran 132 words.
3. Add the conductivity-correction story (0.98 → 0.00) as a second bonus step?
4. The praise list is "Good job!", "Nice thinking!", "You got it!", "Great reasoning!",
   "Spot on!". Any to add or drop?

## Round 2 (2026-09-25): changes the user approved

Nothing is committed. Everything stayed inside `teams/team-tbd/`, and `git status` still shows
only `?? teams/` and `?? __pycache__/`. The user's server on port 8765 was left running. I tested
on port 8767 and stopped that server afterwards. Scripts and screenshots are in
`scratchpad/round2/` (`r2_popout.py`, `r2_map.py`, `r2_chat.py`, `r2-*.png`, `v-*.png`).

### Changes

1. **The young chat has the lesson text.** At startup, `chat_server.py` reads
   `map/strontia-lessons.json` and builds `lessons_digest()`. For each lesson it gives the title,
   a one-line list of the visuals (no data arrays), Look, Question, the choices with
   `[correct]` marked, Reveal, and Why plus Comparison. The digest is added to the **young** prompt
   only, together with this instruction: "When the viewer is on a lesson, use the numbers shown in
   that lesson … and describe only the pictures and charts that lesson shows." Sizes: the default
   prompt is 43,623 bytes, unchanged from before. The young prompt is 59,946 bytes (the digest is
   about 15.7 KB). The page was already sending the lesson number and title in `context`. For bonus
   lessons it now says "bonus lesson 2 of 2" and the title (it used to say "the bonus lesson").
2. **Lesson 3's "% full" chart has a fixed 50 to 100 % y axis.** The lesson has two new fields,
   `y: [50, 100]` and `y_suffix: "%"`. `drawLineChart` in `strontia-core.js` uses a fixed range when
   `y` is given; with no `y` it auto-scales as before, so the map is unaffected. The ticks read 50%
   to 100% in steps of 10, and the title adds "(axis fixed from 50% to 100%)". The script asserts
   that every daily value falls inside that range. Screenshots: `r2-{desk,phone}-L3-pct-chart.png`.
3. **Lesson 6 timing is written for kids.** The text now reads "The river was muddiest in the
   middle of the night on Aug 15 … the muddiest spot was 23.1 NTU at 13 m deep, around midday on
   Aug 16, about a day and a half after the river's peak." It is built by two new helpers,
   `Numbers.part_of_day` (from the timestamp's hour) and `Numbers.days` (hours rounded to half
   days, from `hours_gage_peak_to_reservoir_peak` = 34.4 h). Both are logged in the value → source
   table.
4. **A second bonus lesson: "The sensor that forgot about temperature"** (id `tempcorr`, last in
   the list). Its visuals are a new `profile` chart type (`drawProfileChart` in `strontia-core.js`:
   value across, depth down with the surface at the top, one x axis, hover readout by depth). There
   are two side by side, stacked on phones: July temperature by depth, and July conductivity by depth
   (raw in orange, corrected to 25 °C in blue, and the river gage's July median as a dashed line).
   The question is "The raw reading (orange) was higher near the warm surface … Why?" with the
   choices "more minerals", "sensor broken" and **"Warm water lets electricity pass more easily"**
   (answer C). The Why box is labelled general science and contains no digits. All 20 numbers are
   computed from `sonde_clean.csv` (full casts: `temp_c`, `cond_us_cm`, `spcond_us_cm`) and
   `USGS_South_Platte.csv` (`Specific_Cond_Mean`):
   - median within-cast correlation: raw vs temperature **0.98**, corrected **0.00** (357 full casts).
     This matches `analysis/QC.md`.
   - July, top 3 m against ≥40 m: 18.4 against 14.6 °C. Raw 280 against 262 µS/cm. Corrected 324
     against 326.
   - June: lake corrected **313** against gage **315** (median of daily means), raw 247. Aug 1 to 12,
     before the storm: **312** against **307**, raw 256.
   - The script asserts the premises: raw is higher at the top, corrected is nearly flat, raw sits
     far below the gage, corrected is within 10 µS/cm of it, and the correlations are as above.
   The page's kicker reads "Bonus lesson 1 of 2" or "2 of 2", the lesson list and select use ★,
   progress counts "x of 11", and one kid starter question was added ("Why does warm water let
   electricity through more easily?").
5. README: the lesson list now names the two bonus lessons, and it says the young prompt has the
   lesson digest while the map's prompt is unchanged.

`strontia-lessons.json` now has 11 lessons and 145 numbers, md5 `12c37f82…`. Two runs of
`build_lessons.py` produced byte-identical JSON and identical stdout.

### Evidence

- **`r2_popout.py`**: the verifier's suite extended to 11 lessons, headless Chrome at 1400 px and
  390 px. **380 checks, 0 failures.** Every lesson loads and paints, and has 2 or 3 choices. The right
  and wrong paths alternate. The new bonus was tested both ways (the wrong path shows "Not quite" and
  the answer, the right path shows praise), and it is last ("Finished! Back to lesson 1"). The
  profile-chart hover readout lists raw, corrected and gage. Lesson 3 has the kicker "Lesson 3 of 9"
  and the axis label. Lesson 6's text contains the new phrase and no "12:06" or "hours". Progress
  reaches 11 of 11 ✓ and persists after a reload. Reset needs the confirm tap, then shows 0 of 11
  and still does after a reload. With storage throwing, the page works. No horizontal scroll. The
  Explore crosshair is linked on every panel. No console errors at either width.
- **`r2_map.py`**: the map against the pre-change copy (served temporarily and then deleted), at
  both widths. 140 checks, all identical. The only 2 "failures" are the same test-strictness item
  the verifier found: the popup URL is `strontia.html#lessons`. No console errors.
- **Chat, 3 real calls on port 8767.** The first call's answer was lost because my test script
  waited on the wrong condition (the greeting also counts as a bot message). I fixed the wait and
  reran both calls.
  - Pop-out, lesson 3, wrong answer picked, "What happened to the oxygen near the top?". The request
    had `audience: "young"`, and the context named "lesson 3 of 9, 'Warm water holds less oxygen'".
    The answer quoted the lesson's own numbers: top 3 m 9.9 → 18.4 °C, 9.3 → 7.6 mg/L, "% full"
    about 82% → 81%. It referred to the page's three charts correctly and used the soda comparison.
    It was 140 words; the length target was left as it is, as the user asked
    (`r2-chat-young-L3.png`).
  - Map, "Why does the storm's muddy water show up as a layer in the middle?". The request keys
    were `context` and `messages`, with **no `audience`**. The usual adult-level answer came back,
    with the measured and interpreted parts kept apart (`r2-chat-map.png`).

### Uncertain / for the user

- **The gage comparison numbers differ from the ones in the request.** The request mentioned
  "August about 312–314 vs gage 309; June about 302 vs 302". I could not reproduce those as monthly
  values. They look like single days: Aug 11 was lake 312.7 against gage 309, and Jun 4 was 302.25
  against 302. The lesson uses windows instead: the June median (313 against 315) and the median for
  Aug 1 to 12, before the storm (312 against 307). The lake and the gage do not match day by day. For
  example, in late May the snowmelt dip reaches the gage (276) but not the lake (about 312), because
  a reservoir mixes months of inflow. So the text says "agrees with the river", not "matches".
- **The chart shows July's median profile, not one sweep.** The rule I first used to pick "one
  representative July cast" (the cast whose top-minus-bottom temperature difference was closest to
  the month's median) picked the Jul 19 18:06 cast. That cast sits just before the Jul 20 service
  event, and its corrected line is 12 µS/cm off vertical, so it isn't typical. The month's median
  at each metre is representative by construction, and the Look text says so.
- The river gage line in the chart uses July (317), while the text compares June and early August,
  as requested. A reader could ask why the chart and the text use different months.
- The correct-answer positions are now A, A, B, A, C, B, B, A, B, B, C (not shuffled, as agreed).


## Round 3 (2026-09-25): question quality and connecting the ideas

Nothing is committed. Everything stayed inside `teams/team-tbd/`; `git status` still shows only
`?? teams/` and `?? __pycache__/`. I tested on port 8767 and stopped it afterwards; the server on
8765 was not touched (the main session restarts it). Scripts and screenshots are in
`scratchpad/round3/` (`r3_popout.py`, `r3_map.py`, `r3_chat.py`, `r3-*.png`). The Round 2
versions of `build_lessons.py`, `strontia.html`, `strontia-lessons.json` and `chat_server.py` are
backed up in `scratchpad/` (`*.r2.*`).

### What changed

1. **Opening screen, "Start here".** It comes before lesson 1 and has no question. A four-step
   chain (river → Strontia Springs Reservoir → Foothills treatment plant → Denver's taps) is drawn
   as HTML with small inline SVG icons: a row at 1400 px and a column with ↓ arrows at 390 px.
   The reservoir step is marked "The water scan is here". Below it are Denver Water's sentence,
   quoted word for word from `strontia-brief/places.json` ("Eighty percent of Denver Water's supply
   passes through Strontia Springs Reservoir."), what the sonde is, why layers matter, and what
   they will do and roughly how long. It shows on a first visit (nothing saved, or storage
   blocked), from **Start here** at the top of the list or select, from Back on lesson 1, after
   Reset progress, and after the last lesson. It is not a lesson and is not counted.
2. **Harder questions.** Every joke or obviously wrong choice is gone. Each wrong choice is now a
   misconception a 14-year-old might actually hold (see the table), and each one has a
   `why_not` explanation. Picking it shows "Why not "…"?" plus the reason, above the answer and
   the data. Questions that could be answered just by reading the colours are now "why" or
   prediction questions:
   - L1: what one stripe shows
   - L2: why the warm layer doesn't mix down
   - L3: why "% full" stayed flat
   - L5: why the extra deep oxygen is a clue
   - L6: why the middle, with the temperature clue in the question
   - L7: what explains the layer both sinking and fading

   Correct-answer positions are unchanged: A, A, B, A, C, B, B, A, B, then ★B, ★C. The new
   lesson's three questions use C, A, B.
3. **Connect the dots.** After the Why box, every lesson has a "Connect the dots" box. It holds
   one or two sentences linking back to earlier lessons ("Lesson 2: the warm top sits like a lid.
   Lesson 3: …"), and a chain row of the core lessons' short names with the current one
   highlighted. Wrong-choice reasons also cite lessons ("It's the other way round (lesson 3) …").
4. **Why you'd care.** Every lesson has a green "Why you'd care" box (operators need to know which
   depth the muddy water is at; TOC makes treatment harder; the intake depth is the missing clue;
   and so on). There are no tap-water safety claims. The one line of general knowledge in it
   (lesson 4: iron and manganese) is labelled "(general science)".
5. **Put it all together** (lesson 10 of 10, marked "what if"): a cold, muddy spring storm, made
   up and labelled as such ("nothing here was measured"). It has three chained questions: where
   the water goes, what the sonde's pictures would show, and whether a near-surface intake would
   notice. The page now supports several questions in one lesson (steps Look → Question 1 → 2 →
   3 → Why; each needs an answer before Next; earlier questions stay on the card). The picture is
   the real August storm, labelled "For comparison". Its only numbers are real ones (Apr 7, 5.3 °C),
   and the script asserts that its question text has no digits apart from lesson references.
6. **Bonus lessons are optional.** The list has a "Bonus: if you have time (about 6 min)" header
   (an optgroup on phones), and the card kicker says "Bonus lesson 1 of 2 · optional, if you have
   time". Progress reads "x of 10 finished · bonus: y of 2", where core means lessons 1 to 9 plus
   Put it all together. After Put it all together, Next reads "Bonus lessons (optional) →" with a
   "That's the core finished" note. The last bonus reads "Finished! Back to the start".
7. **Chat.** `lessons_digest()` now includes the opening screen, every question (so all three
   Put-it-all-together questions), each wrong choice's "why not", Connect the dots and Why you'd
   care. The young prompt adds: point back to the lesson an idea came from, and the what-if gets
   no measured numbers of its own. The young prompt is now 72.5 KB (digest 28 KB); the default prompt
   is unchanged. The page's chat context names the opening screen, or for the what-if, the
   current question ("question 1 of 3"). Two kid starters were added: "What would happen if a
   storm came in colder than all the lake water?" and "How does water get from the river to my
   tap?".
8. **Reading-time estimate**, printed by `build_lessons.py`: words / 150 per minute, plus 20 s per
   question. Per question it counts the prompt, the choices, the reveal and the average "why not".
   The intro shows the computed number.
9. The script also asserts: every question has 2 or 3 choices with exactly one correct and a
   "why not" on each wrong one; no digits in Why or Comparison text; and the new premises
   ("% full" moved under 3 points; the deep water is less full than the top; flow and deep oxygen
   rose; the river was cooler than the surface and matched the lake above the mud's depth; the
   layer sank and faded; the gage conductance fell).
10. README: the lessons paragraph describes Start here, Put it all together, the optional bonus
    lessons, and the new boxes.

**About length:** partway through, I tightened all the text to reach the 15-minute target (about
19 min). The user then said it read too terse and asked for more words, so the lessons are back
to full sentences. This is the version below.

### Every question (correct answer in bold with ✓)

| # | Lesson | Question | A | B | C |
|---|---|---|---|---|---|
| 1 | How to read the water scan | Pick one thin up-and-down stripe of colour in the picture. What does it show? | **✓ One sweep of the sonde: the temperature at every depth, at one moment** | The temperature across the lake, from one shore to the other | One depth, followed through the whole season |
| 2 | Warm water floats | The warm (light) water stays in a band at the top, month after month. Why doesn't it mix down and even out the lake? | **✓ Warm water is lighter than cold water, so it floats on top** | The sun only heats the top, and heat can't travel down through water | Cold springs at the bottom keep the deep water cold |
| 3 | Warm water holds less oxygen | From April to July the top water warmed up and its oxygen (mg/L) went down. But the "% full" chart hardly moved. What is the best explanation? | Fish and other living things used up the oxygen | **✓ Warm water can't hold as much oxygen, and the water stayed about as full as it could be** | Calm summer water mixes in less air, so less oxygen got in |
| 4 | The bottom is cut off from the air | The deep water was less full of oxygen (about 72%) than the top (about 82%). Why? | **✓ It is far from the air, and the layers stop it mixing with the top** | Cold water holds less oxygen, so the cold deep water is less full | The pressure deep down squeezes oxygen out of the water |
| 5 | Cold river water sinks | In early August the river got colder than any of the lake water (on Aug 9 it was 13.1 °C; the lake's coldest was 14.5 °C). Then the deepest water got colder and gained oxygen. Why is the extra oxygen a clue about where the river water went? | The deep water got colder, so it could hold more oxygen | Algae near the bottom made more oxygen | **✓ The bottom is cut off from the air, so new oxygen most likely arrived with new water: the cold river** |
| 6 | Follow the storm's mud | The storm's mud showed up as a layer in the middle, not at the top or the bottom. Clue: the river water was about 16.0 °C, and before the storm the lake was that warm at about 5 m deep. Why the middle? | Mud is light, so the muddy water floated up off the bottom | **✓ The river was cooler than the top but warmer than the deep water, so it slid in where the lake matched its weight** | The river was colder than all the lake, but ran out of time before reaching the bottom |
| 7 | The muddy layer sinks and fades | After the peak, the white dots go deeper each day and the layer gets paler. What best explains both? | New muddy river water kept arriving and pushed the layer down | **✓ Mud is heavier than water, so it slowly settles, and the layer loses mud as it sinks** | The mud dissolved into the water, like sugar in tea |
| 8 | Mud and rainwater travel together | The muddy layer had fewer dissolved minerals than the same depths before the storm. What is the best explanation? | **✓ It was fresh rainwater, which has few minerals, arriving with the mud** | The storm water was a bit warmer, and warm water holds fewer minerals | The minerals sank to the bottom with the mud |
| 9 | What reaches the water plant | The plant's organic carbon jumped on Aug 16. Can we be sure the storm caused it? | Yes: it jumped the day after the river's muddiest moment | **✓ Probably, but we need more information** | No: the mud stayed in the middle of the lake, so it couldn't reach the plant |
| 10 | Put it all together: a cold, muddy spring storm (Q1) | Where would this storm's muddy water go? | Into the middle, like the August storm | Through the whole lake, because a storm stirs everything up | **✓ Down along the bottom** |
| 10 | Put it all together: a cold, muddy spring storm (Q2) | Over the next days, what would the sonde's pictures most likely show? | **✓ A muddy band near the bottom, a fairly clear top, and a little more oxygen deep down** | Muddy water at every depth at the same moment | A muddy band near the bottom, with less oxygen, because the layers act like a lid |
| 10 | Put it all together: a cold, muddy spring storm (Q3) | Suppose the plant's intake were near the surface. Would the plant notice this storm quickly? | Yes, just as fast: the plant gets the same water from the whole lake | **✓ Probably not much at first, because the storm water slid in underneath the intake** | Never: the muddy water can never reach the plant |
| ★ | Data detective | On Jun 16 every depth changed at the same moment. What is most likely? | The layers flipped over and the whole lake mixed | **✓ Someone cleaned or adjusted the sensor** | Storm water rushed in and changed the water |
| ★ | The sensor that forgot about temperature | The raw reading (orange) was higher near the warm surface than in the cold deep water. Why? | More minerals flowed in near the surface | Warm water dissolves more minerals, like sugar in hot tea | **✓ Warm water lets electricity pass more easily** |


### Reading time (from `build_lessons.py` stdout)

```
Reading time (words / 150 per minute + 20 s per question; charts not counted)
part        words questions  seconds
opening       166         0       66
read          236         1      115
floats        262         1      125
oxygen        290         1      136
bottom        287         1      135
sinks         318         1      147
mud           376         1      170
fades         288         1      135
minerals      270         1      128
plant         342         1      157
together      532         3      273
detective *    280         1      132
tempcorr *    466         1      207
opening + core + put it together: 26.4 min (24.3 min for a reader who gets every answer right);  bonus (*): 5.6 min
```

The core (opening + 9 lessons + Put it all together) is about **26 min** at 150 words a minute:
24 min for a reader who never needs a "why not", and about 21 min at 200 words a minute. That is
well over the 15-minute aim, because the user preferred fuller text. The terse version measured
about 19 min. The opening screen is about 1 min at 150 wpm (the four boxes are meant to be
skimmed). The bonus lessons take about 6 min.

### Evidence

- **`build_lessons.py`**: two runs gave byte-identical JSON (md5 `0cf2ee3e…`) and identical
  stdout. The file has 12 lessons, 154 numbers, and every one appears in the value → source table.
- **`r3_popout.py`** (headless Chrome, 1400 × 900 and 390 × 844): **1317 checks, 0 failures.**
  - Opening screen: shown on first visit, with the quote, sonde, layers and minutes. It is reached
    from Start here in the list or select, from Back on lesson 1's Look, after Reset (and after a
    reload following Reset), and after the last lesson.
  - Every lesson: loads, its canvases paint, and it has the right number of steps. Next is blocked
    until the question is answered.
  - Every wrong choice of every question (all 12 lessons, including each Put-it-all-together
    question): "Not quite", no praise, the wrong pick marked, "Why not "…"?" with that choice's own
    text, and the right answer shown.
  - Every right path: praise, and no "why not".
  - Why box labelled; Connect the dots and Why you'd care shown; the chain row highlights the
    right lesson.
  - Put it all together: three questions in sequence, each stays on the card, and Next leads to
    the optional bonus lessons.
  - Counts: "0 of 10 finished · bonus: 0 of 2" → "10 of 10 · bonus: 2 of 2". Progress persists
    across a reload and reopens at the saved lesson, not the intro.
  - Reset asks to confirm, then clears.
  - With storage throwing: the intro shows, a tick counts for the visit, Reset works, no errors.
  - Chat opens on the intro with nothing sent. The chat context is right on the intro and on the
    what-if.
  - Explore: linked crosshair on every panel.
  - No horizontal scroll anywhere. No console errors.

  Screenshots: `r3-{desk,phone}-intro.png`, `-after-reset.png`, `-L1-q1-{right0,wrong0,wrong1}.png`,
  `-L6-…`, `-L10-q{1,2,3}-….png`, `-L{1,4,10,11}-why.png`, and the bonus lessons.
- **Map regression (`r3_map.py`)**: the map page, `team-chat.js`/`.css` and `strontia-core.js`
  were not edited this round. At both widths: the Strontia panel, both views × 5 parameter
  hover readouts, chat (5 starters, nothing sent, no `audience`), the pop-out button opening
  `strontia.html` in a popup, and no console errors.
- **Chat, 1 real call** (young, 390 px, Put it all together, question 1 answered wrong with "Into
  the middle"): "Why wouldn't this storm go to the middle like the August one?" The request had
  `audience: "young"` and the context named the what-if and question 1 of 3. The answer was 110
  words. It compared the August river (16.0 °C, "lesson 6") with the what-if river, pointed to
  lesson 5, invented no numbers for the what-if, and ended with a question back to the student
  (`r3-chat-young-PIAT.png`).

### Open questions for the user

1. **Length versus the 15-minute aim.** At full sentences the estimate is about 26 min. Options
   that keep every idea: drop the "Comparison" lines (about 1 min), or shorten the Look texts
   where the chart titles already say the same (about 1 min). Or accept about 25 min and call it
   "two sittings". Should the intro keep showing the computed "about 26 minutes", or say
   something softer?
2. **Put it all together, question 2** predicts "a little more oxygen deep down", based on lesson
   5's cold underflow. It is labelled a prediction. Mud carrying organic matter could also use
   oxygen up. Keep it, or drop the oxygen part and ask only about where the mud shows?
3. **Question 3's "never" feedback** mentions autumn mixing (turnover) as general science. That
   is not otherwise taught in the lessons. OK, or reword it?
4. Answers are still not saved across a reload (only ticks are), so a returning student sees the
   questions fresh. That matches Round 1 behaviour.
