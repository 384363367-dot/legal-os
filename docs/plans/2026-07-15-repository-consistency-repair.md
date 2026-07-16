# Repository Consistency Repair Implementation Plan

**Goal:** Make the v0.1.0 public repository internally consistent, installable, and automatically verifiable without inventing capabilities that are not published.

**Architecture:** Keep the existing nine public Skills as the supported package. Add an explicit capability matrix for routes that are phases or external dependencies, narrow the contract Skill to the two scripts actually shipped, and add repository-level validation plus synthetic tests in CI.

**Tech Stack:** Markdown, Python 3.12, lxml, unittest, GitHub Actions.

---

### Task 1: Clarify the public capability boundary

**Files:**
- Create: `docs/capability-matrix.md`
- Modify: `README.md`
- Modify: `docs/unified-intake-routing.md`
- Modify: `skills/legal-os-unified-intake/SKILL.md`

**Steps:**
1. Document all T-01 through T-12 routes and identify whether each is a public Skill, a phase inside a Skill, or an external dependency.
2. Remove module-version labels that conflict with repository version v0.1.0.
3. Add a concrete install and first-use path to README.
4. Run the repository validator and expect every referenced local path to resolve.

### Task 2: Remove broken contract execution claims

**Files:**
- Modify: `skills/legal-os-contract/SKILL.md`

**Steps:**
1. Remove references to unpublished `runtime.md`, `minimal_redline.py`, `migrate_change_ledger.py`, and `release_gate.py`.
2. Keep `redline_metrics.py` as diagnostic and `redline_quality_gate.py` as the published deterministic gate.
3. Mark external-final release as requiring an organization-specific gate outside this public package.
4. Verify no local resource reference is broken.

### Task 3: Add dependency and repository validation

**Files:**
- Create: `requirements.txt`
- Create: `scripts/validate_repo.py`
- Create: `tests/test_validate_repo.py`

**Steps:**
1. Declare the runtime dependency used by the DOCX scripts.
2. Validate Skill frontmatter, folder/name agreement, `agents/openai.yaml`, local Markdown links, and backticked `scripts/` or `references/` paths.
3. Write synthetic tests that prove the validator accepts the repository and rejects a broken reference.
4. Run `python -m unittest discover -s tests -v` and expect PASS.

### Task 4: Add synthetic DOCX gate coverage and CI

**Files:**
- Create: `tests/test_redline_quality_gate.py`
- Create: `.github/workflows/ci.yml`

**Steps:**
1. Generate minimal synthetic DOCX packages entirely in the test temporary directory.
2. Assert a valid granular redline passes and an untracked or inconsistent redline fails closed.
3. Configure CI to install dependencies, validate repository structure, and run unittest.
4. Run the same commands locally and expect all checks to pass.

### Task 5: Final verification

**Files:**
- Verify all changed files.

**Steps:**
1. Parse every Python file with `ast.parse`.
2. Run repository validation.
3. Run the full unittest suite.
4. Re-scan for missing local links and unpublished script references.
5. Report the local diff; do not push without separate authorization.
