#!/usr/bin/env python3
"""Validate the public README as a product surface, not an internal release log."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


FORBIDDEN_README_MARKERS = (
    "PR #",
    "本地验收",
    "公开边界复核",
    "GitHub Actions",
    "release_status",
    "去身份化",
)


def validate_public_surface(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    readme_path = root / "README.md"
    manifest_path = root / "legalos.manifest.json"
    catalog_path = root / "skills/legal-os-template-runtime/references/template-catalog.json"
    rules_path = root / "docs/public-homepage-and-release-rules.md"

    if not readme_path.is_file():
        return ["README.md: missing"]
    if not manifest_path.is_file():
        return ["legalos.manifest.json: missing"]
    if not catalog_path.is_file():
        errors.append("template catalog: missing")
    if not rules_path.is_file():
        errors.append("docs/public-homepage-and-release-rules.md: missing")

    readme = readme_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    version = str(manifest["product"]["public_version"])
    skills_count = len(manifest["skills"])
    routes_count = len(manifest["routes"])
    template_count = None
    if catalog_path.is_file():
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        template_count = len(catalog.get("templates", []))

    for marker in FORBIDDEN_README_MARKERS:
        if marker in readme:
            errors.append(f"README.md: internal release marker must not appear: {marker}")

    if re.search(rf"v{re.escape(version)}\s+RC", readme, flags=re.IGNORECASE):
        errors.append(f"README.md: stale RC wording for current version v{version}")
    if f"v{version}" not in readme:
        errors.append(f"README.md: current manifest version v{version} is not mentioned")
    if f"Skills-{skills_count}" not in readme and f"{skills_count} 个 Skills" not in readme:
        errors.append(f"README.md: Skills count does not project manifest count {skills_count}")
    if f"routes-{routes_count}" not in readme and f"{routes_count} 条路由" not in readme:
        errors.append(f"README.md: route count does not project manifest count {routes_count}")
    if template_count is not None:
        if f"{template_count} 个标准 Office 模板" not in readme:
            errors.append(
                f"README.md: template count does not project catalog count {template_count}"
            )
    if "public-homepage-and-release-rules.md" not in readme:
        errors.append("README.md: missing link to the homepage/release rules")
    if "当前版本" not in readme:
        errors.append("README.md: missing a current-version section")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_public_surface(root)
    if errors:
        print("Public surface validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Public surface validation: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
