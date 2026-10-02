# Astetik documentation

Astetik turns a supplied table, a declared representation and method, and a shared design manifest into a figure with computed values and source provenance. This hub owns reader routing; each contract has one canonical page.

## Start by task

| Reader job | Start here |
| --- | --- |
| Get an installed-package result | [First figure](Guides/First-Figure.md) |
| Prepare final publication artwork | [Paper figure](Guides/Paper-Figure.md) |
| Choose and declare an analysis | [Scientific workflow](Guides/Research-Protocols.md) |
| Inspect, publish, or reproduce evidence | [Evidence bundle](Guides/Evidence-Bundle.md) |
| Connect pandas, Polars, files, or Prepared data | [Data and preparation](Reference/Data-and-Prepared.md) |
| Give an agent exact commands | [CLI](Reference/CLI.md) |
| Update existing notebook code | [Migration](Reference/Migration.md) |
| Understand planned and excluded work | [One-year roadmap](Overview/Roadmap.md) |
| Maintain the package or its documentation | [Developer home](Developer/README.md) |

## Product sequence

1. Install the actual checkout and read a real source: [first figure](Guides/First-Figure.md).
2. Declare representation, observation identities, units, missingness, and method: [plot specification](Reference/Plot-Specification.md).
3. Resolve categorical and quantitative color, typography, axes, and physical size from one [manifest](Reference/Manifest.md).
4. Validate and compute the chosen [scientific protocol](Reference/Research-Protocols.md), when requested.
5. Render a figure and inspect its numerical marks and origins: [EvidenceResult](Reference/Evidence-Result.md).
6. Verify at final size and atomically publish a new bundle: [evidence workflow](Guides/Evidence-Bundle.md).
7. Reproduce within the retained contract, or explicitly request recomputation: [replay](Reference/Evidence-Result.md#replay).

The first observable result is an `EvidenceResult` with a figure, table, receipt, and mark origins. Product responsibility ends at the recorded computation and artifact boundary described in [scope](Overview/Boundary.md).

## Five-section map

| Section | Canonical pages |
| --- | --- |
| Overview | This hub; [product boundary](Overview/Boundary.md); [roadmap](Overview/Roadmap.md) |
| Guides | [First figure](Guides/First-Figure.md); [paper figure](Guides/Paper-Figure.md); [scientific workflow](Guides/Research-Protocols.md); [evidence bundle](Guides/Evidence-Bundle.md) |
| Reference | [Specification](Reference/Plot-Specification.md); [30 plot kinds](Reference/Plot-Catalogue.md); [manifest](Reference/Manifest.md); [protocols](Reference/Research-Protocols.md); [evidence](Reference/Evidence-Result.md); [data](Reference/Data-and-Prepared.md); [CLI](Reference/CLI.md); [migration](Reference/Migration.md) |
| Developer | [Maintenance](Developer/README.md); [agent workflow](Developer/Agent-Workflow.md); [configuration](Developer/Configuration.md); [documentation](Developer/Documentation.md); [system contract](Developer/Documentation-System.md); [docstrings](Developer/Writing-Docstrings.md); [packaging](Developer/Packaging.md); [release policy](Developer/Release-Policy.md); [release procedure](Developer/Making-Release.md); [versioning](Developer/Semantic-Versioning.md); [security assurance](Developer/Security-Assurance-Case.md); [debt](Developer/Technical-Debt.md) |
| Packages | [Astetik package](../astetik/README.md) |

Generated category indexes provide navigation, not alternate explanations. The [source-to-route map](../docs-site/docs-map.json) defines the maintained published corpus.

Next: [first figure](Guides/First-Figure.md), or [plot catalogue](Reference/Plot-Catalogue.md) if you already have prepared data.
