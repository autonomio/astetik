# Data and Prepared integration

Astetik normalizes supplied data into a copied scientific snapshot. It preserves declared metadata and, for compatible prepared results, verifies and retains upstream preparation evidence. It does not own data acquisition or preparation.

## Supported public inputs

Pass these forms to `astetik.render()` or `astetik.plot()`:

| Input | Behavior and dependency |
| --- | --- |
| pandas `DataFrame` | Deep table copy; pandas is a runtime dependency |
| Polars `DataFrame` | Native table copy and conversion into the plotting snapshot; install the `polars` extra first |
| Local CSV path | Duplicate-column detection, file digest, pandas read, changed-file detection |
| Local Parquet path | File digest and pandas-engine reading, or installed Polars when a pandas Parquet engine is unavailable |
| Compatible Wrangle `Prepared` | Native table and receipt digest verification, copied table, inherited metadata, retained upstream receipt |

No remote data fetch occurs through this input surface. CSV numeric identifiers may need explicit preparation when dtype interpretation would alter their meaning.

## Metadata

Pandas attrs may supply `key` or `row_keys`, `units`, and `descriptions`. Explicit specification keys identify marks and must be complete and unique. Compatible preparation keys can be inherited when omitted; specifications can add metadata, but inherited units cannot be silently relabeled to a conflicting unit.

Units are text declarations, not conversion operators. Prepare unit conversions before rendering. Numeric country/region codes in the bundled metadata are identifiers, not measurements.

## Actual bounded table example

```python
from importlib.resources import as_file, files
import pandas as pd
import astetik as ast

with as_file(files("astetik").joinpath("extras", "countries.csv")) as source:
    entries = pd.read_csv(source).loc[:4, ["name", "alpha-3"]].copy()
result = ast.table(entries, columns=["name", "alpha-3"], key=["alpha-3"], paper="single")
assert result.verify()["passed"]
print(len(result.table))
```

The explicit first-five selection bounds the display and uses actual source rows. Provenance in this form begins with the supplied selected table; use a compatible preparation receipt when earlier selection decisions must remain in the evidence chain. For direct file provenance over the full asset, use [first figure](../Guides/First-Figure.md).

## Compatible Prepared contract

Install Polars support before passing a prepared result; from this source checkout, use `python -m pip install '.[polars]'`. The optional adapter does not itself install or run Wrangle.

The compatible object exposes a Polars `data` table, a finite JSON `receipt`, and retained `_data_digest`/`_receipt_digest` integrity values. Astetik verifies the SHA256 of rechunked uncompressed Arrow IPC with `compat_level=CompatLevel.oldest()`, the receipt digest, and `receipt.output.sha256`. It copies the table and preserves the verified receipt in `receipt.upstream_receipt`.

It inherits preparation keys, units, and variable descriptions. A changed table or receipt fails with `PREPARED_CHANGED`; conflicting unit relabeling fails with `UNIT_CONFLICT`. This is compatibility with the declared preparation protocol, not a claim that every historical Wrangle release supplies it.

## Missingness and snapshots

Only selected fields participate in plot missingness. `missing="error"` is the default; `drop` requires a reason and records excluded identities. Infinite selected numeric values fail. Unselected missing metadata remains in the retained input snapshot.

Typed snapshot encoding supports native scientific scalars, missingness, dtypes, categories, indices, and ordered nested list/dict values used in mark tables. Unsupported object types fail rather than invoking user serializers. Exact replay reads `input.json`; [evidence](Evidence-Result.md) owns that lifecycle.

Authority: [normalization and snapshot source](../../astetik/_data.py) and [input tests](../../tests/test_results.py).

Next: [specification](Plot-Specification.md), or [scientific workflow](../Guides/Research-Protocols.md).
