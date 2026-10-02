# Agent scientific workflow

This page owns Astetik's package-use procedure for agents. Repository actions first follow [AGENTS.md](../../AGENTS.md) and [CLAUDE.md](../../CLAUDE.md); these scientific instructions do not authorize remote publication or reviewer messages.

## Prerequisites and ownership

Use installed Astetik on Python 3.11 or newer, actual input data, and one versioned study manifest. The [first-figure guide](../Guides/First-Figure.md) uses retained country/area metadata; research protocols require user-owned measured observations.
Astetik owns declared computations and artifact/provenance checks. Preparation choices and study validity remain the researcher's responsibility.

## Execute the declared workflow

1. Read `astetik.catalog()` for supported kinds, fields, defaults, and method limits; use `astetik.select(intent)` to inspect representation guidance.
2. Prefer `render(data, spec, manifest)` with a finite JSON specification. Declare observation keys, units, missingness, and scientific methods before rendering.
3. Use one immutable manifest across the study. Bind category colors to identities or semantic roles; paper figures require explicit multi-category mappings.
4. Prepare transformations and exclusions before plotting. Retain verified preparation receipts and pass [Prepared-compatible input](../Reference/Data-and-Prepared.md) when available.
5. Select `paper=True`, `paper="single"`, or `paper="double"` for the final physical layout. Every public catalogue kind has a paper path, including animation posters and native table/text evidence.
6. For research protocols, declare keys, observation units, and an explicit supported method. Facets and unused method fields fail; confidence is not accepted by Spearman or observed longitudinal summaries.
7. Inspect `EvidenceResult.table`, `receipt`, and mark origins before publication. Layout checks cover physical dimensions, font/glyph constraints, clipping, and tick/table collisions within their stated bounds.
8. Change input or declarations and render again; do not mutate sealed evidence. Write to a new directory with `result.write(new_directory)`; existing paths are refused.
9. Replay under the retained environment for exact SVG and scientific equivalence. `strict_environment=False` explicitly permits recomputation in a changed environment while retaining numerical, method, mark, and caption checks.

The canonical [plot specification](../Reference/Plot-Specification.md), [manifest](../Reference/Manifest.md), [protocols](../Reference/Research-Protocols.md), and [evidence result](../Reference/Evidence-Result.md) own exact schemas and errors.

## Observable result and failure boundary

A successful workflow yields a sealed result or a new evidence bundle whose tables, declarations, row origins, design, and receipt can be inspected. It does not establish independence, causality, appropriate sampling, or universal scientific validity.
Missing required declarations, invalid designs, unverifiable upstream receipts, unsupported options, changed sealed state, and failed publication checks raise errors; correct the source rather than suppressing them.

For package changes, run the [maintenance checks](README.md#verify-package-changes). The real installed metadata workflow is `python -m astetik.docs.first_figure NEW_DIRECTORY`. Version 2.0 breaks older notebook usage; use [migration](../Reference/Migration.md).

Next: [first figure](../Guides/First-Figure.md), [paper figure](../Guides/Paper-Figure.md), or [evidence bundle](../Guides/Evidence-Bundle.md).
