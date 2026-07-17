#!/usr/bin/env python3
"""Validate the Legal OS public manifest and its repository projections."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
EXPECTED_ROUTES = {f"T-{number:02d}" for number in range(1, 13)}
EXPECTED_PROFILES = {"public-generic", "private-controlled"}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _implicit_invocation(agent_file: Path) -> bool:
    text = agent_file.read_text(encoding="utf-8")
    match = re.search(r"^\s*allow_implicit_invocation:\s*(true|false)\s*$", text, re.MULTILINE)
    return match is not None and match.group(1) == "true"


def validate_manifest(root: Path, manifest: dict[str, Any] | None = None) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    manifest_path = root / "legalos.manifest.json"
    schema_path = root / "schemas" / "legalos-manifest.schema.json"

    if not manifest_path.is_file():
        return [f"{manifest_path}: missing public manifest"]
    if not schema_path.is_file():
        errors.append(f"{schema_path}: missing manifest schema")

    try:
        manifest = manifest if manifest is not None else load_json(manifest_path)
    except (json.JSONDecodeError, OSError) as exc:
        return [f"{manifest_path}: invalid JSON: {exc}"]

    required = {
        "$schema", "schema_version", "product", "authority", "profiles",
        "execution_modes", "skills", "routes", "invocation_policy", "quality_gates",
    }
    missing = sorted(required - set(manifest))
    if missing:
        errors.append(f"{manifest_path}: missing required fields {missing}")

    schema_version = manifest.get("schema_version")
    if not isinstance(schema_version, str) or not SEMVER_RE.fullmatch(schema_version):
        errors.append(f"{manifest_path}: schema_version must be SemVer")

    product = manifest.get("product", {})
    public_version = product.get("public_version") if isinstance(product, dict) else None
    if not isinstance(public_version, str) or not SEMVER_RE.fullmatch(public_version):
        errors.append(f"{manifest_path}: product.public_version must be SemVer")

    profiles = manifest.get("profiles", [])
    if not isinstance(profiles, list):
        errors.append(f"{manifest_path}: profiles must be a list")
        profiles = []
    profile_ids = {item.get("id") for item in profiles if isinstance(item, dict)}
    if profile_ids != EXPECTED_PROFILES:
        errors.append(f"{manifest_path}: profiles must be exactly {sorted(EXPECTED_PROFILES)}")
    defaults = [item.get("id") for item in profiles if isinstance(item, dict) and item.get("default") is True]
    if defaults != ["public-generic"]:
        errors.append(f"{manifest_path}: public-generic must be the only default profile")
    public_profile = next(
        (item for item in profiles if isinstance(item, dict) and item.get("id") == "public-generic"), {}
    )
    if public_profile.get("distributed") is not True or public_profile.get("private_overlay") is not False:
        errors.append(f"{manifest_path}: public-generic distribution boundary is invalid")
    private_profile = next(
        (item for item in profiles if isinstance(item, dict) and item.get("id") == "private-controlled"), {}
    )
    if private_profile.get("distributed") is not False or private_profile.get("private_overlay") is not True:
        errors.append(f"{manifest_path}: private-controlled must remain an undistributed overlay")

    skill_items = manifest.get("skills", [])
    manifest_skills = {item.get("name") for item in skill_items if isinstance(item, dict)}
    skills_root = root / "skills"
    repository_skills = {path.name for path in skills_root.iterdir() if path.is_dir()} if skills_root.is_dir() else set()
    if manifest_skills != repository_skills:
        errors.append(
            f"{manifest_path}: Skill inventory mismatch; manifest={sorted(manifest_skills)}, "
            f"repository={sorted(repository_skills)}"
        )

    route_items = manifest.get("routes", [])
    route_ids = {item.get("id") for item in route_items if isinstance(item, dict)}
    if route_ids != EXPECTED_ROUTES:
        errors.append(f"{manifest_path}: routes must be exactly T-01 through T-12")
    for route in route_items:
        if not isinstance(route, dict):
            errors.append(f"{manifest_path}: each route must be an object")
            continue
        executor = route.get("executor", {})
        if not isinstance(executor, dict):
            errors.append(f"{manifest_path}: route {route.get('id')} executor must be an object")
            continue
        skill = executor.get("skill")
        if skill is not None and skill not in manifest_skills:
            errors.append(f"{manifest_path}: route {route.get('id')} references unknown Skill {skill!r}")
        if executor.get("kind") == "external-required" and not route.get("external_dependency"):
            errors.append(f"{manifest_path}: route {route.get('id')} must declare its external dependency")

    policy = manifest.get("invocation_policy", {})
    if set(policy) != manifest_skills:
        errors.append(f"{manifest_path}: invocation policy must cover every and only published Skill")
    for skill_name in sorted(repository_skills):
        expected = policy.get(skill_name, {}).get("allow_implicit_invocation")
        if not isinstance(expected, bool):
            errors.append(f"{manifest_path}: {skill_name} invocation policy must be boolean")
            continue
        agent_file = skills_root / skill_name / "agents" / "openai.yaml"
        if agent_file.is_file() and _implicit_invocation(agent_file) != expected:
            errors.append(f"{agent_file}: implicit invocation contradicts legalos.manifest.json")

    router = manifest.get("authority", {}).get("router")
    if router != "legal-os-unified-intake" or router not in manifest_skills:
        errors.append(f"{manifest_path}: authority.router must be legal-os-unified-intake")

    if isinstance(public_version, str):
        projections = [root / "README.md", root / "CHANGELOG.md", root / "docs" / "capability-matrix.md"]
        for projection in projections:
            if projection.is_file() and f"v{public_version}" not in projection.read_text(encoding="utf-8"):
                errors.append(f"{projection}: does not project manifest version v{public_version}")

    try:
        schema = load_json(schema_path)
        if schema.get("properties", {}).get("$schema", {}).get("const") != manifest.get("$schema"):
            errors.append(f"{schema_path}: schema self-reference does not match manifest")
    except (json.JSONDecodeError, OSError) as exc:
        errors.append(f"{schema_path}: invalid JSON: {exc}")

    return errors
