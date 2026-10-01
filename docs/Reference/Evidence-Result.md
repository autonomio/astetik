# Evidence result and replay

`EvidenceResult` binds a rendered figure to supplied input, declared computation, numerical output, design, and mark origins. This reference owns integrity, publication, and reproduction contracts.

## Public surface

An ordinary `astetik.render()` or `astetik.plot()` call returns `EvidenceResult`.

| Surface | Meaning and side effect |
| --- | --- |
| `figure` | Rendered Matplotlib figure |
| `table` | Numerical marks or the protocol-specific numerical output |
| `data` | Retained input snapshot, including declared excluded rows |
| `spec`, `manifest` | Resolved declarations and portable design |
| `receipt` | Scientific, provenance, and environment records |
| `marks` | Mark-id mapping for observations, aggregates, cells, or evaluated curves |
| `result_id` | Digest identifying the bound scientific result and recorded runtime/design |
| `inspect(mark_id)` | Returns a copy of a mark's values, computation, source rows and keys |
| `diff(other)` | Reports changed inputs, methods, values, and design |
| `verify()` | Returns a publication report without writing a bundle |
| `write(directory)` | Verifies and atomically publishes a new bundle; returns its path |

Inspection, comparison, verification, and publication reject later evidence or figure mutation. Re-render from changed inputs or declarations instead of editing a sealed object.

## Minimum concrete use

After [first figure](../Guides/First-Figure.md) has produced its bundle:

```python
import astetik as ast

result = ast.replay("country-regions")
origin = result.inspect(next(iter(result.marks)))
assert "source_keys" in origin
print(result.result_id)
print(result.verify()["passed"])
```

## Receipt boundary

The receipt records source metadata, verified upstream receipt when supplied, units, descriptions, keys, input/used/excluded observation accounting, exclusion reason, plot and analysis methods, numerical analysis, computed caption, actual font, environment identity, and input/table/specification/manifest/mark digests.

Scientific assumptions remain declared. Hashes and seals detect mismatches against retained evidence; they are not external signatures proving authorship or the truth of input data.

## Publication verification

Checks are performed on the final rendered artifact:

- Declared physical dimensions and positive finite geometry.
- Minimum visible type size and text clipping against the figure bounds.
- Adjacent tick-label overlap.
- Table text fitting within cells and adjacent cell-text overlap.
- Actual font resolution, font checksum, and glyph coverage; Unicode spacing characters have an explicit allowance.
- Finite axis bounds.

`verify()` returns `passed`, detailed `checks`, and limitations. Paper rendering fails through `PAPER_VERIFICATION` when these checks fail; `write()` also verifies before exporting. These checks do not inspect every possible graphical collision, enforce every journal's rules, or establish study validity.

## Bundle artifacts

| Artifact | Purpose |
| --- | --- |
| `figure.pdf` | Vector figure with TrueType embedding |
| `figure.svg` | Vector figure with outlined text |
| `figure.png` | Raster companion at declared export dpi |
| `font.ttf` | Exact selected font bytes when the receipt records a font identity |
| `font-notices.txt` | Full notices for bundled Finlandica and Matplotlib DejaVu/STIX families |
| `input.json`, `input.csv` | Exact typed snapshot and readable input companion |
| `summary.json`, `summary.csv` | Typed and readable numerical output |
| `spec.json`, `manifest.json` | Resolved scientific and design declarations |
| `marks.json` | Mark-to-source bindings |
| `receipt.json` | Scientific receipt, verification, export metadata, file digests, and integrity seal |

JSON snapshots retain types, ordered values, column/index metadata, and supported scientific scalars. CSV is a companion, not the exact replay source. Compiled bundles retain the selected font bytes and verify their SHA-256 against the receipt before publication. The accompanying font notices cover the named bundled families; user-supplied fonts require their own notices and redistribution permission. Exports omit metadata timestamps where specified by the exporter.

Publication stages each bundle in its own temporary directory and uses an atomic no-overwrite directory step. Exactly one competing publisher can install the destination; others fail with `OUTPUT_EXISTS`. No persistent destination lock is created. Process termination before installation may leave a staging directory, but the unused destination remains publishable. Handled export failures remove their own staging directory. Systems without the required atomic primitive fail explicitly. Graphics and data are written only when the caller invokes publication, or explicitly supplies an output destination to a wrapper/CLI.

## Replay

`astetik.replay(directory, strict_environment=True)` is the default. It verifies the receipt seal and complete artifact inventory before reconstruction. Retained JSON documents reject duplicate keys and nonfinite constants. Input/summary snapshots and mark bindings must match their scientific receipt digests; resealing the raw file inventory cannot conceal contradictory sidecars. Strict mode requires matching recorded runtime source hashes, Python/implementation and dependency versions, platform/architecture, and FreeType version/build identity. It checks recomputed scientific fields, result identity, and exact regenerated SVG bytes.

`strict_environment=False` explicitly permits recomputation in a changed environment. The receipt/inventory hashes, numerical output, marks, methods, caption, analysis, observation accounting, units, and keys still must match. It does not require exact regenerated SVG equality or claim identical environment identity.

These modes verify different bounded contracts. Retain the recorded environment for an exact replay claim; the package does not recreate an environment from a receipt automatically.

## Errors and authority

Common refusals include `RESULT_CHANGED`, `OUTPUT_EXISTS`, `VERIFICATION_FAILED`, `BUNDLE_CHANGED`, `BUNDLE_INCOMPLETE`, `ENVIRONMENT_CHANGED`, and `REPLAY_DIFFERENCE`.

Authority: [result implementation](../../astetik/_result.py), [replay implementation](../../astetik/_api.py), and [result tests](../../tests/test_results.py).

Next: [evidence workflow](../Guides/Evidence-Bundle.md), or [CLI](CLI.md).
