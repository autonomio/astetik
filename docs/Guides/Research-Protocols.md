# Declare a scientific workflow

Run an implemented protocol on your own measured observations, with method choice and experimental units declared before rendering. The outcome is a figure, numerical analysis, bound caption, and source provenance.

## Prerequisites

- Astetik installed as described in [first figure](First-Figure.md).
- A real study table with observation identities, native numeric measurements, and known units.
- A scientific justification for the experimental unit, method, and assumptions.

The bundled geographic metadata has no measured study outcomes. This guide therefore specifies a required input schema rather than inventing observations. The following code is runnable only after you supply `study.csv` with `specimen`, `group`, and numeric `response`; its group values must be exactly `control` and `treatment`. The `mg/L` declaration must match the actual measurement unit.

## Declare and run the comparison

```python
import astetik as ast

design = ast.Manifest(categories={"control": "primary", "treatment": "secondary"})
spec = {
    "schema_version": "1.0", "kind": "comparison",
    "x": "group", "y": "response", "key": ["specimen"],
    "units": {"response": "mg/L"}, "missing": "error",
    "analysis": {
        "method": "welch", "groups": ["control", "treatment"],
        "observation_unit": "independently sampled specimen",
        "confidence": 0.95,
    },
    "paper": "single",
}
result = ast.render("study.csv", spec, design)
print(result.receipt["analysis"]["contrast"])
print(result.receipt["caption"])
assert result.verify()["passed"]
```

1. Confirm the key identifies observations, not merely row positions.
2. Confirm independence from study design; declaring it does not establish it.
3. Inspect group sizes and the second-minus-first contrast.
4. Inspect contributing marks and the method-bound caption.
5. Publish a fresh bundle through the [evidence workflow](Evidence-Bundle.md).

## Choose an adjacent protocol

Use `paired_t` only with exact complete subject pairing; use `association` for a declared Pearson or Spearman relationship; use `longitudinal` for observed trajectories without trend inference. Parameter and interval rules live once in the [protocol reference](../Reference/Research-Protocols.md).

## Expected result

The receipt records the actual computed estimates, intervals where implemented, method details, assumptions, and caption. No expected numerical values are supplied here because those must come from your real study data.

## Failure boundary

Absent methods, ambiguous or duplicated keys, incomplete pairs, unsupported confidence requests, degenerate samples, protocol facets, and unused analysis fields fail. Do not replace the requested method with another one merely to obtain a figure. Repair preparation or revisit the scientific declaration.

Next: [evidence bundle](Evidence-Bundle.md).
