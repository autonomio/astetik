# Inspect, publish, and replay evidence

Review a result's origins, publish to a new destination, and verify a retained bundle. This workflow preserves the declared scientific computation and makes later changes reviewable.

## Prerequisites

Produce the `country-regions` bundle through [first figure](First-Figure.md), or supply a real bundle written by the current package. Strict replay requires the recorded runtime identity; the [reference](../Reference/Evidence-Result.md#replay) owns that contract.

## Inspect the retained result

```python
import astetik as ast

result = ast.replay("country-regions")
mark_id = next(iter(result.marks))
origin = result.inspect(mark_id)
print(origin)
print(result.result_id)
print(result.verify()["passed"])
```

For the first-success count, each aggregate mark names its category, computed count, source positions, and contributing `alpha-3` identities. Inspection returns a copy rather than mutable evidence state.

## Publish a distinct destination

```python
# Continue with the verified result from the previous step.
result.write("country-regions-retained")
```

Publication verifies first, retains exact typed inputs, and atomically installs the new bundle. The [evidence reference](../Reference/Evidence-Result.md#bundle-artifacts) owns the artifact inventory and refusal behavior.

The command-line equivalent verifies and recomputes an existing bundle:

```bash
astetik replay country-regions
```

## Review a changed environment explicitly

When the recorded environment cannot be restored, request recomputation explicitly:

```bash
astetik replay country-regions --allow-environment-change
```

This is a different verification mode, not an exact replay claim. Numerical and scientific evidence must still match. Read the [mode boundary](../Reference/Evidence-Result.md#replay) before relying on that result.

## Expected result and failures

A successful publication returns the new directory path. A successful CLI replay prints JSON identifying the reconstructed result and verification report. Changed artifacts, missing inventory, incompatible strict environments, differing scientific evidence, mutated result objects, and existing destinations fail.

For two independently rendered results, `before.diff(after)` groups changed inputs, methods, values, and design. Inspect that report before approving a new analysis run.

Next: [EvidenceResult reference](../Reference/Evidence-Result.md).
