# Astetik package

`astetik/` owns the compiler from supplied scientific data and declarations to figures, numerical output, and verifiable evidence.

## Canonical public documentation

- [Product home](https://github.com/autonomio/astetik/blob/e7eb19a59a52cc270c1d7000779731aa2bae4fed/README.md) owns first success.
- [Specification](https://github.com/autonomio/astetik/blob/e7eb19a59a52cc270c1d7000779731aa2bae4fed/docs/Reference/Plot-Specification.md) owns the Python/JSON declaration contract.
- [Catalogue](https://github.com/autonomio/astetik/blob/e7eb19a59a52cc270c1d7000779731aa2bae4fed/docs/Reference/Plot-Catalogue.md) owns representations and numerical defaults.
- [Manifest](https://github.com/autonomio/astetik/blob/e7eb19a59a52cc270c1d7000779731aa2bae4fed/docs/Reference/Manifest.md) owns centralized design and color.
- [Data](https://github.com/autonomio/astetik/blob/e7eb19a59a52cc270c1d7000779731aa2bae4fed/docs/Reference/Data-and-Prepared.md) owns normalization and Prepared compatibility.
- [Evidence](https://github.com/autonomio/astetik/blob/e7eb19a59a52cc270c1d7000779731aa2bae4fed/docs/Reference/Evidence-Result.md) owns inspection, publication, and replay.

## Public entry points

```python
import astetik as ast

print(ast.__version__)
print(ast.catalog()["schema_version"])
print(ast.select("frequency")["kind"])
```

The package exports `Manifest`, `ColorSystem`, `EvidenceResult`, `AstetikError`, `render`, `plot`, `catalog`, `select`, `replay`, catalogue conveniences, and lazily loaded `Animation`. The installed `astetik` command provides JSON-oriented catalogue/render/replay entry points.

## Ownership and adjacent boundaries

The compiler validates and renders declarations. It does not acquire research data, perform arbitrary preparation, infer a scientifically valid method, or establish causal truth. Preparation remains a caller or compatible Wrangle responsibility; the [adapter contract](https://github.com/autonomio/astetik/blob/e7eb19a59a52cc270c1d7000779731aa2bae4fed/docs/Reference/Data-and-Prepared.md#compatible-prepared-contract) is narrower than general Wrangle API compatibility.

Runtime dependencies are Matplotlib, NumPy, pandas, SciPy, pyshp, PyYAML, and Pillow. Polars input/Prepared support is optional through the `polars` extra. Parquet reader dependencies follow the [data input contract](https://github.com/autonomio/astetik/blob/e7eb19a59a52cc270c1d7000779731aa2bae4fed/docs/Reference/Data-and-Prepared.md). Current versions and bounds are authoritative in [project metadata](https://github.com/autonomio/astetik/blob/e7eb19a59a52cc270c1d7000779731aa2bae4fed/pyproject.toml).

## Source orientation

| Source | Responsibility |
| --- | --- |
| `_api.py` | Public compiler, declarations, conveniences, catalogue, replay |
| `_data.py` | Input copying, metadata, verified preparation, typed snapshots |
| `_analysis.py` | Explicit scientific protocols |
| `_manifest.py`, `_colors.py`, `_presentation.py` | Design, semantic encodings, final composition |
| `_renderers.py`, `_table.py`, `_animation.py` | Graphics and recorded numerical marks |
| `_result.py` | Evidence integrity, verification, atomic publication |
| `_cli.py` | Command-line JSON protocol |
| `extras/`, `fonts/` | Shipped geographic metadata/geometry and licensed fonts |
| `plots/`, `tables/` | Direct compatibility routes to the modern core |

## Operational caveats

Imports do not set notebook-global plotting styles. Rendering and export bind declared style and actual fonts. Later evidence mutation blocks verified publication. Use a new destination for each published result and retain the recorded environment for exact replay.

The old helper-file presence is not a promise of historical public behavior. Use current exports and the [migration reference](https://github.com/autonomio/astetik/blob/e7eb19a59a52cc270c1d7000779731aa2bae4fed/docs/Reference/Migration.md).

Next: [first figure](https://github.com/autonomio/astetik/blob/e7eb19a59a52cc270c1d7000779731aa2bae4fed/docs/Guides/First-Figure.md), or [maintenance](https://github.com/autonomio/astetik/blob/e7eb19a59a52cc270c1d7000779731aa2bae4fed/docs/Developer/README.md).
