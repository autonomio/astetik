# Plot specification

The specification is the finite JSON declaration consumed by Astetik's public compiler. It describes the representation, selected variables, scientific choices, and axis policy; the [manifest](Manifest.md) owns design.

## Public interface

```python
import inspect
import astetik as ast

print(inspect.signature(ast.render))
print(inspect.signature(ast.plot))
print(ast.catalog()["spec_fields"])
```

`render(data, spec, manifest=None)` returns `EvidenceResult`. `plot(data, kind, *, x=None, y=None, paper=False, manifest=None, **fields)` constructs the same specification from keywords. Named conveniences route to that compiler; special historical argument conventions belong in [migration](Migration.md).

## Fields

| Field | Contract |
| --- | --- |
| `schema_version` | Supported value `"1.0"`; resolved default `"1.0"` |
| `kind` | Required public catalogue kind |
| `x`, `y` | Column names; `y` may be a list for supported multi-series forms; conventional horizontal x and vertical y |
| `hue` | Category or supported continuous-color variable |
| `row`, `col` | Descriptive facets; research protocols reject them |
| `columns` | Explicit correlation or table columns; names must be distinct |
| `order` | Declared category order |
| `options` | Kind-specific settings from `catalog()`; unknown options fail |
| `title`, `subtitle` | Literal display text; resolved default empty strings |
| `labels` | Optional `x`/`y` display labels only |
| `legend` | Boolean; resolved default `true` |
| `paper` | `false`, `true`, `"single"`, or `"double"`; resolved default `false` |
| `key` | One column name or a list of distinct key-column names; preparation keys may be inherited |
| `units` | Column-to-unit text; `"1"` denotes a dimensionless quantity |
| `descriptions` | Column-to-readable-description text |
| `missing` | `"error"` by default, or `"drop"` with a reason |
| `missing_reason` | Required nonempty explanation for declared missing-value exclusion |
| `analysis` | Method declaration for a research protocol only |
| `axes` | Optional `x`/`y` objects containing `scale` and/or `limits` |

Numeric paper measurements require units. Observation keys must be complete and unique. Source metadata and inheritance rules belong in [data and preparation](Data-and-Prepared.md).

## Concrete declaration

This specification refers to the actual bundled country metadata used in [first figure](../Guides/First-Figure.md):

```json
{
  "schema_version": "1.0",
  "kind": "count",
  "x": "region",
  "key": ["alpha-3"],
  "missing": "drop",
  "missing_reason": "The bundled metadata does not assign a region to these rows.",
  "options": {"orient": "h"},
  "paper": "double"
}
```

## Axis and data boundaries

Axis scales are `linear`, `log`, and `symlog`; log requires positive selected measurements. Numeric limits are two increasing finite values. Limits cannot conceal observations or rendered numerical marks, including relevant interval bounds. Bars, counts, and related aggregate displays retain a zero baseline. Correlation axes identify variables and cannot be assigned arbitrary numeric limits.

Selected missing values fail unless exclusion is declared. Infinite numeric values fail. Unselected metadata does not become a measurement merely because it has a numeric dtype. Plotting does not convert units, remove outliers, execute callbacks, or silently accept unfamiliar settings.

Continuous scatter color can be declared with `options.hue_mode="continuous"`; `categorical` treats numeric codes as categories. `auto` respects explicit category bindings when all values are bound. The [catalogue](Plot-Catalogue.md) identifies kinds accepting `hue_mode`.

## Errors and authority

Errors expose `AstetikError.code`, text, and details; `to_dict()` provides a JSON object. Common declarations fail through `SPEC_SCHEMA`, `PLOT_OPTIONS`, `COLUMN_MISSING`, `KEY_INVALID`, `UNITS_REQUIRED`, `MISSING_DATA`, or an axis-specific code. Manifest validation also rejects invalid design documents.

Authority: [compiler and validation source](../../astetik/_api.py), [structured errors](../../astetik/_errors.py), and the shipped [machine catalogue](../../astetik/docs/plots.json).

Next: [plot catalogue](Plot-Catalogue.md), or [scientific protocols](Research-Protocols.md).
