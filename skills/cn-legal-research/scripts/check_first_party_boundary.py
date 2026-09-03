#!/usr/bin/env python3
"""Check the public research adapter for private paths and hard dependencies."""
from __future__ import annotations

import re
import sys
from pathlib import Path

from source_registry import OFFICIAL_SOURCES, validate_official_url


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_LITERALS = (
    "/Users/",
    "LegalOS_Local",
    "P0_remediation",
    "current_controller_task_id",
    "controller_generation",
    "codex/legal-os-install-receipts",
    "private_overlay",
)
IMPORT_PATTERNS = (
    r"^\s*(?:import|from)\s+(?:requests|urllib3|bs4|beautifulsoup4|selenium|playwright|mcp)\b",
)
INERT_XML_NAMESPACES = {
    "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
}


def validate() -> list[str]:
    errors: list[str] = []
    for source in OFFICIAL_SOURCES:
        ok, reason, _ = validate_official_url(source.official_url)
        if not ok:
            errors.append(f"registry {source.id}: {reason}")
        if not source.official_url.startswith("https://"):
            errors.append(f"registry {source.id}: official_url is not HTTPS")
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.resolve() == Path(__file__).resolve():
            continue
        if path.suffix.lower() not in {".py", ".md", ".yaml", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        relative = path.relative_to(ROOT)
        for literal in FORBIDDEN_LITERALS:
            if literal in text:
                errors.append(f"{relative}: forbidden private literal {literal}")
        if path.suffix.lower() == ".py":
            for pattern in IMPORT_PATTERNS:
                if re.search(pattern, text, flags=re.MULTILINE):
                    errors.append(f"{relative}: hard external dependency import")
            insecure_urls = [
                value for value in re.findall(r"https?://[^\"'\s]+", text)
                if value.startswith("http://") and value not in INERT_XML_NAMESPACES
            ]
            if insecure_urls:
                errors.append(f"{relative}: insecure URL literal")
            if "Path.home()" in text or "~/.codex" in text:
                errors.append(f"{relative}: implicit user/runtime directory")
    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("FIRST_PARTY_BOUNDARY_FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("FIRST_PARTY_BOUNDARY_PASS: public adapter uses standard library and registered HTTPS sources only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
