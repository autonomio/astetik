# CLAUDE.md

The repository law, operating discipline, and code stance — the single canonical constitution for every contributor, human or agent.

> **Astetik governance adoption:** these are local standards, not proof that GitHub enforces them. Read [SETUP.md](SETUP.md) before activation; live permissions, required checks, review availability, and publication controls require explicit verification. No commit, push, PR, review message, ruleset update, or release is authorized by this document alone.

Read [AGENTS.md](AGENTS.md) before each task or message. Human task instructions control the authorized action and take precedence over repository workflow defaults. Product use follows [the agent workflow](docs/Developer/Agent-Workflow.md); gate configuration follows [Configuration](docs/Developer/Configuration.md).

## Motivation

We don't want saga ornamentation. We want commits that move the needle. The needle is the thing that humans actually benefit from in the software. Always ask "what are the key usage paths here, and how is this proposed change moving those?". Never be satisfied with work that seems to check the boxes, but doesn't really move the capability where the actual benefit is.

## The laws

Eleven laws. Ten are workflow gates on every PR; the eleventh is branch protection on `master`. Any failure blocks merge. No bypass. This is the required operating standard after verified activation; a checked-in snapshot alone is not live enforcement.

1. **Every PR closes exactly one OPEN slice-labelled issue — plus that slice's parent PRD when, and only when, the slice is the PRD's last open sub-issue.** PR title byte-equals the slice issue's title. Diff stays within the issue's `## Surfaces` globs. Diff touches no path in `## Out of Scope`. Issue body preserves every `> **Significance.**` blockquote from the slice template verbatim, and every `Done Means` checkbox is checked or carries `OVERRULED: <reason>` before merge; the `slice_closeout_guard` workflow writes the closeout evidence fields when a merged PR closes the issue and reopens an evidence-less close. A PR opened by an author in `automation.bot_authors` skips this law while `automation.exempt_gates` lists `slice` — dependency bumps carry no slice issue, and the other nine laws still run on them. *(pr_checks_slice)*

2. **PR title, every non-merge commit, and the linked issue title match Conventional Commits v1.0.0, and no commit message or the PR title names an AI/LLM assistant.** Allowed types: `feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert`. *(pr_checks_cc)*

3. **Typing discipline never weakens.** No new `Any`, `cast(..., Any)`, `# type: ignore`, `# pyright: ignore`, or `# noqa`. Pyright error count cannot rise. The `typing` budget in `.github/budgets.json` cannot be raised, and the scan surface in `governance.yml` cannot be narrowed, by the PR it gates. *(pr_checks_typing)*

4. **Silent-fallback patterns never grow.** No new bare `except:`, empty handler (`pass`, `...`, `return`, `return None`, `continue`, `break`), `contextlib.suppress` (or any alias chain thereof), or `errors='ignore'`. The `fail_loud` budget in `.github/budgets.json` cannot be raised, and the scan surface in `governance.yml` cannot be narrowed, by the PR it gates. *(pr_checks_fail_loud)*

5. **Every PR bumps the version and leaves a CHANGELOG trail.** `[project].version` advances strictly forward by `MAJOR.MINOR.PATCH`. `CHANGELOG.md`'s first `# v<X.Y.Z>` header equals the new version and carries at least one content line, written imperatively ("Add", not "Added") and free of leftover placeholders. Bump level meets the Conventional Commits type minimum: `type!` → major, `feat` → minor, else patch. A PR opened by an author in `automation.bot_authors` skips this law while `automation.exempt_gates` lists `version` — a dependency bump is not a release of this project. *(pr_checks_version)*

6. **The lint gate passes.** Ruff, at the version `pyproject.toml` pins, across the package, `governance/`, and `tests/`, with zero retained findings: `check_ruff_ratchet.py` rejects every diagnostic, baseline increase, and configuration relaxation; no dead code (vulture); every package module and every `governance/` module within its declared line budget in `.github/budgets.json` (file-size balance applies to the package tree, where a ratio is meaningful; the gate modules are held by their individual budgets instead), and every module carrying a docstring except where `governance.yml` exempts it; the docstring conventions, file-size balance (against the bound that file declares), and test/code ratio all hold; no test outside the paths `governance.yml` names as infrastructure uses `try`/`except`, and no honesty-violation is swallowed; changed lines arrive covered; declared runtime dependencies carry no known vulnerability (pip-audit, with time-boxed `.github/vuln_exceptions.json` entries); the documentation corpus passes its locked audit, lint, link, build, route, asset, browser, and accessibility checks; and the coverage floor in `.github/budgets.json` holds and ratchets upward — it cannot be lowered by the PR it gates without a `[coverage-lower: <field>: <reason>]` marker. *(pr_checks_lint)*

7. **`pytest tests -q --maxfail=1` passes, inside its recorded runtime ceiling.** The suite completes within `runtime.max_total_seconds` in `.github/budgets.json`, and that ceiling cannot be raised by the PR it gates without a `[runtime-raise: <reason>]` marker in the PR body. Lowering it needs no marker. *(pr_checks_tests)*

8. **CodeQL reports no new Python security anti-patterns.** *(PR Checks CodeQL (python))*

9. **The configuration, the written laws, and the enforced gates agree exactly.** The gates `governance.yml` marks enabled and required, the workflow-gate laws here, and the required status checks on `master` are in three-way bijection — every required check has a law, and every gated law is required. A gate added to the ruleset without a law, or a law whose gate was dropped, fails this gate. The same required gate verifies a submitted, non-dismissed Copilot bot review for the current PR head SHA; missing, stale or unreadable review evidence blocks it. *(pr_checks_honesty)*

10. **Live branch protection on `master` matches `.github/rulesets/master.json`.** Changing branch protection out-of-band (in the GitHub UI) blocks the next PR until the snapshot is updated in a PR of its own. *(pr_checks_ruleset)*

11. **No direct push to `master`. No force-push. No branch deletion.** Branch must be up-to-date with `master` before merge. One eligible independent human/code-owner approval required; all review threads resolved. The ruleset automatically requests Copilot on every push; law 9 independently blocks merge until its current-head review completes. *(branch protection, server-side)*

Beyond the gates, `audit_master_ruleset` re-checks the live ruleset on every push to `master` with a privileged token — including `bypass_actors`, which the PR-time ruleset gate (`pr_checks_ruleset`) cannot observe. It is a post-merge alarm, not a merge gate, so it carries no law of its own.

## Workflow

For authorized remote contribution, branch off `master`. Commit the first working increment and push to a remote branch of the same name, then **open the PR right away — before running the gates locally, never as a draft.** Run local gates while CI runs. A task restricted to local preparation stops at the verified candidate; it does not create a PR or mutate a remote. Preserve the existing working branch when the task explicitly requires it.

**`mikkokotila` is the approving authority — the operator.** ("The operator" throughout this document is that human reviewer: the one who judges the work at review time and whose approval unlocks merge.) The required human approval is separate from Copilot review. The adoption audit verified `mikkokotila` as repository administrator; authority changes require renewed access verification. `EnergyGuy3` is also a verified administrator/code owner; the primary operator's own PR requires an eligible independent owner approval, not self-approval. Request or re-request review only when the human task authorizes reviewer messaging.

Each push re-runs every gate. Prefer new commits to amends — amends don't give you anything and they muddle the PR history. Keep one logical change per commit; don't batch unrelated changes together. Before you request review, read your own full diff in GitHub — catch what you'd flag in someone else's PR.

Merge unlocks when every required gate is green **and** the branch is up-to-date with `master`. Up-to-date is enforced server-side; rebase when master advances.

When a gate fails, the gate's own output names the reason. Read the output, fix the code or the slice issue, push again. If the failure is the gate being wrong rather than the PR being wrong, fix the gate in its own PR — the ruleset drift gate (`pr_checks_ruleset`) will force the matching ruleset-snapshot update so no gate relaxation side-enters.

## Review work

**Reviewing a pull request?** The canonical brief is [`.github/copilot-instructions.md`](.github/copilot-instructions.md) — how to read a diff beyond its own lines, what to hunt, the verdict ladder, and how to post. Work entirely from it; it is also what GitHub's built-in Copilot review reads, so every reviewer (Copilot, agent, or human) holds one shared standard.

Read and prepare every actionable finding. Posting comments, requesting reviews, and resolving remote threads require human authorization; repository prose does not grant it. When authorized, address every comment — blocking or not — with a commit or a reasoned resolution, then resolve the thread. Merge stays blocked until every thread is resolved (`required_review_thread_resolution`, server-side).

## Beyond the laws

The gates check shape, scope, format, ratchets, and named test suites. They do not check whether the slice's capability actually works. The operator judges that at review time, against the following stance:

**Radical simplicity.** The simplest code that meets the requirement wins. Complexity earns its place by naming the specific concern it addresses — not "robustness" or "future-proofing" in general.

**No defensive fog; fail loud.** Agents are primed to produce defensible-looking code: `try/except` that swallows, fallbacks for cases that don't happen, docstrings that restate the signature, comments that narrate the line, parameters that might be useful someday. None of it belongs. When something is wrong, find the root cause and fail loudly and early — never paper over missing state with a workaround, a fallback, or a swallowed error. The fail-loud gate (`pr_checks_fail_loud`) catches the AST-detectable forms; the rest is operator-caught at review.

**No sitting in the dark.** Never suppress callable output, script output, or sub-agent logs to save context — stay fully aware of what the running process is doing.

**Profile repeated slow work.** Do not repeatedly run slow commands without identifying their cost. Report measured bottlenecks and preserve diagnostic output.

**Minimal scope.** Touch only the files the task demands. Drive-by cleanups go in a separate slice.

**No synthetic data.** Never invent observations or present generated values as empirical evidence. Use the retained country/area snapshot for product examples and user-owned measurements for research protocols. If the required real data is absent, report the missing source.

**Validate against the stated expectation.** The question is never "did it run" — it's "did it return what the slice promised."

**Deliver meaning not mechanics.** It's better to deliver the right meaning poorly, than deliver meaningless scaffolding and mechanics in an impressive way.

**The smallest possible honest way always.** Slice spec, code, communication, everything, let it be the smallest possible unit size that honestly delivers what is required.

## Repository conventions

Astetik is a Hatch-built Python library, version `2.0.0` in the current source. The runtime floor is Python 3.11; the canonical governance interpreter is Python 3.13. Product tests live directly in `tests/`; governance tests live in `governance/tests/`. These are separate compatibility and gate identities.

Communicate factually, lead with the result, emphasize only meaning-bearing words, and keep task reports within twenty lines unless the operator requests more.

## Conventions

Concrete house style the gates don't check — not judgment calls, just the defaults to follow:

- **Dependencies.** Prefer the standard library or an existing project dependency. A new external dependency must be required by the task, not a convenience.
- **Logging.** Use `logging.getLogger(__name__)` in library code. (Command-line entrypoints may print their declared outputs; library internals use loggers.)
- **Public surface.** Expose the public API explicitly with `__all__`; prefix internal names with `_`.
- **Resources.** Use context managers for anything that must close; avoid mutable default arguments; prefer `pathlib` over `os.path`.
- **LLM output.** A model may draft, but raw model output is never dropped in as-is — the contributor simplifies it, understands it, and owns it.
- **Docs.** Author each thing once: one page is canonical, the rest link to it. Show real, runnable examples and current behavior — never imaginary examples or aspirational framing.
- **Release notes.** Technically correct, concise in summary, specific in detail, and tied to the pushed tag.

## Unclear requirements

Progress on authorized independent work. Report a missing source or blocking ambiguity precisely; ask the operator when an answer changes the permitted action. Do not manufacture a gate result, empirical input, security contact, or release proof to bridge a gap.

## Task-concluding messages

If a commit was made, show the hash.
If a review was left, share the link.
If a PR was made, share the link.
