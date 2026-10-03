# Semantic versioning

This page owns version decisions and synchronized metadata. The source version is `2.0.7`; that declaration is not proof of a published release.

## Prerequisites and surfaces

Determine public compatibility impact against the real base and inspect all version-bearing surfaces.

| Surface | Responsibility |
| --- | --- |
| `pyproject.toml` | Canonical distribution/build version |
| `astetik.__version__` | Runtime identity consistent with installed metadata |
| `CHANGELOG.md` | Newest `# v<X.Y.Z>` section equals the candidate version |
| `CITATION.cff` | Software citation version; release date only when actually established |
| Git tag `v<version>` | Released identity, created only through authorized release procedure |

No release date or DOI is invented to complete citation metadata.

## Decision rules

- Major: incompatible public API, CLI, schema, package, or artifact contract.
- Minor: compatible new capability.
- Patch: compatible correction, documentation/metadata repair, or dependency refresh.

The version gate enforces a minimum from Conventional Commits: `type!` requires major, `feat` requires minor, other types at least patch. Every non-exempt PR advances strictly forward and adds a specific imperative changelog entry, including documentation-only changes. Configured dependency-bot exemptions are explicit and narrow; [configuration](Configuration.md) owns them.

## Procedure and proof

1. Select the minimum honest bump from actual compatibility impact.
2. Update all version surfaces, preserving the reviewed change's exact meaning.
3. Check the changelog header/content and run the version gate with the actual base/PR declarations.
4. Run packaging/install checks to compare distribution and runtime identity.
5. Follow [release policy](Release-Policy.md) for unused version and publication boundaries.

A larger bump is allowed; a reused tagged/uploaded version is not. Passing SemVer checks says nothing about whether a release occurred.

Next: [making a release](Making-Release.md) or [migration](../Reference/Migration.md).
