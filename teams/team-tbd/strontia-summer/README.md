# Strontia Springs Reservoir, a summer in section

An exhibit-style page for a general audience: the reservoir drawn in cross-section,
blue water shaded by temperature, chlorophyll, turbidity, dissolved oxygen and
conductivity as dots, the river pouring in, the level following DWR storage, snow
on the mountains following the Hoosier Pass snowpack, and a scrubber through the
summer of 2026, with a quiz under the scene.

Open `index.html`. It is self-contained; no server, no network.

A second tab, "Data pages", frames the team's two other pages: the Foothills TOC and
alkalinity prediction dashboard (`../map/prediction-dashboard.html`, data in
`../dashboard/`) and "Strontia Springs, by depth" (`../map/strontia.html`, the full
lesson set and the Explore heatmaps). The build inlines each with its data and scripts
so they also open without a server; the lessons page's chat still needs the team server.
After regenerating either page's data, rebuild this page to pick it up.

The quiz is the lesson set written for the depth pictures in `../map/strontia.html`
(`../analysis/build_lessons.py` writes `../map/strontia-lessons.json`), asked in front of
the scene: opening a question travels the scene to that lesson's day, shows only the dots
it is about, and draws a dashed band around the depths it points at. Questions, choices,
explanations and every number in them come from the lessons file. This folder's `build.py`
only chooses which lessons the scene can carry (nine of twelve; the three about reading
the heatmap itself stay on the lessons page), the day for each (computed from the same
data), the dots to show, and one "Look" sentence per question. Lesson numbers in the text
become lesson titles, since the quiz shows a subset in its own order. After an answer the
lesson's own charts appear under it, drawn by the lessons page's `../map/strontia-core.js`
(inlined into `index.html`) from the slices of `../map/strontia-profile.json` those charts
need, with the lesson's original "Look" sentence as the caption. Progress is kept in
the browser's local storage. The lessons page's chat is not here: it needs the team server.

## What is here

| File | What it is |
|---|---|
| `index.html` | The page. Generated; do not edit by hand. |
| `template.html` | The page's HTML, CSS and JavaScript, with a marker where the data is inlined. |
| `build.py` | Builds `index.html` from the template, the sonde data, the storage record and the lessons file. |
| `sonde_data.py` | Cleans the sonde export and the upstream daily series. Also imported by `strontia-section/build.py` at the repository root. |

## What it reads

The build finds the repository root by walking up until it sees `data/`, so this
folder can sit anywhere inside the repository. From the root it reads:

- `data/Strontia 0407_0819.xlsx`: the profiling sonde export (Denver Water).
- `data/USGS_South_Platte.csv`, `data/SouthPlatteTelemetry.csv`, `data/USC00058022.csv`, `data/HoosierPass.csv`, `data/FoothillsInfluent.csv`: the upstream and plant series.
- `water-system-3d/storage-history.json`: daily Strontia storage from the Colorado DWR, for the water level.
- `teams/team-tbd/map/strontia-lessons.json`, `strontia-profile.json` and `strontia-core.js`: the lessons, the depth data behind their charts, and the code that draws them, for the quiz.
- `teams/team-tbd/map/prediction-dashboard.html` with `teams/team-tbd/dashboard/foothills-prediction.json` and `dashboard-extra.json`, and `teams/team-tbd/map/strontia.html` with `team-chat.js` and `team-chat.css`: the two data pages in the second tab.

## Rebuild

```
uv run --with pandas --with openpyxl teams/team-tbd/strontia-summer/build.py
```

Denver Water's data terms in `data/TERMS.md` travel with the page; they are
reproduced in its grown-ups section.
