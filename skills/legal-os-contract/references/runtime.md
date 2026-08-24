# Python runtime

Public GitHub source does not require or ship a repository-level private runtime snapshot. Run bundled deterministic scripts with Python 3.12+ and install the repository-root `requirements.txt` in the active environment when needed.

Examples:

```bash
python scripts/redline_quality_gate.py ...
python scripts/redline_metrics.py REDLINE.docx
```

The release/installation package may provide an environment wrapper, but Skill correctness must not depend on an unpublished `runtime/` directory. Do not silently install additional third-party packages beyond the declared repository requirements.
