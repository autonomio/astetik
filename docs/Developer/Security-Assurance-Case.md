# Security assurance case

This page owns the argument for Astetik's security requirements and its evidence boundaries. [SECURITY.md](../../SECURITY.md) owns reporting and response; [release policy](Release-Policy.md) owns software distribution. The argument applies to the declared local library and repository controls, with the residual risks below.

## System boundary and threat model

Astetik accepts supplied tables, local source files, specifications/manifests, and retained evidence bundles. It validates declarations, computes supported methods, renders figures, and writes a new local artifact directory. It has no hosted account service, authentication database, arbitrary plotting callback interpreter, or data-acquisition service.

An attacker may supply malformed or misleading data, declarations, fonts, or bundles; modify an artifact or a source during use; forge a self-consistent receipt; race publication; or compromise a dependency, contribution, workflow credential, or distribution service. Assets are the caller's files and credentials, the integrity of recorded scientific computations, reviewed source, and the origin of distributed software. Filesystem and process permissions remain those of the caller.

The caller chooses a trusted execution environment, source and publication destination, scientific assumptions, and an appropriate operating-system account. Astetik checks its declared input and publication contracts; it does not authenticate a research participant, sandbox arbitrary Python objects, or establish that supplied measurements are true.

## Trust boundaries

| Boundary | Untrusted or privileged input | Control and evidence scope |
| --- | --- | --- |
| Scientific input to compiler | Tables, local files, declarations, upstream preparation | Allowlisted schemas, copied typed snapshots, preparation identity and source-change checks |
| Retained bundle to replay | JSON, CSV, fonts, artifact inventory and environment claims | Fixed local filenames, digests, semantic bindings, typed reconstruction, strict replay |
| Result to filesystem | Mutable figure/evidence state and caller-selected destination | Verification, state checks, unique staging and atomic no-overwrite publication |
| Contributor to protected source | Code, workflow changes, issue/PR text | Slice/parser tests, required checks, independent review and live ruleset audit |
| Dependency to trusted environment | Runtime, build, governance and documentation packages | Declared bounds, hashed CI inputs, pinned actions, vulnerability monitoring |
| Reviewed source to distribution | Tag, release identity, artifacts, publisher credentials | Release controls and actual signing/verification evidence; configuration alone is insufficient |

## Applied secure design principles

The following ten principles are the [OpenSSF secure-design prerequisite](https://www.bestpractices.dev/en/criteria/0#know_secure_design). Their application is bounded by the interfaces and evidence named here.

| Principle | Applied argument | Source and regression evidence |
| --- | --- | --- |
| Economy of mechanism | Python, CLI and compatibility entry points share one compiler and explicit specification grammar rather than separate decision engines | [Compiler](../../astetik/_compile.py); [specification contracts](../../tests/test_specification_contracts.py) |
| Fail-safe defaults | Invalid declarations fail; failed verification prevents `write()`; existing destinations are refused rather than overwritten | [Result publication](../../astetik/_result.py); [publication tests](../../tests/test_publication.py) |
| Complete mediation | The public publication path checks sealed state and final figure verification; replay checks inventory, file digests and scientific bindings before accepting retained evidence | [Replay](../../astetik/_replay.py); [artifact binding tests](../../tests/test_replay_artifact_bindings.py); [result tests](../../tests/test_results.py) |
| Open design | Schemas, identity computation, validators and tests are public. Integrity relies on specified checks, not hidden grammar or secret algorithms | [Identity](../../astetik/_result_state.py); [snapshot parser](../../astetik/_snapshot_parse.py); [replay identity tests](../../tests/test_replay_source_identity.py) |
| Separation of privilege | Protected contributions require checks and an eligible independent human review; release/publication add protected environments and separate opt-in conditions | [Constitution](../../CLAUDE.md); [ruleset snapshot](../../.github/rulesets/master.json); [release policy](Release-Policy.md) |
| Least privilege | The runtime uses caller filesystem permissions without an authentication service or shell execution. CI declares job permissions and nonpersistent checkout credentials except the explicit release push | [CLI](../../astetik/_cli.py); [workflow contracts](../../governance/tests/test_ci_contract.py); [activation](../../SETUP.md) |
| Least common mechanism | Inputs/manifests are copied, rendering uses a scoped context and lock, and each export has unique staging rather than a shared stale lockfile | [Compiler](../../astetik/_compile.py); [export](../../astetik/_result_export.py); [design](../../tests/test_design.py) and [concurrent publication tests](../../tests/test_publication.py) |
| Psychological acceptability | Humans and agents use explicit specifications, stable error codes, documented recovery paths and one immutable manifest; hidden exclusions and legacy transformations are refused | [CLI contract](../Reference/CLI.md); [migration](../Reference/Migration.md); [numeric declaration tests](../../tests/test_numeric_option_identity.py) |
| Limited attack surface | Supported data formats, catalogue kinds and options are explicit; runtime rendering does not execute arbitrary callbacks, perform network acquisition, or host user accounts | [Product boundary](../Overview/Boundary.md); [specification](../../astetik/_spec.py); [specification tests](../../tests/test_specification_contracts.py) |
| Input validation with allowlists | Validators check field names, types, values, finite numerical declarations, typed snapshots, and exact artifact inventory; invalid inputs raise structured errors | [Manifest parser](../../astetik/_manifest_load.py); [snapshot parser](../../astetik/_snapshot_parse.py); [snapshot boundary tests](../../tests/test_snapshot_json_boundary.py) |

[MAINTAINERS.md](../../MAINTAINERS.md#security-competence) records the primary maintainer's dated secure-design and common-error knowledge attestation. The table records applied mechanisms; it does not claim a training certificate or independent review.

## Common implementation weaknesses

| Weakness | Countermeasure and actual boundary | Evidence |
| --- | --- | --- |
| Unsafe deserialization (CWE-502) | Retained values use typed JSON reconstruction; manifests use a SafeLoader that rejects object construction and duplicate mappings, rather than pickle or executable input | [Manifest code](../../astetik/_manifest_load.py); [YAML tests](../../tests/test_design.py); [JSON boundary tests](../../tests/test_replay_json_boundary.py) |
| Invalid or ambiguous input (CWE-20) | Allowlisted schema checks reject duplicate keys, nonfinite constants and boolean values masquerading as scientific numbers | [Snapshot](../../astetik/_snapshot_parse.py); [numeric tests](../../tests/test_numeric_option_identity.py); [snapshot tests](../../tests/test_snapshot_json_boundary.py) |
| Path traversal (CWE-22) | Replay requires a fixed inventory of local basenames; retained font symlinks are refused. The caller's chosen source/destination is not an authorization sandbox | [Replay](../../astetik/_replay.py); [artifact tests](../../tests/test_replay_artifact_bindings.py); [font tests](../../tests/test_font_portability.py) |
| Concurrent modification and stale state (CWE-367) | Source-change, font identity, sealed-result and artifact-binding checks reject the tested races and mutations; arbitrary hostile process interference is outside this claim | [Source reader](../../astetik/_source_file.py); [font tests](../../tests/test_font_portability.py); [result tests](../../tests/test_results.py) |
| Concurrent publication (CWE-362) | Complete output is staged under a unique directory and installed with the platform's exclusive rename; only the failing writer's staging is cleaned | [Atomic publication](../../astetik/_result_atomic.py); [export](../../astetik/_result_export.py); [process/concurrency tests](../../tests/test_publication.py) |
| Resource leakage (CWE-772) | World geometry readers close on successful and failing paths; each tested failure retains its structured exception | [World renderer](../../astetik/_render_world.py); [reader lifetime tests](../../tests/test_world_reader_lifetime.py) |
| Command injection (CWE-78) | Runtime declarations do not execute shell commands or callbacks; maintenance tooling passes argument arrays to subprocesses. Reviewed workflow source is privileged code | [CLI](../../astetik/_cli.py); [ruleset tooling](../../governance/ruleset_gate.py); [workflow contracts](../../governance/tests/test_ci_contract.py) |
| Unmaintained components and supply-chain input (CWE-1104) | Package bounds, hashed CI tools, SHA-pinned actions, dependency updates and vulnerability checks expose known advisories; they cannot prove every dependency benign | [Dependency audit](../../governance/check_dependency_vulnerabilities.py); [Dependabot](../../.github/dependabot.yml); [documentation audit](Documentation-System.md#security-audit-boundary) |

## Verification and retained evidence

For the merged 2.0 source baseline, [1099 product tests and coverage](https://github.com/autonomio/astetik/actions/runs/36914931313) passed with 4444 of 4945 statements covered (89.87%). [Packaging](https://github.com/autonomio/astetik/actions/runs/36914931308) produced two bit-identical distributions and verified installed-wheel imports outside the checkout on Python 3.11, 3.12 and 3.13. These runs identify their exact source candidate; later changes require new evidence.

The merged-master [scientific and documentation checks](https://github.com/autonomio/astetik/actions/runs/36969583737), [CodeQL](https://github.com/autonomio/astetik/actions/runs/36969583672), and [privileged ruleset audit](https://github.com/autonomio/astetik/actions/runs/36969583756) succeeded. The last checked the full protection payload, including bypass actors, using the actual audit credential. No token permission flags or secret contents follow from that success.

To evaluate a new candidate:

1. Run its package/governance tests and affected gates, retaining the exact commit, coverage and failure output.
2. Inspect changed trust boundaries, schemas, dependencies, workflow permissions, action pins, artifact contents and documentation.
3. Verify live protection and eligible review through [SETUP.md](../../SETUP.md); local policy or an advisory review does not prove enforcement.
4. Verify an actual distributed artifact through [release policy](Release-Policy.md), preserving the signing identity and verifier result.
5. Resolve failed checks or report the unresolved claim. A configured capability, green skipped job or badge questionnaire is insufficient evidence.

```bash
python -m pytest tests governance/tests -q
gh attestation verify ARTIFACT --repo autonomio/astetik
```

The first exercises local contracts. The second applies only to an actually attested artifact; a missing or invalid attestation fails the provenance claim.

## Residual risks

SHA-256 receipt seals establish consistency and detect the tested changes; they do not authenticate a research source or prevent an attacker from replacing an entire bundle with self-consistent fabricated content. Prepared receipts likewise retain upstream claims without proving consent, measurement validity, sampling, independence or causal interpretation.

Large or hostile tables, fonts and native dependency parsers can exhaust resources or exploit an unknown upstream flaw. Astetik is not a sandbox. Use bounded trusted inputs and an appropriate isolated process when the source is hostile; operating-system permissions and resource limits are caller responsibilities. Other code in the same Python process can alter shared Matplotlib state; scoped rendering and recorded font identities cover the tested interference, not arbitrary process compromise.

Static analysis, property tests and vulnerability databases have bounded coverage. The product test-density exception remains explicit in [technical debt](Technical-Debt.md). No project-owned memory-unsafe module, native sanitizer/fuzzer proof, universal security guarantee, or independent security review is claimed.

Scientific evidence bundles are unsigned. Software release signing is a separate [distribution control](Release-Policy.md): configured attestations do not establish that a 2.0 wheel/sdist has been published, signed or verified. No SLSA level, SBOM or offline provenance claim follows without actual retained evidence.

A site build does not prove deployed TLS, headers, redirects or availability. [Maintainer continuity](../../MAINTAINERS.md#continuity) rests on separately identified human attestation and verified permissions; the primary operator's own PR still needs eligible independent approval.

Next: [security reporting](../../SECURITY.md), [release policy](Release-Policy.md), or [maintenance](README.md).
