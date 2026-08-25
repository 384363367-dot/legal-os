#!/usr/bin/env python3
"""Validate the public cn-law-hub source and dependency boundary."""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
LEGACY_CRAWLERS = {
    "court_law_crawler.py",
    "tax_law_crawler.py",
    "moj_law_crawler.py",
    "treaty_crawler.py",
    "mod_law_crawler.py",
    "mee_law_crawler.py",
    "party_law_crawler.py",
}
FORBIDDEN_PRIVATE_LITERALS = (
    "/Users/",
    "/private/",
    "/tmp/",
    "~/.codex",
    "~/.workbuddy",
    "legal-os-law-research",
)

found = sorted(str(path.relative_to(ROOT)) for path in ROOT.rglob("*.py") if path.name in LEGACY_CRAWLERS)
imports = []
private_literals = []
for path in ROOT.rglob("*"):
    if not path.is_file() or path.suffix not in {".py", ".md", ".yaml", ".json"}:
        continue
    if path.resolve() == Path(__file__).resolve():
        continue
    text = path.read_text(encoding="utf-8", errors="ignore")
    for library in ("requests", "selenium", "playwright"):
        if re.search(rf"(^|\n)\s*(?:import\s+{library}\b|from\s+{library}\b)", text):
            imports.append(f"{path.name}:{library}")
    for literal in FORBIDDEN_PRIVATE_LITERALS:
        if literal in text:
            private_literals.append(f"{path.relative_to(ROOT)}:{literal}")

positive = []
for path in [ROOT / "SKILL.md", *(ROOT / "references").glob("*.md")]:
    if not path.exists():
        continue
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        lower = line.lower()
        negative = any(
            marker in lower
            for marker in ("不依赖", "无需", "不得", "不是", "not require", "does not require", "must not require")
        )
        if negative:
            continue
        if ("第三方" in line and "skill" in lower and any(x in line for x in ("必须", "需要安装", "依赖"))) or (
            "mcp" in lower and any(x in line for x in ("必须", "依赖", "需要安装"))
        ):
            positive.append(line.strip())

if found or imports or private_literals or positive:
    print(
        "FIRST_PARTY_BOUNDARY_FAIL",
        {
            "legacy": found,
            "imports": imports,
            "private_literals": private_literals,
            "declared_hard_dependencies": positive,
        },
        file=sys.stderr,
    )
    raise SystemExit(1)
print("FIRST_PARTY_BOUNDARY_PASS: public cn-law-hub has no crawler, private path or hard external runtime dependency")
