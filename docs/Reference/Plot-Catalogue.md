# Plot catalogue

The public catalogue defines 31 accepted representation kinds and their current option grammar. It does not choose a statistical inference method for the caller. Common declaration fields belong in [plot specification](Plot-Specification.md).

## Public selection and defaults

```python
import astetik as ast

catalogue = ast.catalog()
assert len(catalogue["plots"]) == 31
print(catalogue["plots"]["hist"])
print(ast.select("frequency"))
```

`catalog()` returns `schema_version`, `intents`, `spec_fields`, and `plots`. Each kind reports paper support, allowed options, and resolved defaults. The shipped [JSON catalogue](../../astetik/docs/plots.json) is generated from this API; its exact option/default inventory is authoritative.

`select(intent)` maps declared distribution, comparison, association, longitudinal, frequency, correlation, or geography intent to a representation. It reports when a scientific method is required; it never infers that method.

## All current kinds

| Kind | Representation or computation | Defining defaults and constraints |
| --- | --- | --- |
| `hist` | Observed histogram counts, proportions, percents, or density | NumPy `bins="auto"`; count default; shared bin edges, even in log space on a logarithmic axis; final bin includes its upper edge |
| `kde` | One- or two-dimensional Gaussian density | Scott bandwidth, 128-point grid, no support extension; nonsingular samples required |
| `multikde` | Grouped density panels | KDE rules; hue groups can become rows |
| `oned` | Observation event/rug plot | One numeric variable; identity marks |
| `scat` | Numeric scatter | Point size 18; alpha 0.85; circle marker with a thin paper-coloured edge; hue mode auto |
| `twod` | Two-vector scatter convenience | Scatter semantics; two vectors or N-by-2 array through the convenience wrapper |
| `line` | Observed series, or a mean or median at each x with its interval | Each observation by default; stable ascending x order; straight segments; line width 1.25 |
| `count` | Category row counts | Vertical orientation by default; zero baseline |
| `multicount` | Grouped category counts | Count semantics; hue grouping or facets |
| `bar` | Category aggregation with an optional interval and observations | Sum by default; no interval; zero baseline; value axis ends on a labelled tick |
| `bartwo` | Grouped category aggregation | Mean by default; no error bars |
| `bargrid` | Faceted category aggregation | Mean by default; no error bars |
| `box` | Distribution summary with outliers or every observation shown | Linear quantiles; Tukey 1.5-IQR whiskers that end on observations |
| `violin` | Gaussian-density category distributions with quartiles marked | Scott bandwidth; 128-point grid; slim inner box; density of log10 values on a logarithmic axis; split requires two hue categories |
| `strip` | Category observations with deterministic jitter | Van der Corput offset; jitter 0.12 |
| `swarm` | Observations packed in display space | Deterministic packing; insufficient space fails |
| `grid` | Category observations in a facet layout | Deterministic jitter; point size 18 |
| `pie` | Proportion of displayed totals | Start angle 90 degrees; percentage labels; nonnegative nonzero total |
| `corr` | Numeric correlation matrix | Spearman default; full coefficient range; no annotation/mask by default |
| `regs` | Scatter and ordinary least-squares line with its confidence band | Draw observations, fit, and 0.95 band by default; fitted in the displayed scale; at least three observations and varying x required |
| `roc` | Binary receiver-operating curve | Positive label 1; stable descending-score threshold sweep |
| `world` | Country-code choropleth | Bundled geometry; unprojected longitude/latitude; one declared aggregate per country code |
| `compare` | Separate observation panels per numeric column | Category hue required; additional facets unsupported |
| `overlap` | Two measurement aggregates within categories | Mean default; horizontal orientation; category hue required |
| `comparison` | Two-group mean/contrast protocol | Explicit Welch or paired t declaration required |
| `association` | Scatter plus declared correlation protocol | Explicit Pearson or Spearman declaration required |
| `longitudinal` | Observed trajectory protocol | Explicit observed method; unique time within series |
| `animate` | Selected animation poster frame | Zero-based frame 0; bar frame by default |
| `table` | Native rendered table and cell provenance | Four significant display digits; exact selected values retained |
| `text` | Native text table and cell provenance | Four significant display digits for numeric cells |
| `panels` | Several complete plots composed in one lettered figure | Panels of `hist`, `line`, `scat`, `regs`, `bar`, `box`, or `violin`; letters a, b, c; each plot area keeps the manifest aspect |

Every kind accepts paper mode through the compiler. [Manifest](Manifest.md) and [publication checks](Evidence-Result.md#publication-verification) own the shared final-size controls. A supported kind does not imply every combination of facets, axes, options, and dtypes is valid.

## Publication orders

`hist`, `line`, `scat`, `regs`, `bar`, `box`, and `violin` share one presentation contract, and `panels` composes them. `catalog()` reports every option and default; the table names what each kind lets a caller decide.

| Kind | Statistic options | Mark options |
| --- | --- | --- |
| `hist` | `stat` (`count`, `proportion`, `percent`, `density`), `cumulative`, `common_norm`, `bins` or `binwidth`, `kde` with `bw_method`, `reference` (`mean`, `median`), `rug` | `element` (`bars`, `step`), `fill`, `multiple` (`layer`, `stack`, `dodge`), `shrink`, `alpha`, `edgecolor`, `edgewidth`, `orient` |
| `line` | `estimator` (`null`, `mean`, `median`), `errorbar` (`sd`, `se`, `ci`, `iqr`), `confidence`, `sort` | `interval` (`band`, `bars`), `band_alpha`, `capsize`, `linewidth`, `linestyle`, `dashes`, `drawstyle`, `marker`, `markersize`, `alpha` |
| `scat`, `regs` | `regs` only: `fit_reg`, `fit_groups`, `band`, `confidence`, `annotate_fit` | `point_size`, `alpha`, `marker`, `edgecolor`, `edgewidth`, `hue_mode`; `regs` adds `draw_scatter`, `linewidth` |
| `bar` | `estimator` (`mean`, `median`, `sum`), `errorbar`, `confidence` | `width`, `alpha`, `edgecolor`, `edgewidth`, `capsize`, `linewidth`, `points` (`none`, `all`), `point_size`, `jitter`, `orient` |
| `box` | `whis`, `means` | `width`, `fill`, `alpha`, `linewidth`, `points` (`outliers`, `all`), `point_size`, `jitter`, `orient` |
| `violin` | `bw_method`, `gridsize`, `cut` | `width`, `fill`, `alpha`, `linewidth`, `inner` (`box`, `quartiles`, `none`), `split`, `points` (`none`, `all`), `point_size`, `jitter`, `orient` |

All seven accept `color` for a single series (a manifest role or `#RRGGBB`), `annotate_n` to state sample sizes, and `legend_loc`. Legend keys are painted with the fill, opacity, and edge of the marks they name.

`legend_loc` is `best`, one of eight inside positions, `outside right`, or `outside top`; `line` also accepts `end`, which names each series beside its last point. The position is measured on the finished figure. `best` uses an inside position that reaches no mark and otherwise sets the legend in rows above the plot. An inside position that reaches a mark is refused, except that an upper position on a zero-based value axis lengthens that axis when its limits are not declared. An `outside right` legend wider than 40% of the figure is refused. A figure whose labels, legend, or panels leave the plot no room is refused rather than drawn.

A fit is a straight line in the displayed scale: on a logarithmic axis it is fitted to the log10 values, and the receipt records the scale, slope, intercept, r, p-value, and n. A `symlog` axis has no such line, so a fit on one is refused. Its band bounds the mean response at the declared confidence. Category names wider than their slot break between words.

Facets (`row`, `col`) repeat one kind over the levels of a column with shared axes; each axis is labelled once and one legend keys every group. This example composes three kinds from the Natural Earth estimates shipped for the `world` kind:

```python
from importlib.resources import as_file, files

import pandas as pd
import shapefile

import astetik as ast

with as_file(files("astetik").joinpath("extras", "countries.dbf")) as source:
    records = shapefile.Reader(str(source.with_suffix(""))).records()
frame = pd.DataFrame([record.as_dict() for record in records])
frame = frame[(frame["POP_EST"] > 0) & (frame["GDP_MD_EST"] > 0)]
data = pd.DataFrame(
    {
        "area": frame["ADM0_A3"],
        "income": frame["INCOME_GRP"].str.slice(3),
        "population": frame["POP_EST"],
        "output": frame["GDP_MD_EST"] * 1e6,
    }
)
log = {"scale": "log"}
spec = {
    "kind": "panels",
    "paper": "double",
    "key": ["area"],
    "units": {"population": "persons", "output": "USD"},
    "options": {"ncols": 3},
    "panels": [
        {"kind": "hist", "x": "output", "axes": {"x": log}},
        {
            "kind": "regs",
            "x": "population",
            "y": "output",
            "axes": {"x": log, "y": log},
            "options": {"annotate_fit": True},
        },
        {
            "kind": "box",
            "x": "income",
            "y": "output",
            "axes": {"x": log},
            "options": {"orient": "h", "points": "all"},
        },
    ],
}
result = ast.render(data, spec)
assert result.verify()["passed"]
print(result.receipt["methods"]["plot"]["panels"][1]["regression"]["slope"])
```

Each panel's methods are recorded under `methods.plot.panels`, and every mark carries its panel letter in `facet`.

## Numerical boundaries

KDE fails on inadequate or singular samples. Histogram edges must contain all selected observations; a KDE overlay requires histogram density units. Category sum/mean/median aggregations are explicit options. `sd`, `se`, and `ci` describe a mean and `iqr` a median; each interval other than `iqr` requires at least two observations in every group, and the refusal names the group that has one. `ci` is the two-sided Student t interval at the declared `confidence`. Box outliers remain visible.

Numeric hue has explicit auto/categorical/continuous modes for scatter-family kinds. Numeric group codes remain categories when declared as such. Comparisons of multiple measurements require compatible units; transformations belong in preparation. Scientific interval rules belong in the [protocol reference](Research-Protocols.md).

## Animation surface

`astetik.animate(data, x=..., y=..., frame=N, plot_type="bar", ...)` produces one native `EvidenceResult`. It records the selected source row, observation key, and source field for each quantity. The two measurement columns must share a declared unit; category bindings use those column names.

`astetik.Animation(data, x, y, label_col=None, plot_type="bar", filename=None, *, paper=False, manifest=None, units=None, frame=0, key=None)` constructs frame results in input row order. `poster` exposes the selected `EvidenceResult`. `write(new_directory, duration_ms=500)` publishes a GIF, verified per-frame bundles, and an animation receipt. Supported frame representations are bar and pie; duration must be an integer of at least 20 ms. Supplying `filename` explicitly publishes during construction. `Animation` reads and normalizes input once; every frame retains the same input digest, source and preparation metadata, and later caller-input changes do not alter constructed frames.

This is display of supplied frame observations, not trajectory inference or automatic interpolation of missing measurements.

## Table and text surface

`astetik.table()` and `astetik.text()` return the same native evidence type, with selected source values and per-cell origins. `digits` accepts integers from 1 to 15 for significant-digit formatting only. They do not require IPython. Large tables or long text can fail [cell-fit checks](Evidence-Result.md#publication-verification); use an explicitly bounded selection or a suitable design.

Authority: [renderer source](../../astetik/_renderers.py), [animation](../../astetik/_animation.py), [tables](../../astetik/_table.py), and [renderer tests](../../tests/test_renderers.py).

Next: [scientific workflow](../Guides/Research-Protocols.md), or [first descriptive figure](../Guides/First-Figure.md).
