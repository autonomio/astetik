# Command-line interface

The installed `astetik` command exposes the same scientific compiler and evidence contracts as Python. Specifications are local JSON documents; manifests may use supported manifest file formats.

## Commands

| Command | Required arguments and behavior |
| --- | --- |
| `astetik catalog` | Prints the versioned kinds, options, defaults, intent map, and specification fields |
| `astetik render` | `--data`, `--spec`, `--output`; optional `--manifest`; writes a new verified bundle |
| `astetik replay` | Bundle path; optional `--output` for a distinct retained copy; optional `--allow-environment-change` for explicit recomputation |

## Concrete installed example

After the [first-success command](../Guides/First-Figure.md) has written `country-regions`, its declarations and readable source companion can be used as CLI inputs:

```bash
astetik catalog
astetik replay country-regions
astetik render --data country-regions/input.csv --spec country-regions/spec.json --manifest country-regions/manifest.json --output country-regions-cli
```

The `render` command creates a new input reading and result; CSV is not the exact typed replay source, so use `replay` when you need the retained exact snapshot. Existing destinations are refused.

## JSON and errors

Catalog output is JSON on stdout. Render/replay success prints `result_id`, `output`, `receipt`, and `verification`. Declared contract failures print JSON containing `code`, `message`, and `details` to stderr and return exit status 2. Argument parsing failures are handled by argparse.

CLI specification loading rejects duplicate JSON fields and nonfinite constants. Callbacks, arbitrary Python objects, and silent option pass-through are not part of the protocol. The [specification reference](Plot-Specification.md) owns field grammar, and [evidence](Evidence-Result.md#replay) owns strict replay versus recomputation.

Authority: [CLI source](../../astetik/_cli.py) and [API/CLI tests](../../tests/test_api.py).

Next: [evidence workflow](../Guides/Evidence-Bundle.md).
