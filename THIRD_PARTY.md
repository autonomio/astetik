# Third-party notices

Astetik's MIT license is [LICENSE](LICENSE). This page retains attribution for incorporated template material and identifies separately licensed assets and dependency review inputs.

## Repository template

Governance and documentation-system material is adapted from the supplied repository template at revision `fa7bf92caab5bb8d7f73120d4dc3526fd86c0348`, whose source is `https://github.com/Vaquum/new-repository-template`.
This legal attribution is the required exception to Astetik/Autonomio branding; it does not claim organizational affiliation or transfer the source project's operational state.

```text
MIT License

Copyright (c) 2024 Vaquum

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Fonts and dependency inputs

Bundled Finlandica is licensed under the SIL Open Font License 1.1; retain [astetik/fonts/OFL.txt](astetik/fonts/OFL.txt). The documentation site's copy retains its own adjacent font/license assets and [template notice](docs-site/THIRD_PARTY_LICENSES.txt).

Review dependencies and licenses against `pyproject.toml`, `requirements/constraints.txt`, `requirements/ci/*.in`, their hash-pinned `*.txt` outputs, and `docs-site/package.json`/`package-lock.json` before release whenever dependencies change materially. This is not a generated or exhaustive SBOM.
Astetik declares actual scientific runtime dependencies; its Python vulnerability check is not vacuous. The documentation audit's exact severity thresholds belong in the [documentation system contract](docs/Developer/Documentation-System.md#security-audit-boundary).

Next: [packaging](docs/Developer/Packaging.md) or [release policy](docs/Developer/Release-Policy.md).
