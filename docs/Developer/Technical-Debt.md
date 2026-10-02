# Technical debt

This page owns the register for limitations explicitly accepted and carried. Unstarted work belongs in issues; an initial measured governance baseline is not evidence that all historical code meets a zero-debt ideal.

## Prerequisites

Read current source, focused tests, the relevant gate budget, and issue/PR evidence before recording a limitation. Do not turn a failed acceptance condition into accepted debt merely to pass a gate.

## Register contract

Each accepted item records a stable identifier, affected surface, evidence source, current severity, realistic blast radius, trigger for correction, migration/removal path, and canonical documentation requiring change.
Severity describes current repository risk. State any downstream assumption that increases it; do not inflate it with hypothetical harms.

## Current register boundary

The completed typing and lint repair leaves zero Pyright errors/warnings, zero explicit dynamic typing or suppression escapes, and zero full Ruff findings in [.github/budgets.json](../../.github/budgets.json). Scientific operations now use precise domain types and coherent modules; actual regression tests retain exact marks, methods, tables and rendered pixels. The largest/median package ratio is below the restored template ceiling of 16. [governance.yml](../../governance.yml) owns current thresholds.

| Debt id | Current state and evidence | Correction path |
| --- | --- | --- |
| `GOV-TYPE-001` | Resolved: strict Pyright and both AST/regex escape scans are zero; matched upstream dataframe/scientific stubs and typed native operation contracts | Keep the zero budget and complete package scan; reject suppressions or new dynamic escapes |
| `GOV-RUFF-001` | Resolved: full package/governance/product-test Ruff report has zero findings, including annotation and complexity rules | Keep zero per-path/code ceilings and frozen rule configuration |
| `GOV-SHAPE-001` | Resolved: coherent scientific, rendering, snapshot and publication modules pass file balance under the restored 16 ceiling | Keep every actual module under its measured declared line cap |
| `GOV-TEST-001` | Retained: the product test/code ratio passes the adopted 0.33 minimum but remains below the template's 1.0 default; aggregate physical-line counts do not establish behavioral coverage | Add missing scientific contract and regression protection with behavior work; strengthen the threshold when actual coverage and ratio justify it |

The initial 4,696-error/3-warning typing snapshot resolved the wrong Python environment. The corrected invocation explicitly selects the installed interpreter; it measured 4,070 errors/0 warnings before repair and zero after repair. That correction is part of the evidence, not a discarded failure. Ruff's 577 inherited findings are eliminated. No initial diagnostic budget is retained as a waiver.

Product limitations remain in the canonical [boundary](../Overview/Boundary.md) and [evidence contracts](../Reference/Evidence-Result.md). The budget/configuration and current gate reports remain authoritative; passing these gates does not establish research validity.

## Closure procedure

1. Fix source and add meaningful regression protection in the scoped change.
2. Correct the canonical page describing the old limitation.
3. Remove the active debt entry or retain a short resolved note with actual change evidence.
4. Reduce affected budgets when the measured debt decreases; do not leave stale mitigation language.

Next: [configuration](Configuration.md) or [maintenance](README.md).
