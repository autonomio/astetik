# Migration to Astetik 2.0

Version 2.0 replaces notebook-global presentation with explicit declarations, an immutable design manifest, and `EvidenceResult`. This page owns historical argument translation and behavior changes; current interfaces live in the linked references.

## New primary interface

Prefer `astetik.render(data, spec, manifest)` or `astetik.plot(data, kind, ...)` for new code. Specifications use conventional horizontal x and vertical y. Existing plot names and direct legacy plot-module imports route through the same core.

The environment and package boundaries are described in the [package page](../../astetik/README.md). Install this version from its source; the documentation does not claim that the modern version has already been published to a package index.

## Retained special argument conventions

| Historical entry | Retained interpretation |
| --- | --- |
| `line(data, x="response", y="time")` | Wrapper x names measurements and y names time; new `plot(..., "line", x="time", y="response")` uses conventional axes |
| `roc(y_pred, y_true)` | Preserves argument order while separating scores from truth labels |
| `world(..., area_col=..., value_col=...)` | Maps to source geography and values |
| `label_col` | Maps to `hue` |
| `x_label`, `y_label` | Map to display labels |
| `sub_title` | Maps to `subtitle` |
| `corr_method` | Maps to the correlation method |

Do not use an old positional example to infer the specification grammar. Consult [plot specification](Plot-Specification.md) and the [catalogue](Plot-Catalogue.md).

## Breaking behaviors

| Historical usage | Current replacement |
| --- | --- |
| Plotting side effects without a returned result | Native evidence result; use `result.figure` for its rendered figure |
| Ambient style or arbitrary plotting keywords | Central manifest and validated catalogue options |
| Silent missingness/outlier handling | Declared exclusion reason; preparation owns outliers and transformations |
| `dropna=True` | `missing="drop"` plus `missing_reason` |
| Smoothing or transform callbacks | Explicit prepared input |
| `save=True` | New destination through `result.write(path)` or wrapper `save=path` |
| Figure mutation after computation | Change declarations or data and render again |
| Notebook HTML tables | Native `table`/`text` results with cell provenance |
| Implicit statistical interpretation | Explicit supported research protocol and observation unit |

Old unsupported options fail; they are not silently ignored. `outliers=True`, smoothing, and transformation callbacks raise a preparation requirement. File overwrite is refused. Paper and scientific declarations belong in the [manifest](Manifest.md), [protocol](Research-Protocols.md), and [evidence](Evidence-Result.md) contracts.

## Animation and exact reproduction

The [animation surface](Plot-Catalogue.md#animation-surface) now exposes verified poster evidence and per-frame bundles. It supports declared bar/pie frames rather than executing arbitrary plotting callbacks or shell commands.

Replay now defaults to the recorded runtime identity and exact SVG check. Changed-environment recomputation must be explicit and still match scientific evidence; the complete [replay contract](Evidence-Result.md#replay) is authoritative.

## Preserve historical analyses

Keep the old package version and environment for old notebooks. Migration is a new analysis run: declare prior preparation and assumptions, inspect exclusions and numerical differences, and retain a new bundle. Modern provenance begins with the actual supplied input; it cannot reconstruct undocumented historical preparation.

Next: [first figure](../Guides/First-Figure.md), then [evidence workflow](../Guides/Evidence-Bundle.md).

Legacy utility imports remain available. Helpers that performed hidden outlier removal, random aggregation, global styling, warning suppression, fabricated timestamps, or implicit data loading now raise `LEGACY_API` with an explicit preparation or manifest recovery path. Exact country/area lookup and caller-supplied-axis date formatting remain supported; unknown country identity raises `COUNTRY_IDENTITY`. These errors preserve import paths while requiring each scientific transformation to be declared.
