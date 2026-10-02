# Astetik

[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/15154/badge)](https://www.bestpractices.dev/en/projects/15154)

Astetik, an Autonomio project, compiles scientific figures, numerical output, and provenance from a declared plot specification and design manifest.

It owns validation, rendering, explicit statistical protocols, publication checks, and evidence bundles. Data preparation and the validity of a study design remain outside that boundary; see [product scope](docs/Overview/Boundary.md).

The current package has 30 [catalogue kinds](docs/Reference/Plot-Catalogue.md), a centralized [design manifest](docs/Reference/Manifest.md), and [inspectable, replayable evidence](docs/Reference/Evidence-Result.md). Python and command-line agents use the same contracts.

## Install and get a first result

Python 3.11 or newer is required. From a checkout of this version:

```bash
python -m pip install .
python -m astetik.docs.first_figure country-regions
```

The second command reads the bundled country metadata and writes a new `country-regions` evidence directory. It counts recorded regions; it does not invent measurements or perform scientific inference. A missing region is explicitly excluded and accounted for. The [first-figure guide](docs/Guides/First-Figure.md) explains the source, exact expected observations, and equivalent Python workflow.

The output includes PDF, SVG, PNG, numerical tables, typed inputs, a specification, manifest, mark provenance, and a receipt. Existing output directories are refused; [bundle publication](docs/Guides/Evidence-Bundle.md) owns the full procedure.

## Start by task

- [Create a figure](docs/Guides/First-Figure.md) from actual bundled metadata.
- [Make a paper figure](docs/Guides/Paper-Figure.md) at its final physical size.
- [Declare a scientific protocol](docs/Guides/Research-Protocols.md) for your own measured study data.
- [Use prepared data](docs/Reference/Data-and-Prepared.md) with verified upstream provenance.
- [Move an older notebook](docs/Reference/Migration.md) to the evidence interface.
- [Browse the documentation](docs/README.md) or [package boundaries](astetik/README.md).

## Responsibility and project information

Publication and replay checks establish bounded artifact and computation contracts; they do not establish independence, causality, or universal scientific validity. Their exact scope belongs in the [evidence reference](docs/Reference/Evidence-Result.md).

Use [support](SUPPORT.md) for usage problems and [security policy](SECURITY.md) for private-reporting boundaries. Contributors start with [maintenance](docs/Developer/README.md); repository rules live in [the constitution](CLAUDE.md) and [governance](GOVERNANCE.md). Cite the software using [CITATION.cff](CITATION.cff) and retain the exact Astetik version/source and result identifier. The package is [MIT licensed](LICENSE); [third-party notices](THIRD_PARTY.md) retain template attribution and Finlandica's separate license.

Next: [first figure](docs/Guides/First-Figure.md).
