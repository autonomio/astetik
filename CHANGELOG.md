# v3.0.1

- Preserve cumulative step histogram outlines and clarify invalid panels fields.

# v3.0.0

- Add publication options to `hist`, `line`, `scat`, `regs`, `bar`, `box`, and `violin`: declared statistics and intervals, mark styling, a single-series `color`, `annotate_n`, and `legend_loc`.
- Add the `panels` kind, which composes any number of those plots into one lettered figure, and the `hue_order` field for the order of hue groups.
- Place every legend of those kinds by measurement on the finished figure so it reaches no mark; paint its keys as the marks are painted; refuse a position that cannot clear the data.
- Draw `line` as a mean or median at each x with an SD, SE, Student t, or IQR interval; label series at their line ends with `legend_loc="end"`.
- Fit `regs` in the displayed scale with a confidence band for the mean response, per group with `fit_groups`, and report r, p, and n with `annotate_fit`.
- Add the Student t interval (`errorbar="ci"`) and IQR to `bar`; require `estimator="mean"` for SD, SE, and CI, and name the group when an interval has one observation.
- Mark quartiles inside `violin`, estimate its density in the displayed scale, and show every observation over `bar`, `box`, and `violin` on request.
- Set paper figures on a white page unless the manifest declares `colors.paper`.
- Size facet and panel figures so each plot area keeps the manifest aspect; label shared axes once; key every hue group in the one shared legend; lengthen a single plot by a legend set above it.
- Refuse a figure whose labels, legend, or panels leave the plot no room, instead of drawing a collapsed layout.
- Print logarithmic tick labels as plain text, step linear ticks by 1, 2, 2.5, or 5, print large tick values whole, and end zero-based value axes on a labelled tick.
- Break category names between words when they are wider than their slot.
- Add `scripts/studio.py`, a local page whose controls re-render the actual `astetik.render` call for each of these kinds.

# v2.0.10

- Remove Dependabot version-update configuration; automated security fixes are disabled and dependency automation is asserted absent by the governance suite.

# v2.0.9

- Refresh docs-site dependencies past npm audit CVEs; retire expired braces exception via a 30-day deepmerge exception.

# v2.0.8

- Stop automatic Copilot code review on every push; reviews remain available on request.

# v2.0.7

- Verify transient HEAD failures through safe GET requests with bounded retry delays.
- Retain actionable HTTP diagnostics while redacting URL credentials and query values.

# v2.0.6

- Align the README with the Autonomio product standard, published installation, runnable paper figure, and existing OpenSSF badges.
- Route current canonical repository links within the documentation site while preserving immutable references and code examples.

# v2.0.5

Restore automatic PyPI uploads with the existing Autonomio organization token; retain separately verified release signatures and supply the token only to the pinned upload action in this workflow.

# v2.0.4

Remove extra publication approvals after protected merges; verify and attach the exact signed distributions automatically. Preserve immutable versions, serialize queued releases, skip version-preserving merges before tag creation, and retain verified public signatures during upload recovery.

# v2.0.3

- Isolate publication validation, retain exact release selection after master advances, and separate builds from signing privileges.
- Publish vulnerability response, access continuity, roadmap, and verifiable release-signature practices.
- Approve unchanged legacy 1.16 artifacts through protected keyless signing without local key unlock or PyPI reupload.
- Link the actual OpenSSF Best Practices record and synchronize source metadata.

# v2.0.2

- Consolidate CI coverage, installed-wheel checks and dependency audits while preserving scientific acceptance and required check names.
- Cancel superseded source checks, bound documentation execution and group and stagger dependency updates.
- Record two maintainer-approved, exact-version documentation audit exceptions through November 2, 2026; retain all findings and block every other advisory.
- Delay bounded documentation-link retries after transient network or server failures.

# v2.0.1

- Assign enforcement-surface ownership to bit-mis and retain EnergyGuy3 as the release/PyPI recovery backup.
- Distinguish PR review from protected signing and publication job approval.
- Isolate release-test metadata and link installed documentation to matching immutable source versions.

# v2.0.0

- Compile plots and scientific protocols through explicit specifications and a centralized design manifest.
- Retain typed inputs, observation origins, method declarations, and verified evidence bundles.
- Support publication presets, semantic color roles, and strict artifact replay.
- Adopt canonical documentation, the static documentation site, and its automated checks.
- Preserve original input positions in summaries and nested provenance after declared exclusions.
- Adopt eleven repository laws, ten required checks, pinned toolchains, and protected branch enforcement.
- Eliminate inherited typing and lint diagnostics while retaining scientific rendering and provenance contracts.
- Keep repository-law checks deterministic and require independent human approval alongside automatic review requests.
- Validate other required checks before slice acceptance without depending on the slice check itself.
