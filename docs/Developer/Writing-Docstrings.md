# Writing docstrings

A docstring earns its place by explaining a constraint, unit, failure, side effect, or boundary that the signature does not already communicate. This page is the contributor review standard adapted from the supplied documentation template.

## Prerequisites and authority

No tools are needed to read this standard. The local governance adoption includes `governance/check_docstrings.py` and `check_module_docstrings.py`, configured in the lint plane. Run them with Python 3.13 and the pinned gate toolchain; passing local checks does not establish activated remote enforcement or complete semantic accuracy.

## Review criteria

| Element | Standard |
| --- | --- |
| Opening | Describe the caller's result: Return, Parse, Validate, Resolve, or Extract |
| Empty verbs | Avoid calculate, generate, make, and build when they describe only machine activity |
| Defaults | Keep default values in the signature; do not duplicate them in descriptive prose |
| Notes | Use `NOTE:` when a searchable note marker is needed |
| Content | Add relevant units, identity, ordering, mutation, computation, or error boundaries |
| Omission | Delete padding and signature narration instead of supplying ceremonial prose |

Module docstrings should orient readers to the module's actual responsibility. The automated checks enforce declared title/module rules; review still owns whether each statement is useful and true. Changes to runtime docstrings remain scoped code changes, not permission granted by this standard.

## Concrete existing example

Astetik's `Manifest.rc()` describes the useful side-effect boundary: it returns settings for `rc_context` without mutating global Matplotlib plotting state. That tells readers more than the method name and dictionary return annotation alone. Its [source](../../astetik/_manifest.py) is authoritative.

When changing callable behavior in a later implementation task, check the documented constraint against a focused test, inspect the real signature, and run the [current package checks](README.md#verify-package-changes). Do not write aspirational guarantees into docstrings.

## Maintenance boundary

Signature defaults remain source-owned. Public usage, schema tables, and workflow examples belong in their canonical maintained Markdown pages. A docstring change must not silently expand the public API or suggest a scientific assumption is proven.

Next: [Documentation System](Documentation-System.md) or [maintenance](README.md).
