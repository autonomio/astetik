# Design manifest

`Manifest` is the immutable, versioned design policy shared by every catalogue kind. It owns visual decisions; [plot specifications](Plot-Specification.md) own scientific declarations.

## Public names

```python
import astetik as ast

manifest = ast.Manifest(categories={"control": "primary", "treatment": "secondary"})
revised = manifest.with_primary("#235B60")
assert manifest.categories["control"] == revised.categories["control"] == "primary"
print(revised.to_dict())
```

`Manifest()` supplies defaults. `from_dict(document)` validates a document; `load(path)` reads JSON, TOML, or safe YAML; `to_dict()` returns portable JSON-compatible values. `with_primary(hex)` returns a new validated manifest. `font_path` and `font_info` expose actual font resolution separately from portable choices.

## Schema and units

The supported `schema_version` is `"1.0"`. Partial sections inherit defaults; unknown fields and duplicate loaded keys fail.

| Section | Fields and resolved defaults |
| --- | --- |
| `typography` | `font="Finlandica"`, `font_path=null`, `fontsize=9`, `labelsize=9`, `titlesize=10`, `ticksize=8`, `legendsize=8`; sizes in points |
| `paper` | `preset="single"`, `width_mm=89`, `aspect=1.45`, `dpi=300`, `min_fontsize=7` |
| `axes` | `linewidth=0.6`, `grid=false`, `spines=["left","bottom"]`, `tick_direction="out"`, `tick_length=2.5`; line/tick sizes in points |
| `categories` | Identity-to-color bindings, empty by default |

`paper=True` uses the manifest's preset and physical width. A specification's `paper="single"` or `"double"` selects 89 mm or 178 mm respectively. Aspect is width divided by height for one panel; facet composition derives panel geometry. PNG dpi must be an integer of at least 300. Paper type sizes are raised to the declared floor, which cannot be below 7 pt.

## Color as communication

| Role | Default | Meaning |
| --- | --- | --- |
| `primary` | `#2A4A70` | Principal measurement/series and sequential endpoint |
| `secondary` | `#806A45` | Secondary semantic binding |
| `paper` | `#F7F7F2` | Figure and export background |
| `ink` | `#252D33` | Strong foreground and selected graphical details |
| `muted` | `#626B72` | Subordinate foreground and labels |
| `line` | `#D4DADD` | Rules, grid, and structural lines |
| `negative` | `#A54532` | Negative diverging endpoint |
| `neutral` | `#F7F7F2` | Diverging midpoint |
| `positive` | `#2A4A70` | Positive diverging endpoint |

Role values are six-digit hex colors. Category values are either literal hex or existing role names. Bindings remain role names in serialized manifests and resolve against current colors at use. Changing primary updates primary-bound categories, sequential scales, and the positive endpoint when it equals the previous primary. Literal category values remain fixed.

Categories bind to identities independently of appearance order. Exploratory defaults derive from label identity and reject insufficient differentiation; paper plots with multiple color-encoded categories require explicit bindings. Position-only categories can share the primary mark color. Foreground ink/muted require at least 4.5:1 contrast against paper, semantic marks/categories at least 3:1, category pairs CIELAB distance at least 12, signed endpoints at least 35, and neutral-to-endpoint distance at least 20. These are configured-color checks, not universal accessibility guarantees for every opacity or visual impairment.

Sequential scales interpolate in CIELAB. Diverging scales preserve an exact neutral midpoint; correlation uses a fixed full coefficient range. Use `ColorSystem(manifest).categorical(labels, strict=True)`, `.sequential()`, `.diverging()`, and `.primary` when inspecting encodings.

## Font resolution and side effects

Finlandica Regular is bundled with its license. Explicit font files must exist; a relative file path resolves beside a loaded manifest. Unavailable alternative font families fall back to Matplotlib's bundled DejaVu Sans and record that decision. `font_info` records requested/resolved family, actual path, SHA256, and fallback status.

`rc(paper=False)` returns scoped Matplotlib settings; `dimensions(paper=False, panels=1)` returns inches. Manifest construction does not change plotting rcParams; bundled fonts are registered for resolution. The renderer binds actual font files, and publication checks include [glyph coverage](Evidence-Result.md#publication-verification).

## Example and authority

The full shipped [example manifest](../../astetik/docs/design.example.json) demonstrates every configurable field and role-bound categories. It is a configuration example, not a research dataset.

Authority: [manifest source](../../astetik/_manifest.py), [color source](../../astetik/_colors.py), and [design tests](../../tests/test_design.py).

Next: [paper workflow](../Guides/Paper-Figure.md).
