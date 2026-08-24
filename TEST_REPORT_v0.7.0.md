# Legal OS v0.7.0 Test Report

**Build:** v0.7.0 Public Prerelease
**Test date:** 2026-08-24  
**Repository tree tested:** the candidate working tree used to create the RC archive; final archive reverse-extraction results are recorded below after packaging.

## Result summary

The deterministic local release gates passed, subject to the environment limitation stated below.

| Check | Result |
|---|---|
| Repository validator | PASS |
| Manifest/schema/invocation consistency | PASS |
| Synthetic routing scenarios | PASS — 16 scenarios |
| Root unittest suite | PASS — 54 tests |
| Contract bundled suite | PASS — 27 tests |
| Legal quality gate bundled suite | PASS — 9 tests |
| Unified Intake bundled suite | PASS — 3 tests |
| Repository-wide pytest execution | PASS — **93 tests**, plus 5 passing subtests |
| Repository-wide pytest collection | PASS — 93 tests; no duplicate-module import mismatch |
| `cn-case-hub` first-party boundary | PASS |
| `cn-law-hub` first-party boundary | PASS |
| Template catalog | PASS — 24/24 registered assets and SHA-256 bindings |
| Office package structure | PASS — 24 DOCX/XLSX assets readable as OOXML ZIP packages |
| Installer dry-run | PASS |
| Installer macOS Bash 3.2/BSD `find` compatibility | PASS — GNU-only commands removed and regression-tested |
| Installer clean-install test | PASS — 14 Skills |
| Installer `--replace` backup test | PASS |
| ASF Apache License 2.0 byte/hash lock | PASS — SHA-256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |
| Original main banner byte/hash lock | PASS — Git blob `16a43b80e86098b387a285c4afac46d7d1b47cdb` |
| Complete historical plan byte/hash lock | PASS — SHA-256 `68518b9442bd62cf5bdac35e4c938786476a06a4cbd9624bbac9cd5e9c9d1bf0` |
| JSON parsing | PASS |
| YAML parsing | PASS |
| Python AST/compile-level parse | PASS |
| Duplicate test basenames | PASS — none |
| Sensitive/private-pattern scan used for release review | PASS — no known matter identifiers, credentials or absolute user paths found |
| Legacy third-party current-law crawler implementation | PASS — not distributed |
| Package payload manifest | PASS — 151 payload files, each size/mode/SHA-256 recorded |
| Internal `SHA256SUMS.txt` | PASS — 152 entries (151 payload files plus `PACKAGE_MANIFEST.json`) |
| Final ZIP reverse extraction | PASS — fresh directory; `.git` metadata absent |
| Reverse-extracted repository/routing/boundary/template/installer gates | PASS |
| Reverse-extracted unittest suites | PASS — 54 + 27 + 9 + 3 tests |
| Reverse-extracted repository-wide pytest | PASS — 93 tests, plus 5 passing subtests |
| Isolated Python 3.12 `pip check` | PASS — no broken requirements |
| GitHub Actions on uploaded PR commits | PASS — PR #17 project CI and CodeQL checks |

## Commands exercised

Core release checks included:

```bash
python scripts/validate_repo.py
python scripts/validate_routing_scenarios.py
python skills/cn-case-hub/scripts/check_first_party_boundary.py
python skills/cn-law-hub/scripts/check_first_party_boundary.py
./install.sh --dry-run
python -m unittest discover -s tests -v
python -m unittest discover -s skills/legal-os-contract/tests -v
python -m unittest discover -s skills/legal-quality-gate/tests -v
python -m unittest discover -s skills/legal-os-unified-intake/tests -v
pytest -q --collect-only
pytest -q
python -m pip check
```

## Final archive reverse-extraction verification

The package was built with one top-level directory, `LegalOS-v0.7.0-GitHub-RC/`. `PACKAGE_MANIFEST.json` records every repository payload file except the two generated package-control files; `SHA256SUMS.txt` covers every payload file plus the package manifest. The archive-level `.sha256` file covers the ZIP itself.

After the report was updated with the actual worktree and first-pass archive results, the candidate ZIP was rebuilt. That final ZIP was extracted into a new empty directory without using the working tree. The following were re-run from the extracted copy without changing its contents:

- outer ZIP SHA-256 and internal manifest/sum verification;
- repository validator and all 16 routing scenarios;
- both first-party research boundary checks;
- 24-template hash/OOXML integrity tests, including `memory-update-candidate-diff` resolution;
- installer dry-run and the installer clean/replace regression tests;
- root and all bundled unittest suites;
- repository-wide pytest collection and execution;
- official-license, original-banner, complete-plan and litigation-terminology locks.

The reverse-extracted counts remained exactly 54 root tests, 27 contract tests, 9 quality-gate tests, 3 Unified Intake tests and 93 repository-wide pytest tests (plus 5 passing subtests).

## Defects found and corrected during this rebuild

The final green result was not obtained by lowering business rules. The rebuild caught and corrected concrete defects before packaging:

1. The first-party boundary checker initially treated a negative statement such as “does not depend on third-party tooling” as a positive dependency declaration. The parser was corrected so that only an actual hard dependency fails the gate.
2. A v0.7 research test accidentally named its helper method `run`, overriding `unittest.TestCase.run`. The helper was renamed; the production Skill was not weakened.
3. Distributed instructions inherited local-snapshot paths such as `../runtime/legalos-python` and `runtime/requirements.txt`. These were replaced with reproducible repository-level Python/root-requirements commands.
4. The audited missing `memory-update-candidate-diff` template catalog entry was restored and tested.
5. Duplicate test basenames that could cause pytest import mismatch were renamed or converted to unique compatibility entry points.
6. The GitHub `main` license text was found to omit an Apache License 2.0 paragraph. The final file is byte-for-byte identical to the Apache Software Foundation official text and this governance repair is disclosed in the CHANGELOG, upgrade report and Release Notes.
7. A shortened history plan and placeholder banner in the handoff SOURCE were rejected; the complete plan and original GitHub `main` banner remain byte-locked. Litigation terminology and the `OPEN_SOURCE_BOUNDARY.md` disclosure were also normalized and covered by regression tests.
8. The installer used GNU-only `mapfile` and `find -printf`, which fail on the macOS default Bash 3.2/BSD `find` toolchain. Skill discovery was rewritten with a Bash 3-compatible sorted `find -print` loop, and runtime setup now defaults to `python3` with an explicit `PYTHON` override.
9. Two public-boundary strings exposed an internal personal designation/finalization label. They were generalized without changing code behavior, then the privacy and absolute-path scans were repeated.
10. Unified Intake routed treaty research to `cn-law-hub`, but the authority schema and source registry did not yet accept treaties. Treaty authority type, official MFA source requirements, validation and two regression tests were added.
11. A candidate rule would have made formal/external/directly usable DOCX trigger a default visual pass when runtime capability existed. It was rejected as inconsistent with the controlling source-first/no-default-render policy; the final rule requires an explicit visual need or a concrete layout risk.

## Template integrity

The catalog contains 24 entries and each points to an existing asset whose SHA-256 matches the registered value. The previously missing memory template now resolves correctly.

The package-level Office scan also confirmed that every bundled DOCX/XLSX is a readable ZIP package with its expected OOXML core entries.

## First-party research boundary

`cn-case-hub` and `cn-law-hub` run their own boundary checks. The distributed tree does not contain the historical third-party current-law crawler implementations that were present in an older local snapshot. No third-party Skill/MCP/commercial database is an installation prerequisite for either research workflow.

External legislation/case websites remain data sources and can impose their own access restrictions. A source blocked by login, CAPTCHA, permissions, robots or service availability must be recorded as blocked/limited rather than bypassed.

## Privacy and publication scan

Before packaging, the tree was scanned for known matter/user identifiers used in the development context, common API-key/private-key markers and absolute local user paths. No release-blocking hit was found. Public examples remain synthetic or public-authority examples.

This automated scan does not replace maintainer review of the final GitHub diff.

## Dependency verification

`requirements.txt` contains:

```text
lxml==6.1.0
```

Verification used a newly created Python 3.12 virtual environment. `lxml==6.1.0` was installed from the repository requirement, and `python -m pip check` returned `No broken requirements found.` Pytest and PyYAML were installed only as audit tooling and are not runtime requirements.

The repository CI retains `python -m pip check`; GitHub Actions repeated the dependency and repository gates in a clean Python 3.12 runner on PR #17.

## Release decision

**Release decision: LOCAL PASS / REMOTE CI PASS / PUBLIC PRERELEASE.**

The package passed local release review and PR #17 remote CI. The manifest may therefore use `released`, and the exact merged commit may be tagged `v0.7.0` and published as a GitHub prerelease after final merge verification.
