#!/usr/bin/env python3
"""Validate the public Legal OS repository without third-party YAML parsers."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

try:
    from scripts.validate_manifest import validate_manifest
except ModuleNotFoundError:  # Support direct execution as scripts/validate_repo.py.
    from validate_manifest import validate_manifest


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(?P<data>.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
RESOURCE_RE = re.compile(r"`((?:scripts|references)/[^`\s]+)`")
SKILL_REFERENCE_RE = re.compile(r"`((?:legal-os|cn-law)-[a-z0-9-]+|legal-quality-gate)`")
INTERNAL_DIRECTIVE_RE = re.compile(r"(?:\bFor (?:Claude|Codex):|superpowers:)", re.IGNORECASE)


def parse_frontmatter(path: Path) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, [f"{path}: missing YAML frontmatter"]

    metadata: dict[str, str] = {}
    for line in match.group("data").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            errors.append(f"{path}: invalid frontmatter line: {line!r}")
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")

    extra = sorted(set(metadata) - {"name", "description"})
    if extra:
        errors.append(f"{path}: unsupported frontmatter keys: {extra}")
    return metadata, errors


def local_target(source: Path, raw_target: str) -> Path | None:
    target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
    if not target or target.startswith("#") or re.match(r"^(?:https?|mailto):", target):
        return None
    target = unquote(target.split("#", 1)[0].split("?", 1)[0])
    return source.parent / target


def validate_repository(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    skills_root = root / "skills"
    skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir()) if skills_root.is_dir() else []
    if not skill_dirs:
        errors.append(f"{skills_root}: no Skill directories found")
    published_skills = {path.name for path in skill_dirs}

    errors.extend(validate_manifest(root))

    for skill_dir in skill_dirs:
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"{skill_dir}: missing SKILL.md")
            continue
        metadata, frontmatter_errors = parse_frontmatter(skill_file)
        errors.extend(frontmatter_errors)
        name = metadata.get("name", "")
        description = metadata.get("description", "")
        if name != skill_dir.name:
            errors.append(f"{skill_file}: name {name!r} does not match folder {skill_dir.name!r}")
        if not NAME_RE.fullmatch(name):
            errors.append(f"{skill_file}: invalid skill name {name!r}")
        if not description:
            errors.append(f"{skill_file}: description is empty")

        agent_file = skill_dir / "agents" / "openai.yaml"
        if not agent_file.is_file():
            errors.append(f"{skill_dir}: missing agents/openai.yaml")
        else:
            agent_text = agent_file.read_text(encoding="utf-8")
            if "interface:" not in agent_text or "default_prompt:" not in agent_text:
                errors.append(f"{agent_file}: missing interface/default_prompt metadata")
            if f"${name}" not in agent_text:
                errors.append(f"{agent_file}: default prompt does not mention ${name}")

        skill_text = skill_file.read_text(encoding="utf-8")
        for match in RESOURCE_RE.finditer(skill_text):
            target = skill_dir / match.group(1)
            if not target.exists():
                errors.append(f"{skill_file}: missing bundled resource {match.group(1)!r}")
        for match in SKILL_REFERENCE_RE.finditer(skill_text):
            dependency = match.group(1)
            if dependency not in published_skills:
                errors.append(f"{skill_file}: unbundled named Skill dependency {dependency!r}")

    for markdown_file in sorted(root.rglob("*.md")):
        text = markdown_file.read_text(encoding="utf-8")
        if INTERNAL_DIRECTIVE_RE.search(text):
            relative_source = markdown_file.relative_to(root)
            errors.append(f"{relative_source}: internal agent instruction found")
        for match in MARKDOWN_LINK_RE.finditer(text):
            target = local_target(markdown_file, match.group(1))
            if target is not None and not target.exists():
                relative_source = markdown_file.relative_to(root)
                errors.append(f"{relative_source}: broken local link {match.group(1)!r}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate_repository(args.root)
    if errors:
        print("Repository validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Repository validation: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
