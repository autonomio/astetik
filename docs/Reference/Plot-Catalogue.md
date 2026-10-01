# Plot catalogue

The public catalogue defines 30 accepted representation kinds and their current option grammar. It does not choose a statistical inference method for the caller. Common declaration fields belong in [plot specification](Plot-Specification.md).

## Public selection and defaults

```python
import astetik as ast

catalogue = ast.catalog()
assert len(catalogue["plots"]) == 30
print(catalogue["plots"]["hist"])
print(ast.select("frequency"))
```

`catalog()` returns `schema_version`, `intents`, `spec_fields`, and `plots`. Each kind reports paper support, allowed options, and resolved defaults. The shipped [JSON catalogue](../../astetik/docs/plots.json) is generated from this API; its exact option/default inventory is authoritative.

`select(intent)` maps declared distribution, comparison, association, longitudinal, frequency, correlation, or geography intent to a representation. It reports when a scientific method is required; it never infers that method.

## All current kinds

| Kind | Representation or computation | Defining defaults and constraints |
| --- | --- | --- |
| `hist` | Observed histogram counts or density | NumPy `bins="auto"`; count default; shared bin edges; final bin includes its upper edge |
| `kde` | One- or two-dimensional Gaussian density | Scott bandwidth, 128-point grid, no support extension; nonsingular samples required |
| `multikde` | Grouped density panels | KDE rules; hue groups can become rows |
| `oned` | Observation event/rug plot | One numeric variable; identity marks |
| `scat` | Numeric scatter | Point size 18; alpha 0.85; circle marker; hue mode auto |
| `twod` | Two-vector scatter convenience | Scatter semantics; two vectors or N-by-2 array through the convenience wrapper |
| `line` | One or more observed series | Stable ascending x order; straight segments; line width 1.25 |
| `count` | Category row counts | Vertical orientation by default; zero baseline |
| `multicount` | Grouped category counts | Count semantics; hue grouping or facets |
| `bar` | Category aggregation | Sum by default; no error bars; zero baseline |
| `bartwo` | Grouped category aggregation | Mean by default; no error bars |
| `bargrid` | Faceted category aggregation | Mean by default; no error bars |
| `box` | Distribution summary with outliers shown | Linear quantiles; Tukey 1.5-IQR whiskers |
| `violin` | Gaussian-density category distributions | Scott bandwidth; 128-point grid; split requires two hue categories |
| `strip` | Category observations with deterministic jitter | Van der Corput offset; jitter 0.12 |
| `swarm` | Observations packed in display space | Deterministic packing; insufficient space fails |
| `grid` | Category observations in a facet layout | Deterministic jitter; point size 18 |
| `pie` | Proportion of displayed totals | Start angle 90 degrees; percentage labels; nonnegative nonzero total |
| `corr` | Numeric correlation matrix | Spearman default; full coefficient range; no annotation/mask by default |
| `regs` | Scatter and ordinary least-squares line | Draw observations and fit by default; varying x required |
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

Every kind accepts paper mode through the compiler. [Manifest](Manifest.md) and [publication checks](Evidence-Result.md#publication-verification) own the shared final-size controls. A supported kind does not imply every combination of facets, axes, options, and dtypes is valid.

## Numerical boundaries

KDE fails on inadequate or singular samples. Histogram edges must contain all selected observations; a KDE overlay requires histogram density units. Category sum/mean/median aggregations are explicit options; SD/SE error bars require sufficient observations and are not confidence intervals. Box outliers remain visible.

Numeric hue has explicit auto/categorical/continuous modes for scatter-family kinds. Numeric group codes remain categories when declared as such. Comparisons of multiple measurements require compatible units; transformations belong in preparation. Scientific interval rules belong in the [protocol reference](Research-Protocols.md).

## Animation surface

`astetik.animate(data, x=..., y=..., frame=N, plot_type="bar", ...)` produces one native `EvidenceResult`. It records the selected source row, observation key, and source field for each quantity. The two measurement columns must share a declared unit; category bindings use those column names.

`astetik.Animation(data, x, y, label_col=None, plot_type="bar", filename=None, *, paper=False, manifest=None, units=None, frame=0, key=None)` constructs frame results in input row order. `poster` exposes the selected `EvidenceResult`. `write(new_directory, duration_ms=500)` publishes a GIF, verified per-frame bundles, and an animation receipt. Supported frame representations are bar and pie; duration must be an integer of at least 20 ms. Supplying `filename` explicitly publishes during construction.

This is display of supplied frame observations, not trajectory inference or automatic interpolation of missing measurements.

## Table and text surface

`astetik.table()` and `astetik.text()` return the same native evidence type, with selected source values and per-cell origins. `digits` accepts integers from 1 to 15 for significant-digit formatting only. They do not require IPython. Large tables or long text can fail [cell-fit checks](Evidence-Result.md#publication-verification); use an explicitly bounded selection or a suitable design.

Authority: [renderer source](../../astetik/_renderers.py), [animation](../../astetik/_animation.py), [tables](../../astetik/_table.py), and [renderer tests](../../tests/test_renderers.py).

Next: [scientific workflow](../Guides/Research-Protocols.md), or [first descriptive figure](../Guides/First-Figure.md).
