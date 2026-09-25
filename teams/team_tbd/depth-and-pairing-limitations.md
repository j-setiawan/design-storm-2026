# What the Strontia profile can and cannot tell us about Foothills

## The missing link: intake depth

The Strontia sonde file contains water-quality readings at many depths in the reservoir. Foothills Influent contains laboratory measurements of TOC and alkalinity, but the available files do not identify the depth or depths from which the water reaching the Foothills intake was withdrawn on each date.

Without intake elevation/depth and withdrawal-operation data, we cannot identify which sonde readings represent the water that later reached Foothills. A profile-wide input vector combines readings from across the water column, including depths that may not have contributed to the intake flow. It is useful for exploratory association, but it does not establish a depth-specific source for the plant sample.

## Date matching is an assumption

The current prototype pairs a Strontia profile on date D with Foothills lab measurements on date D plus an optional day lag. A same-date or fixed-lag match is a practical modeling assumption; it does not prove that the matched reservoir water became the matched plant influent sample. Reservoir mixing, storage, withdrawal depth, transport, and sampling time can all affect that relationship.

The `--date-lag-days` setting lets us test fixed calendar offsets, but it cannot resolve an unknown or changing intake depth or a variable water travel/mixing time.

## The paired dataset is small

The Strontia deployment in these files covers only a few months, and only dates present in both the sonde and Foothills records can be paired. That leaves a small number of examples for fitting models, especially after reserving later dates for an honest chronological holdout. With many profile dimensions relative to the number of paired dates, model scores can change substantially with the chosen period and may not generalize to other seasons or reservoir conditions.

More matched sonde profiles and Foothills lab samples across multiple seasons and hydrologic conditions would help. More data would provide more examples for training and chronological validation, improve coverage of uncommon TOC/alkalinity treatment classes, and make it easier to assess whether a model's apparent skill persists over time. Additional rows alone do not resolve the unknown intake depth or date-to-date water movement; intake and operations information would still be valuable.

## How to interpret current model results

- Treat the full-profile models as exploratory predictors or association analyses.
- Do not interpret a useful prediction score as evidence that every depth contributes equally, or that a particular depth supplied the Foothills water.
- Performance applies only to the date-paired rows and the chronological holdout that was evaluated.
- Because the paired sample is small, treat reported scores as uncertain and specific to the tested period; more matched dates across seasons would strengthen evaluation.
- The sonde and Foothills datasets are provisional and subject to the terms in [`data/TERMS.md`](../../data/TERMS.md). Keep those terms with derived outputs.

## Data that would strengthen the link

To connect profile readings to the water actually sampled at Foothills, obtain, if available:

1. The Strontia withdrawal/intake elevation and any changes in intake configuration.
2. Daily or sub-daily withdrawal depth/port operations and reservoir release records.
3. The collection timestamps for Foothills lab samples, rather than date alone.
4. A hydraulic travel-time or water-age estimate from Strontia withdrawal to Foothills sampling, ideally varying with operations and flow.
5. Corresponding reservoir profiles and plant samples over a longer period for validation.

With these, inputs could be aligned to the active intake layer and plausible travel-time window. Until then, comparing full-profile, depth-band, and profile-summary representations is a useful sensitivity analysis, but it cannot identify the actual source depth.
