# Strontia Springs Reservoir, a summer in section

An exhibit-style page for a general audience: the reservoir drawn in cross-section,
blue water shaded by temperature, chlorophyll, turbidity, dissolved oxygen and
conductivity as dots, the river pouring in, the level following DWR storage, snow
on the mountains following the Hoosier Pass snowpack, and a scrubber through the
summer of 2026.

Open `index.html`. It is self-contained; no server, no network.

## What is here

| File | What it is |
|---|---|
| `index.html` | The page. Generated; do not edit by hand. |
| `template.html` | The page's HTML, CSS and JavaScript, with a marker where the data is inlined. |
| `build.py` | Builds `index.html` from the template, the sonde data and the storage record. |
| `sonde_data.py` | Cleans the sonde export and the upstream daily series. Also imported by `strontia-section/build.py` at the repository root. |

## What it reads

The build finds the repository root by walking up until it sees `data/`, so this
folder can sit anywhere inside the repository. From the root it reads:

- `data/Strontia 0407_0819.xlsx`: the profiling sonde export (Denver Water).
- `data/USGS_South_Platte.csv`, `data/SouthPlatteTelemetry.csv`, `data/USC00058022.csv`, `data/HoosierPass.csv`, `data/FoothillsInfluent.csv`: the upstream and plant series.
- `water-system-3d/storage-history.json`: daily Strontia storage from the Colorado DWR, for the water level.

## Rebuild

```
uv run --with pandas --with openpyxl teams/team-tbd/strontia-summer/build.py
```

Denver Water's data terms in `data/TERMS.md` travel with the page; they are
reproduced in its grown-ups section.
