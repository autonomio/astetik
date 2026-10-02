# Prepare a paper figure

Render an existing result at the intended physical size, with one shared design and semantic color mapping. This guide changes presentation while retaining the supplied observations and method.

## Prerequisites

Complete [first figure](First-Figure.md) and publish its `country-regions` bundle. Keep the recorded environment for strict replay. Use a new destination for the revised result.

## Revise the design and render again

```python
import astetik as ast

original = ast.replay("country-regions")
design = ast.Manifest.from_dict(original.manifest).with_primary("#235B60")
spec = {**original.spec, "paper": "single"}
revised = ast.render(original.data, spec, design)
changes = original.diff(revised)
assert changes["design"]["changed"]
assert not changes["values"]["changed"]
assert revised.verify()["passed"]
```

The first-success manifest binds Africa to `primary`, so the new primary propagates to that category. Literal category colors remain explicit.

Rendering `original.data` starts provenance from the supplied pandas snapshot. It does not inherit the originating file metadata or upstream preparation receipt. Retain the original bundle alongside the revised bundle to preserve that source chain. The [manifest reference](../Reference/Manifest.md) owns binding, palette, typography, and physical-size rules.

## Review the final artifact

Inspect the revised figure and numerical table. `revised.verify()` checks the rendered artifact at its declared size; its exact checks belong in the [evidence reference](../Reference/Evidence-Result.md#publication-verification). Publish only after the checks pass:

```python
# Continue with the revised result from the previous step.
revised.write("country-regions-single")
```

The resulting bundle contains the revised graphics and design, plus the retained scientific input and provenance. It is a separate result with a separate identity.

## Failure boundary

Long labels, dense category sets, missing glyphs, tick overlap, or insufficient space can fail final-size verification. Choose a larger permitted width, fewer declared facets, or more precise labels and render again. Do not shrink text below the publication floor or mutate a sealed figure to bypass the contract.

Study validity and journal-specific requirements remain outside these artifact checks; see [product scope](../Overview/Boundary.md).

Next: [publish and replay evidence](Evidence-Bundle.md).
