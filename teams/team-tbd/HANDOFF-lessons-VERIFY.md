# Verifier report: Strontia pop-out page with lessons

Written 2026-09-25 by the verifier for `HANDOFF-lessons.md` §8. The builder's report was not taken
on trust: every item below was re-run or recomputed. Nothing is committed or pushed.

Verifier scripts and screenshots are in the session scratchpad, under
`/private/tmp/claude-502/-Users-msmith-Downloads-ddd-temp-design-storm-2026/eb71962f-0b72-463f-9690-bbeac2adbedb/scratchpad/verify/`
(`recompute.py`, `v_popout.py`, `v_map.py`, `v_chat.py`, `v-*.png`, `m-*.png`).

## Summary

| # | Item | Result |
|---|---|---|
| 1 | Regenerate from a clean `analysis/out/`, reproducible, changes only under `teams/` | **Pass** |
| 2 | Every lesson number recomputed independently | **Pass**, with 1 wording fix (lesson 7) and 2 notes |
| 3 | Content: "Why" labelled, nothing overstated, reading level, no tap-water claims | **Pass**, after 2 small wording fixes (lessons 6 and 8) |
| 4 | Questions: 2 or 3 choices, one correct, answer always shown, praise only when right | **Pass** |
| 5 | Pop-out UI at 1400 and 390 px, storage working and throwing, Explore, chat, Reset progress | **Pass** (336 checks, 0 failures) |
| 6 | Map page regression | **Pass** (140 checks; the 2 "failures" were my test being too strict, see below) |
| 7 | This report | Done |

## 1. Regenerate: pass

- Moved `analysis/out/` to `scratchpad/verify/out-prev/` and ran the README order from an empty
  folder: `clean_sonde → grid_sonde → storm_trace → autoresearch/prepare → fill_best →
  build_profile_json → build_lessons` (about 16 s).
- `map/strontia-lessons.json` md5 `e93211fd…` and `map/strontia-profile.json` md5 `961cee7b…`,
  byte-identical to the builder's files. A second `build_lessons.py` run gave the same bytes, and
  its stdout (the value → source table, 125 numbers) was identical too.
- `sonde_clean.csv`, `casts.csv`, `storm_casts.csv` and `storm_numbers.json` are byte-identical to
  the previous `analysis/out/`.
- `git status`: only `?? teams/` and the existing `?? __pycache__/`. `git diff HEAD` is empty, so
  no tracked file changed (the whole of `teams/` is untracked, so git can't show finer detail
  inside it).
- After my text fixes (below), `strontia-lessons.json` is now md5 `94b7e194…`. It was generated
  twice with the same bytes both times.

## 2. Numbers: pass (all 125 trace to the data)

`recompute.py` reads `sonde_clean.csv` (full casts), `casts.csv`, `storm_casts.csv`, the raw USGS
15-minute JSON in `strontia-brief/series/`, and `data/USGS_South_Platte.csv`,
`SouthPlatteFlow.csv` and `FoothillsInfluent.csv`. It doesn't import or copy any of
`build_lessons.py`. It then checks that each value appears in the lesson text. It also compares
every line-chart series against my own daily medians: the largest difference is 0.1, which is
rounding.

All of these match:

- **L1:** depths to 44 m, Apr 7 to Aug 19, key 5.4 to 19.1 °C (1st and 99th percentiles of the
  season grid), a sweep about every 6 h.
- **L2:** July median 18.4 °C in the top 3 m against 14.6 °C at ≥40 m; biggest daily gap 7.6 °C on
  May 15; 5.3 °C on Apr 7. The smallest daily gap is 2.45 °C (Aug 5), so "layered until the data
  ends" holds.
- **L3:** in the top 3 m, April → July: 9.9 → 18.4 °C, 9.3 → 7.6 mg/L, 82 → 81 %.
- **L4:** deep % saturation by month 70, 70, 73, 71, 75; whole-season medians 72 % (deep) and 82 %
  (top); lowest deep daily median 6.5 mg/L on Jul 18; lowest single reading 5.9 mg/L.
- **L5:** river coldest on Aug 9 at 13.1 °C against the lake's coldest 1 m daily median of 14.5 °C
  (the lake's coldest single reading that day was 14.4, so the premise still holds); deep water
  15.7 → 14.3 °C (Aug 4 → 11); oxygen 6.9 → 8.1 mg/L (Aug 9); river 15.1 → 13.1 °C; flow 469 →
  582 cfs.
- **L6:** gage peak 329 FNU at 1:45 a.m. on Aug 15; lake peak 23.1 NTU at 13 m on Aug 16; layer
  about 8 to 18 m (medians 7.5 and 17.5 over the 16 layer casts); river 16.0 °C; pre-storm surface
  17.1 °C; the lake matched the river's temperature at 5 m.
- **L7:** the daily peak NTU values 6.0, 19.6, 23.1, 17.5, 10.4, 8.0; last cast 6:06 a.m. on Aug
  19, layer 13 to 22 m.
- **L8:** the layer read 6 to 12 µS/cm low before the Aug 18 service. At the gage, 296.5 → 280
  µS/cm: the median before onset, with the 13:00 glitch sample dropped, then the minimum.
- **L9:** TOC 2.0 on Aug 10 to 15, then 2.5 on Aug 16; 0.7 % of 448 June to August day-to-day
  changes, 2022 to 2026. All 448 are true consecutive-day steps.
- **Bonus:** 7 service dates; chlorophyll segment medians 0.88 → −0.19 µg/L on Jun 16.

What my first pass flagged, and why:

- **Lesson 7, a pairing problem (fixed).** The text said "Muddiest depth and how muddy it was, day
  by day: Aug 15: 12 m, 19.6 NTU …". The depth there is the *median* of that day's per-cast peak
  depths, but the NTU is the day's *maximum*, so the two are not the same reading. The 19.6 NTU
  reading was at 15 m, not 12 m. Both numbers are correct, and the "sinks deeper" story holds
  either way (max-based depths are 7, 15, 13, 15, 20, 22 m). I only reworded the labels (see
  Fixes).
- **Lesson 6, "12:06 p.m. … about 34 hours later" (note only).** 12:06 is when the cast started.
  The 13 m reading in that cast was taken at about 12:48, which makes it 35 h from the gage peak.
  This comes from `storm_numbers.json` / FINDINGS and is fine as "about"; I didn't change it.
- The other flags were my own string formats ("about every 6 hours") or my first onset estimate
  including the 13:00 glitch sample. With it dropped I get 296.5, which matches.

Highlight boxes: I checked each against the data. The July × top-3 m box, the ≥40 m × season box,
the storm-layer box (7.5 to 17.5 m, the layer casts to Aug 19 06:06), the after-peak box (3 to
24 m, the actual range of layer tops and bottoms after the peak) and the Jun 16 ± 2 days box all
match.

## 3. Content: pass (after small fixes)

- Every "Why" box has the label "Why it happens · general science, not from this data". No Why
  or Comparison text contains a digit. Every analogy starts with "Comparison:".
- Lesson 6's Why had a data finding in it ("The storm water was a little cooler than the surface
  water, so it sank"). I rewrote it as a general statement. The data version is still in the
  explanation above it.
- Lesson 8's question said the layer had fewer minerals "than the water around it". The number
  actually compares it with *the same depths before the storm*, so I changed the wording to say
  that.
- Nothing is overstated. L9 keeps "Probably, but we need more information", and the intake depth
  is named as the missing clue. L5 says "the team's best explanation, not something the data
  proves". L7's Why notes that settling can't be told apart from outflow.
- "Readings are provisional" appears once, in the footer, next to the profile JSON's `terms` text
  and a link to `DATA-TERMS.md`.
- There are no tap-water or safety claims (I searched the text for "tap", "drink" and "safe").
- Reading level fits ages 13 to 16. Sentences in the explanations average 12 to 20 words, and
  science words are explained where they appear (stratified, decomposers, interflow, density, FNU
  and NTU, specific conductance).

## 4. Questions: pass

All 10 lessons have 3 choices with exactly one correct. On both desktop and phone, answering right
showed one of the five praise lines. Answering wrong showed "Not quite, here is what happened.",
with no praise and the wrong pick marked "✗ your pick". Both paths showed "The answer: …" and the
✓ on the correct choice, and after answering the choices lock and Next unlocks. The correct answer
sits at A, A, B, A, C, B, B, A, B, B, and choices are not shuffled. Four of the ten answers are
"A", which a student could spot as a pattern; see open question 6.

## 5. Pop-out UI: pass (`v_popout.py`, 336 checks, 0 failures)

Tested at 1400 × 900 and 390 × 844 in headless Chrome on port 8767.

- **Layout.** Title "Strontia Springs, by depth". A 10-item list on desktop and a `<select>` on
  phone. No horizontal scroll on any lesson, on the Reset-confirm state, or in either Explore view.
- **Every lesson.** Loads, and every canvas draws. Look → Question (Next blocked until an answer)
  → reveal → Why. Hover readouts work on both a heatmap (L2) and a line chart (L3).
- **Back/Next.** Back from lesson 2's Look lands on lesson 1's Why, and Back is disabled at lesson
  1's Look.
- **Progress with storage working.** After a reload, 10 of 10 ✓ (list ticks on desktop, "✓" in
  every option on phone), and the page reopens at the last lesson. Only the ticks and the place
  are saved: after a reload the question has to be answered again. That seems fine.
- **Progress with storage throwing.** I ran an init script that makes `localStorage` throw. The
  page loads, a ✓ counts for the visit, Reset works, and there are no console errors.
- **Reset progress** (the builder's mid-build addition). The first tap changes the link to "Clear
  all ticks and answers? Tap again to confirm" and does not reset. The second tap gives 0 of 10
  and goes back to lesson 1, and a reload still shows 0 of 10. The confirm state times out back to
  "Reset progress" after 5 s. The link stays inside the viewport at 390 px
  (`v-phone-reset-confirm.png`). It works at both widths, and with storage blocked.
- **Explore.** Five heatmaps, with the gage and TOC strips in the storm view only. Hovering the %
  saturation panel draws the crosshair on **every** panel at the same x: 661 px on all 7 overlays
  on desktop storm, 659 on desktop season, 197 and 196 on phone. The sticky readout lists all five
  values (`v-*-explore-*.png`).
- **Chat.** "Ask Claude about this" opens the chat with 5 starters and a greeting that names the
  lesson, and sends no POST.
- **Console.** No errors on either width.

## 6. Map page regression: pass (`v_map.py`)

I served the builder's pre-change copy (`scratchpad/map-before.html`, dated before the refactor)
next to the current page as a temporary `map/zz-verify-before.html`, and deleted it afterwards.
Then I drove both pages the same way at both widths.

- **Identical on both pages.** Panel widening; both views × all 5 parameter chips: the hover
  readout, title, `aria-pressed`, and canvas image size for each; gage and TOC strip pixels;
  findings text; the chat window and button position and text; the intro and fine print; the
  `chatContext()` string; the tour (stop 1 → Next → Back → Exit); and the storm replay (bar
  shows, slider max 120, it animates, it exits).
- **Chat.** It opens from "Ask Claude about this picture" with 5 starters and sends nothing. I
  stubbed the endpoint so no real call was made; the map's request body is
  `{messages, context}` with **no** `audience`.
- **Pop-out button.** It sits beside the ask button at both widths (`m-phone-actions.png`) and
  opens `strontia.html` in a popup named `strontia`. My test expected the URL to end in
  `strontia.html` and got `strontia.html#lessons`, because the page adds the mode hash itself.
  That is expected behaviour, not a regression.
- **Console.** No errors on either page (the DWR CORS error didn't appear this run).

## Chat, young audience (2 real calls)

Both calls were on the pop-out at 390 px.

- **Request.** It carried `"audience":"young"` and the lesson context: the lesson, step, question,
  correct answer, and the viewer's (wrong) answer.
- **Call 1, lesson 4: "Why is the deep water less full of oxygen than the top?"** A good answer
  for the age: short sentences, "stratified" explained, general science labelled, kind to the
  wrong pick. It was **134 words**.
- **Call 2, lesson 3: "How much did the oxygen in the top layer drop from April to July?"**
  **123 words.** It said *"I don't have a number for the top layer"* and gave the deep-water
  numbers from FINDINGS (9.4 → 7.1 mg/L). The lesson on screen shows 9.3 → 7.6 mg/L for the top
  3 m. It also told the student to "hover near the top on the picture", but lesson 3 has line
  charts, not a heatmap. This confirms the builder's issue (1).

## Fixes made (all in `analysis/build_lessons.py`; JSON regenerated, deterministic)

1. **Lesson 7, Look:** "The white dots mark the muddiest depth on each day" → "… mark the usual
   depth of the muddiest spot on each day".
2. **Lesson 7, explanation:** "Muddiest depth and how muddy it was, day by day:" → "Day by day,
   the usual depth of the muddiest spot, and the muddiest reading:". The numbers are unchanged.
3. **Lesson 8, question:** "… fewer dissolved minerals than the water around it" → "… than the
   same depths before the storm".
4. **Lesson 6, Why:** the storm-specific past tense ("The storm water was a little cooler … so it
   sank … it went a bit deeper") became general statements ("Inflow water that is a little cooler
   than the surface water sinks below it … muddy water goes a bit deeper still. Then it spreads
   …").

The four fixes change text only. The number count is still 125 and every recomputed value still
matches. The UI tests ran after fixes 1 to 3; fix 4 changes one sentence of prose that the page
shows exactly as written.

## Recommendations on the builder's four issues

1. **Give the young chat the lesson text? Yes.** Call 2 shows the problem clearly: it said it had
   no top-layer number while the lesson on screen shows one. It also pointed at a picture the
   lesson doesn't have. The cheapest reliable fix is to add a compact digest of
   `strontia-lessons.json` to the **young** system prompt only: for each lesson, the title, look,
   visual types, question, correct answer, explanation and Why, but not the chart arrays. That is
   roughly 10 to 12 KB. Also add one line: "When the lesson on screen shows a number, use that
   one." Putting the text in `context` instead would need the 1000-character limit raised. I
   didn't change this because the handoff said "same documents"; it needs the user's call.
2. **132 words against ~120: tighten slightly.** My two calls ran 134 and 123 words, so the model
   aims near the target and overshoots a little. If the user wants it nearer 120, change the
   instruction to "under 100 words" (models tend to overshoot a stated limit). Otherwise leave it:
   the answers read well. Low priority.
3. **Floating "Ask a question" button overlapping the card: minor. Suggest hiding it in Lessons
   mode, or making it icon-only on phones.** Measured at 390 px, the 143 × 44 px button covers the
   bottom-right of the card and heatmap while scrolling (`v-*-L*-look.png`,
   `v-phone-reset-confirm.png`). At 1400 px it overlaps the card's right edge by about 59 px when
   the card is behind it. The 110 px bottom padding means the end of the content can always be
   scrolled clear. Every lesson card already has "Ask Claude about this", so the floating button
   is redundant in Lessons mode. Either change is a few lines of CSS, but it is a design choice.
4. **Lesson 4, 72 % against 82 %: keep the computed values.** They are whole-season medians of the
   readings (71.94 and 81.7). The mean of the monthly medians gives the same rounding (71.7 and
   81.6). The handoff's "~70 vs ~81" was a loose cross-check that no computation reproduces
   exactly, and the monthly values in the lesson (70, 70, 73, 71, 75) match the handoff. Changing
   to 70/81 would break the "no hand-typed numbers" rule.

## Open questions for the user

1. Should the young chat get the lesson digest (recommendation 1)?
2. Should the young answer length be tightened to "under 100 words", or left as it is?
3. The floating chat button on the pop-out: hide it in Lessons mode, make it icon-only on phones,
   or leave it?
4. **Lesson 3's "% full" chart** has an auto-scaled y-axis of 78 to 84 %. That makes a flat line
   look wiggly, but the lesson's point is that it "hardly changed". Fix the axis at 0 to 100 %
   (or 50 to 100 %) for that chart? That is a small change in `build_lessons.py` (an axis range on
   the visual) plus `strontia-core.js`. I left it because it is a chart-design choice.
5. **Lesson 6 timing.** "12:06 p.m. … about 34 hours" uses the cast's start time. The 13 m reading
   itself was about 40 minutes later (about 35 h). Keep it (it matches FINDINGS), or say "around
   midday"?
6. **Answer positions** are fixed (A, A, B, A, C, B, B, A, B, B). Shuffle the choices per visit,
   or just rebalance them in the script?
7. From the builder's list: add the conductivity-correction story (0.98 → 0.00) to the bonus
   lesson, and should the praise list change?
