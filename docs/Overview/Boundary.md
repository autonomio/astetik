# Product boundary

Astetik owns the passage from supplied observations and explicit choices to rendered, inspectable evidence. It serves scientific researchers and agents through the same public interface.

## Implemented boundaries

| Stage | Astetik owns | Caller owns |
| --- | --- | --- |
| Input | Copying supplied tables; local file reading; verified Prepared integration | Acquiring data, consent, source validity, and preparation |
| Declaration | Validating supported fields, units, keys, exclusions, axes, and method choices | Choosing what constitutes an observation and a valid scientific question |
| Computation | Explicit methods and their recorded numerical output | Whether assumptions hold and results are substantively meaningful |
| Design | One manifest for typography, geometry, axes, and semantic color | Appropriate labels, scientific encodings, and the target publication |
| Publication | Artifact checks, provenance, atomic bundles, and bounded replay | Interpretation, reporting, and downstream distribution |

The public path is `render(data, spec, manifest)`, with `plot()` and named conveniences over the same compiler. The [package page](../../astetik/README.md) owns entry points and module responsibilities.

## Current scope

The [catalogue](../Reference/Plot-Catalogue.md) contains descriptive figures, three declared research protocols, animation posters, and native table/text evidence. Astetik does not provide a general statistical modeling platform, automatically select inference methods, infer causal validity, convert units by relabeling, or remove outliers while plotting.

Paper output is a verified rendering request, not an assurance that every journal will accept every artifact. Exact checks and replay boundaries are defined once in the [evidence reference](../Reference/Evidence-Result.md).

## Example boundary

The shipped country metadata supports geographic naming, grouping, and frequency demonstrations. Numeric country and region codes are identifiers, not scientific measurements. The worked first success counts metadata rows; scientific protocol workflows require your own measured study table.

Notebook-era examples and images are retained in Git history, not as the source of modern API claims. The current Python source, public catalogue, and focused tests are authoritative.

## Roadmap boundary

No future behavior is promised by this documentation. This iteration adopts the documentation system and includes a focused correction of original-row mark provenance, without a broader evidence-compiler redesign. Full repository-governance adoption is separate work; [maintenance](../Developer/README.md) states the checks actually present.

Next: [first figure](../Guides/First-Figure.md).
