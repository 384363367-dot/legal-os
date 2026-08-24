# Legal OS v0.7.0 Release Notes

> `v0.7.0` tag 保留该版本发布时的原始 banner；当前 `main` 另有一项已记录的公开首页视觉更新，不改变 v0.7.0 的功能、接口或发布状态。

v0.7.0 upgrades Legal OS from a case-search-plus-external-current-law boundary into a bundled first-party research family while preserving the existing T-01 through T-12 routing architecture.

## Highlights

- `cn-case-hub`: new/existing matter entry, latest-state lock, multi-round official-source research, procedure-chain verification, dual-axis `A/B/C/D × +/±/0/-` classification and decision-fork variables.
- `cn-law-hub`: first-party maintained current-law source/version/effectiveness/article/temporal-applicability workflow without a third-party Skill or crawler runtime dependency.
- Treaty research is a first-class current-authority subtype with official-source and status validation.
- `legal-os-litigation`: research findings now flow into evidence gaps and litigation actions.
- T-05 dispatches case and current-law research to the appropriate bundled Skill while preserving one primary substantive workflow.
- `legal-os-learning-maintenance` becomes the 14th public Skill and T-12 governance executor.
- Repository governance, strict manifest/schema, CI, public/private boundaries and historical regression tests are preserved.
- 24 public Office templates are registered and SHA-256 bound.
- Root installer is GitHub-source aware and no longer depends on a local-snapshot `runtime/` directory.
- Root installer works with the macOS default Bash 3.2/BSD `find` toolchain and defaults to `python3` for optional runtime setup.
- Legal DOCX remains source-first and no-default-render: formal/external/directly usable status alone does not trigger visual QA.

## Disclosed governance repairs

- `LICENSE` is intentionally corrected to the byte-for-byte Apache Software Foundation official Apache License 2.0 text (SHA-256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`). GitHub `main` had omitted one paragraph; this is an explicit v0.7.0 governance repair, not a silent replacement.
- The original GitHub `main` `legal-os-banner.png` and the complete historical `docs/plans/2026-07-15-repository-consistency-repair.md` are preserved byte-for-byte; the handoff placeholder/shortened copies are not used.
- `OPEN_SOURCE_BOUNDARY.md` now expressly records the first-party maintenance/dependency boundary for both research Skills and the no-access-control-bypass rule.
- The litigation research handoff term is normalized to `argument/procedural action`.

## Verification state

Local deterministic checks pass in an isolated Python 3.12 environment, including repository validation, dependency consistency and 93 repository-wide pytest tests (plus 5 passing subtests). PR #17 also passed the repository CI and CodeQL checks on the uploaded commits before merge. See `TEST_REPORT_v0.7.0.md` for the exact test scope.

## Release status

This is a public prerelease, not a stable release. The manifest status is `released`; final legal work remains subject to matter-specific facts, authority verification, quality gates and human signoff.
