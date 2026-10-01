# First figure from the installed package

Create a regional frequency figure from actual bundled country metadata and inspect its counted observations. This workflow exercises publication output without inventing research measurements.

## Prerequisites

- Python 3.11 or newer.
- A checkout of the current Astetik source and permission to install it in your Python environment.
- A new output directory only if you choose publication below.

From the checkout, install the package:

```bash
python -m pip install .
```

The workflow uses package resources, so it also works outside the checkout. It requires no data download.

## Render the actual metadata

```python
from importlib.resources import as_file, files
import astetik as ast

resource = files("astetik").joinpath("extras", "countries.csv")
design = ast.Manifest(categories={
    "Africa": "primary", "Americas": "#A54532", "Asia": "#2D7D60",
    "Europe": "#7D5595", "Oceania": "secondary",
})
spec = {
    "schema_version": "1.0", "kind": "count", "x": "region",
    "key": ["alpha-3"],
    "order": ["Africa", "Americas", "Asia", "Europe", "Oceania"],
    "missing": "drop",
    "missing_reason": "The bundled metadata does not assign a region to these rows.",
    "options": {"orient": "h"},
    "title": "Recorded geographic entries by region",
    "paper": "double",
}
with as_file(resource) as source:
    result = ast.render(source, spec, design)

print(result.table[["category", "estimate"]].to_string(index=False))
print(result.receipt["observations"])
assert result.verify()["passed"]
```

The specification declares the missingness decision. The file reader retains the source-file hash, and counted marks retain the contributing country identities. The [specification reference](../Reference/Plot-Specification.md) owns field semantics.

## Expected observations

The bundled file has 249 geographic entries, not a claim about the contemporary number of sovereign states. Its missing region is Antarctica (`ATA`), so 248 entries contribute to the figure.

| Recorded region | Entries |
| --- | ---: |
| Africa | 60 |
| Americas | 57 |
| Asia | 51 |
| Europe | 51 |
| Oceania | 29 |

These are expected values for the retained repository asset, not stable API guarantees or a current geopolitical reference. `result.receipt["observations"]` records the input, used, excluded identities, policy, and reason.

## Inspect and publish

`result.inspect(next(iter(result.marks)))` returns the origins of the first counted mark. To publish, call `result.write("country-regions")` using a path that does not exist. The full [bundle guide](Evidence-Bundle.md) owns publication and replay.

The installed worked example performs the same descriptive job and publishes to the supplied directory:

```bash
python -m astetik.docs.first_figure country-regions
```

## Failure boundary

A missing installed resource indicates a packaging defect. Missing selected values fail without the declared exclusion policy; existing output directories fail instead of being overwritten. Correct data or design declarations and render again.

Next: [paper figure](Paper-Figure.md).
