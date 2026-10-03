<div align="center">
  <br />
  <a href="https://github.com/autonomio"><img src="https://avatars.githubusercontent.com/u/28189776?v=4" alt="Autonomio" width="150" height="150" /></a>
  <br />
</div>
<br />
<div align="center"><b>Astetik turns declared scientific figures into checked graphics, numerical output, and repeatable research evidence.</b></div>

<div align="center">
  <a href="#astetik">Astetik</a> •
  <a href="#what-astetik-is-not">Scope</a> •
  <a href="#capabilities">Capabilities</a> •
  <a href="#first-successful-figure">First Figure</a> •
  <a href="#choose-the-next-task">Learn More</a>
</div>
<br />
<div align="center">
  <a href="https://www.bestpractices.dev/en/projects/15154"><img src="https://www.bestpractices.dev/projects/15154/badge" alt="OpenSSF Best Practices" /></a>
  <a href="https://scorecard.dev/viewer/?uri=github.com/autonomio/astetik"><img src="https://api.scorecard.dev/projects/github.com/autonomio/astetik/badge" alt="OpenSSF Scorecard" /></a>
  <a href="https://pypi.org/project/astetik/"><img src="https://img.shields.io/pypi/v/astetik?label=pypi" alt="PyPI version" /></a>
  <a href="https://github.com/autonomio/astetik/blob/master/docs/README.md"><img src="https://img.shields.io/badge/docs-manual-blue" alt="Astetik documentation" /></a>
  <a href="https://github.com/autonomio/astetik/actions/workflows/ci.yml"><img src="https://github.com/autonomio/astetik/actions/workflows/ci.yml/badge.svg?branch=master&amp;event=push" alt="Master scientific contracts and documentation" /></a>
</div>

<hr />

<a id="astetik"></a>

# Astetik — Scientific figures with evidence

*Scientific figures from a declared specification and shared design, with numerical output and verifiable provenance.*

Astetik compiles supplied data, a finite plot specification, and one design manifest
into a figure and its evidence. Declare the scientific decision and visual encoding,
inspect the computed values and their origins, then retain the result for publication
and bounded replay. Python, notebooks, and command-line agents use the same contracts.

## What Astetik Is Not

Astetik owns validation, rendering, supported statistical protocols, publication
checks, and evidence bundles. Researchers own data preparation, sampling, study
design, method selection, and interpretation. Astetik does not infer those decisions
or establish independence, causality, or scientific suitability.

The [product boundary](https://github.com/autonomio/astetik/blob/master/docs/Overview/Boundary.md) defines that responsibility.
Imports do not change notebook-global plotting styles; design is applied within
the declared rendering workflow.

## Capabilities

The [plot catalogue](https://github.com/autonomio/astetik/blob/master/docs/Reference/Plot-Catalogue.md) covers **30 kinds**, each with
a paper path, including animation posters and table/text evidence.

| Research task | Supported capability |
| --- | --- |
| Choose a representation | Inspect the catalogue and intent guidance for supported plots, defaults, and constraints |
| Keep a study visually coherent | One immutable manifest controls typography, axes, dimensions, and semantic color bindings |
| Prepare a paper figure | Single- or double-column physical sizes, vector exports, retained fonts, and final-size verification |
| Declare a scientific computation | Explicit supported estimation, resampling, comparison, association, regression, and longitudinal protocols |
| Inspect what a mark means | Numerical tables, original input positions, observation identities, methods, and verified upstream preparation receipts |
| Audit and repeat a result | Sealed evidence, atomic publication, integrity checks, strict replay, and comparison of changed results |

Color binds to meaning and category identity across figures. Set your study's primary
with `manifest.with_primary("#235B60")`; primary-bound categories update together.
The [manifest reference](https://github.com/autonomio/astetik/blob/master/docs/Reference/Manifest.md) owns palette, contrast,
typography, and physical-size rules.

## First successful figure

Install the current **2.0 API** from PyPI:

```bash
python -m pip install astetik
```

Use Python 3.11 or later. The example reads the bundled country/area metadata;
no data download or invented research measurements are needed. Choose a new output
directory; existing destinations are rejected.

```python
from importlib.resources import as_file, files
from pathlib import Path
import astetik as ast

manifest = ast.Manifest(categories={
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
resource = files("astetik").joinpath("extras", "countries.csv")
with as_file(resource) as source:
    result = ast.render(source, spec, manifest)

assert result.table["estimate"].tolist() == [60, 57, 51, 51, 29]
assert result.receipt["observations"]["used"] == 248
assert result.verify()["passed"]
print(result.table[["category", "estimate"]].to_string(index=False))

bundle = result.write(Path("country-regions"))
repeated = ast.replay(bundle)
assert repeated.result_id == result.result_id
assert repeated.verify()["passed"]
print(bundle.resolve())
```

Expected result: Africa 60, Americas 57, Asia 51, Europe 51, and Oceania 29, followed
by the absolute path of `country-regions`. Of the 249 retained geographic entries,
248 contribute; Antarctica (`ATA`) has no region and is explicitly excluded and
accounted for. These counts describe the shipped snapshot, not a current geopolitical
reference or a scientific inference. The [first-figure guide](https://github.com/autonomio/astetik/blob/master/docs/Guides/First-Figure.md)
owns the source and observation accounting.

`render` returns an `EvidenceResult`: a figure, numerical table, declarations, receipt,
and mark-to-observation origins. `paper="double"` selects a 178 mm figure; use
`paper="single"` for 89 mm, or `paper=True` for the manifest's declared preset.
Verification checks the final physical artifact before publication. The
[paper-figure guide](https://github.com/autonomio/astetik/blob/master/docs/Guides/Paper-Figure.md) covers design revisions and failures.

## Retain the evidence

| File | Retained evidence |
| --- | --- |
| `figure.pdf`, `figure.svg`, `figure.png` | Vector figures and a raster companion |
| `input.json`, `input.csv` | Exact typed input snapshot and a readable companion |
| `summary.json`, `summary.csv` | Numerical output and a readable companion |
| `spec.json`, `manifest.json` | Resolved scientific and design declarations |
| `marks.json` | Mark values, computations, and contributing observation origins |
| `receipt.json` | Source, methods, environment, verification, result identity, and artifact digests |
| `font.ttf`, `font-notices.txt` | Selected font bytes and notices for the bundled families |

The same evidence can be inspected and repeated from a shell or an agent:

```bash
astetik catalog
astetik replay country-regions
```

The [bundle guide](https://github.com/autonomio/astetik/blob/master/docs/Guides/Evidence-Bundle.md) covers inspection, publication,
and replay; the [command-line reference](https://github.com/autonomio/astetik/blob/master/docs/Reference/CLI.md) defines JSON output
and structured failures.

## Risk Boundary

Strict replay requires the recorded compatibility envelope and verifies exact
regenerated SVG plus scientific evidence. Explicit recomputation in a changed
environment retains numerical and provenance checks without claiming identical
rendering. Unsigned receipts establish integrity relative to retained evidence;
they do not establish authorship or the truth of observations.

Publication checks cover declared dimensions, visible type sizes, font/glyph identity,
clipping, and selected tick/table collisions. Journal-specific requirements and other
graphical collisions remain the researcher's responsibility. The
[evidence reference](https://github.com/autonomio/astetik/blob/master/docs/Reference/Evidence-Result.md) defines these bounded contracts.

## Choose the next task

| Job | Start here |
| --- | --- |
| Create and inspect a first figure | [First figure](https://github.com/autonomio/astetik/blob/master/docs/Guides/First-Figure.md) |
| Use final paper dimensions and study colors | [Paper figure](https://github.com/autonomio/astetik/blob/master/docs/Guides/Paper-Figure.md) |
| Declare a method for measured study data | [Research protocols](https://github.com/autonomio/astetik/blob/master/docs/Guides/Research-Protocols.md) |
| Select a plot and its supported options | [Plot catalogue](https://github.com/autonomio/astetik/blob/master/docs/Reference/Plot-Catalogue.md) |
| Integrate verified prepared data | [Data and Prepared](https://github.com/autonomio/astetik/blob/master/docs/Reference/Data-and-Prepared.md) |
| Retain, inspect, and repeat evidence | [Evidence bundle](https://github.com/autonomio/astetik/blob/master/docs/Guides/Evidence-Bundle.md) |
| Integrate Python or a command-line agent | [Specification](https://github.com/autonomio/astetik/blob/master/docs/Reference/Plot-Specification.md); [command line](https://github.com/autonomio/astetik/blob/master/docs/Reference/CLI.md) |
| Replace an older notebook call | [Migration](https://github.com/autonomio/astetik/blob/master/docs/Reference/Migration.md) |
| Navigate the whole manual | [Documentation hub](https://github.com/autonomio/astetik/blob/master/docs/README.md) |

Agents start with the [scientific workflow](https://github.com/autonomio/astetik/blob/master/docs/Developer/Agent-Workflow.md),
`ast.catalog()`, and `ast.select(intent)`. Installed documentation entry points live
beside `astetik.__file__` under `docs/`. Structured `AstetikError` fields support
recovery by correcting declarations rather than substituting a method.

<a id="contribute-support-and-cite"></a>

## Contributing

Start with [CONTRIBUTING.md](https://github.com/autonomio/astetik/blob/master/CONTRIBUTING.md) and
[developer setup and validation](https://github.com/autonomio/astetik/blob/master/docs/Developer/README.md). Propose work through
[Autonomio Astetik issues](https://github.com/autonomio/astetik/issues).

## Support

Use [SUPPORT.md](https://github.com/autonomio/astetik/blob/master/SUPPORT.md) for bug reports, feature requests, and usage questions.
Include Astetik and Python versions, the specification, manifest, result identifier,
and full relevant error. Use small shareable actual data for a reproduction.

## Vulnerabilities

Use [SECURITY.md](https://github.com/autonomio/astetik/blob/master/SECURITY.md) for supported source and the private reporting route.
Arrange a private channel with the maintainer when private vulnerability reporting
is unavailable. Do not put exploitable details or credentials in public issues.

## Citations

Use [CITATION.cff](https://github.com/autonomio/astetik/blob/master/CITATION.cff) for software citation metadata. A reproducible
research citation should identify Astetik, its exact version or source commit,
and the retained specification, manifest, and result identifier. No DOI is supplied.

## License

[MIT License](https://github.com/autonomio/astetik/blob/master/LICENSE). [Third-party notices](https://github.com/autonomio/astetik/blob/master/THIRD_PARTY.md) retain template
attribution and Finlandica's separate font license.
