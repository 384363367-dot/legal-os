# Legal OS v0.7.0 Upgrade Report

**Status:** Released Public Prerelease
**Date:** 2026-08-24  
**Target repository:** `384363367-dot/legal-os`  
**Baseline principle:** GitHub `main`/v0.6.2 repository governance is the repository baseline; the 2026-08-20 local snapshot is used only as a source of newer Skill/runtime content; v0.7.0 research capabilities are applied as controlled increments.

## 1. Why this package was rebuilt

An earlier v0.7.0 package was rejected during self-audit because it incorrectly treated a local installed-Skill snapshot as a complete GitHub source tree. That could have removed or weakened repository documentation, regression tests, manifest/schema constraints, CI controls and public/private safeguards. This RC was rebuilt from a repository-level baseline and does **not** reuse that packaging method.

The superseded package `LegalOS-v0.7.0-GitHub.zip` must not be uploaded.

## 2. Architectural result

v0.7.0 keeps the existing T-01 through T-12 route namespace and the single-primary-workflow rule. The public Skill inventory becomes 14:

- `legal-os-unified-intake`
- `legal-os-contract`
- `legal-os-litigation`
- `legal-os-correspondence`
- `legal-os-business-communication`
- `legal-os-data-verification`
- `legal-os-file-delivery`
- `legal-os-reporting-presentation`
- `legal-os-matter-memory`
- `legal-os-template-runtime`
- `legal-quality-gate`
- `cn-case-hub`
- `cn-law-hub`
- `legal-os-learning-maintenance`

No new T-route was created. T-05 is a research family with deterministic subtype dispatch:

- `current-law-research` → `cn-law-hub`
- `case-research` → `cn-case-hub`

When legal/case research supports a contract, litigation or other substantive matter, the substantive workflow remains the single primary route and T-05 remains auxiliary.

## 3. `cn-case-hub`: first-party case research redesign

The Skill name is retained for route and invocation compatibility, but the workflow is upgraded into a Legal OS-maintained case-research module.

### New/existing matter entry

- New matters separate confirmed facts, unverified facts, parties/legal relationships and the legal question before searching.
- Existing matters first freeze the latest verified procedural posture, latest judgment/order, new evidence and latest opposing position.
- New verified procedural/judgment information supersedes an older value as the current-state authority; old values remain historical timeline data.

### Search and source controls

- Three search layers: legal issue, decisive facts and adjudicative/legal basis.
- Multi-round calibration records court wording, omitted angles and next-round search language.
- Source weight is explicit; case count cannot substitute for source authority or factual similarity.
- Search snippets, model memory and secondary summaries are leads only unless opened and verified against an acceptable source.
- Login, CAPTCHA, robots, rate-limit or access restrictions must not be bypassed.

### Dual-axis case classification

Relevance and outcome direction are separated:

- Relevance: `A` core / `B` important / `C` general / `D` exclude.
- Direction: `+` supportive / `±` conditional or mixed / `0` neutral / `-` adverse.
- Combined matrix examples: `A+`, `A-`, `B+`, `B-`.

An `A-` case is high-value adverse authority and must not be hidden or downgraded merely because its direction is unfavorable.

### Decision-fork variables and strategy handoff

The Skill identifies facts or conditions that explain why materially similar cases diverge. The report converts those variables into evidence gaps and a handoff to the substantive workflow.

The Skill uses “检索样本支持比例” only when a sample distribution is described; it does not call a search sample a “胜诉率”.

### Backward compatibility

The v0.6 record model (`similarity`, `direction`) remains accepted. v0.7 adds optional matrix and decision-variable fields rather than invalidating existing saved case records.

## 4. `cn-law-hub`: first-party current-law research

`cn-law-hub` is rebuilt as a Legal OS-maintained research workflow. It handles:

- source and issuing-body verification;
- authority type and hierarchy;
- effective/repealed/amended status;
- amendment and version chains;
- exact article/pinpoint identification;
- event-time and procedure-time temporal applicability;
- conflicts or unresolved authority status;
- treaties as a distinct authority type, with official treaty-source and status checks.

It contains standard-library query/validation utilities and does not require a third-party Skill, MCP or commercial database SDK as an installation prerequisite.

Third-party crawler implementations that existed in a local historical snapshot were not included in this package. Banned legacy crawler names are checked by the first-party boundary gate.

“First-party” here describes the maintained workflow and shipped code. It does not mean Legal OS owns the legislation databases or official source websites it consults.

## 5. `legal-os-litigation`: research-to-strategy handoff

Litigation remains the primary merits/strategy workflow. It does not duplicate the research modules. Its new handoff is:

`decision-fork variable → matter fact → supporting/adverse evidence → evidence_gap → opponent attack → evidence action → argument/procedural action`

The workflow must explain how a high-relevance adverse case is distinguishable or carry it as an unresolved risk. Research therefore changes evidence and litigation action rather than remaining a citation appendix.

## 6. Unified Intake and routing changes

- T-05 dispatches current law and cases to separate first-party Skills.
- T-12 points to `legal-os-learning-maintenance`.
- Exactly one primary route remains mandatory.
- Research modules are auxiliaries when they are used inside a substantive matter.
- The complete invocation policy covers all 14 distributed Skills and remains aligned with `agents/openai.yaml`.

## 7. Learning and maintenance

`legal-os-learning-maintenance` is included as a public governance Skill and receives an `agents/openai.yaml` interface. Its purpose is controlled, net-new-only maintenance:

- record reusable deltas rather than restating existing rules;
- distinguish reusable rules from matter-specific facts;
- support periodic review and critical hotfix paths;
- preserve rollback and explicit approval for durable authority changes.

## 8. Template and Office runtime repair

The package contains 24 registered public Office templates. The missing memory candidate-diff registration found during audit was restored:

- template ID: `MEMORY-CANDIDATE-DIFF-V1.12`
- document type: `memory-update-candidate-diff`
- asset: `skills/legal-os-matter-memory/assets/templates/记忆更新候选差异表_标准模板.docx`

All 24 template assets are hash-bound in the catalog. The resolver can now resolve `memory-update-candidate-diff` instead of incorrectly returning `TEMPLATE_REQUIRED`.

The source-first Office QA rule remains controlling. Ordinary and formal legal DOCX both default to no rendering unless the user explicitly requests visual/PDF/print/font verification, the deliverable is inherently visual, or structured source inspection identifies a concrete layout risk. “Formal”, “external” or “directly usable” status alone is not a visual-check trigger; an explicit no-render instruction is a hard stop.

## 9. GitHub repository governance preserved/restored

This RC preserves the repository controls that the rejected package had accidentally weakened:

- strict `legalos.manifest.json` and JSON Schema;
- `execution_modes`;
- `public-generic` / `private-controlled` profiles;
- complete `invocation_policy`;
- `template_runtime` contract;
- strict manifest/repository/routing validators;
- pinned GitHub Actions revisions and read-only contents permission;
- dependency check on a clean CI runner;
- public/private boundary and contribution/security documentation;
- historical architecture and workspace documentation;
- historical CHANGELOG entries;
- original regression coverage plus v0.7 tests.

The repository `.gitignore` again excludes ordinary `*.docx`, `*.pdf`, `*.xlsx`, `private/`, `confidential/`, `client-materials/` and `matter-files/`, while allowing the approved public template asset directories.

### Disclosed governance repairs and preserved main artifacts

- The working tree was created from GitHub `main` commit `2468b9b615003fee581316503cd6da394751707a`; the handoff SOURCE was applied only as a controlled increment.
- `docs/plans/2026-07-15-repository-consistency-repair.md` retains the complete GitHub `main` history plan byte-for-byte (SHA-256 `68518b9442bd62cf5bdac35e4c938786476a06a4cbd9624bbac9cd5e9c9d1bf0`). The shortened handoff copy was not used.
- `legal-os-banner.png` retains the original GitHub `main` bytes (1,478,553 bytes; Git blob `16a43b80e86098b387a285c4afac46d7d1b47cdb`; SHA-256 `0c92cbc57c2075ffa7d6abab6661ade15afde659432bbd8db2698839f745a375`). The handoff placeholder was not used.
- The GitHub `main` `LICENSE` omitted a paragraph from the Apache License 2.0 body. v0.7.0 intentionally repairs that file by using the Apache Software Foundation official `LICENSE-2.0.txt` byte-for-byte. The repaired file SHA-256 is `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`. This is an explicit governance fix, not a silent replacement.
- `OPEN_SOURCE_BOUNDARY.md` is intentionally changed to disclose the first-party maintenance and dependency boundary for `cn-case-hub` and `cn-law-hub`, distinguish external research sources from bundled code dependencies, and prohibit bypass of source access controls.
- The litigation handoff term is normalized across the Skill, reference and reports as `argument/procedural action`.

## 10. Installer repair

The root installer is designed for the GitHub source layout:

- default target: `${CODEX_HOME:-$HOME/.codex}/skills`;
- `--dry-run` for a no-change preview;
- no silent overwrite;
- `--replace` backs up the old Skill before replacement;
- `--setup-runtime` installs from repository-root `requirements.txt`;
- no dependency on an unpublished or local-snapshot `runtime/` directory;
- macOS Bash 3.2/BSD `find` compatibility, with no GNU-only `mapfile` or `find -printf` dependency;
- `python3` as the default runtime command, with an explicit `PYTHON` override.

Stale `../runtime/legalos-python` and `runtime/requirements.txt` references were removed from distributed Skill instructions.

## 11. Tests and release discipline

New tests cover:

- T-05 two-Skill dispatch;
- first-party research boundary;
- dual-axis case records and backward compatibility;
- current-law authority record validation;
- official treaty records and invalid authority-type rejection;
- template catalog completeness and missing-template repair;
- installer dry-run / clean install / replacement backup;
- repository and invocation-policy consistency.

Test modules use unique basenames so repository-wide pytest collection does not fail with import mismatch.

Independent release review also removed two public-boundary leaks (an internal personal designation in a script comment and an internal finalization label in a rule heading) and repeated the public privacy/path scan. These strings were documentation metadata only; no legal rule or test expectation was weakened.

The product state is `released` after PR #17 passed GitHub Actions on a clean runner and received final maintainer review. The GitHub release remains marked as a prerelease rather than a stable release.

## 12. Files materially added or changed for v0.7.0

### New first-party research module

- `skills/cn-law-hub/**`

### Major case-research upgrade

- `skills/cn-case-hub/SKILL.md`
- `skills/cn-case-hub/references/output-contract.md`
- `skills/cn-case-hub/references/source-registry.md`
- `skills/cn-case-hub/scripts/build_official_queries.py`
- `skills/cn-case-hub/scripts/validate_case_records.py`
- `skills/cn-case-hub/scripts/check_first_party_boundary.py`
- `skills/cn-case-hub/agents/openai.yaml`

### Litigation / intake / governance integration

- `skills/legal-os-litigation/SKILL.md`
- `skills/legal-os-litigation/references/case-research-handoff.md`
- `skills/legal-os-unified-intake/SKILL.md`
- `skills/legal-os-learning-maintenance/agents/openai.yaml`
- `legalos.manifest.json`
- `schemas/legalos-manifest.schema.json`

### Template/runtime/installation corrections

- `skills/legal-os-template-runtime/references/template-catalog.json`
- `skills/legal-os-contract/references/runtime.md`
- distributed Skill commands with stale local runtime paths
- `install.sh`

### Repository governance/documentation/tests

- `.github/workflows/ci.yml`
- `.gitignore`
- `LICENSE` — disclosed correction to the exact ASF Apache License 2.0 text
- `OPEN_SOURCE_BOUNDARY.md` — disclosed first-party research/dependency boundary expansion
- `README.md`
- `CHANGELOG.md`
- `docs/case-and-law-research-v0.7.md`
- `docs/capability-matrix.md`
- `docs/unified-intake-routing.md`
- `docs/litigation-workspace.md`
- root validators and v0.7 regression/installer tests
- `RELEASE_NOTES_v0.7.0.md`
- `UPGRADE_REPORT_v0.7.0.md`
- `TEST_REPORT_v0.7.0.md`

The following GitHub `main` artifacts are explicitly unchanged:

- `legal-os-banner.png`
- `docs/plans/2026-07-15-repository-consistency-repair.md`

## 13. Release verification

Local verification used an isolated Python 3.12 environment. PR #17 then repeated dependency, repository, routing, first-party-boundary, installer and regression gates on clean GitHub runners; project CI and CodeQL checks passed before merge. This public prerelease does not waive matter-level legal verification or human signoff.
