#!/usr/bin/env python3
"""Compare public/private release identity without exposing private payload data."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SEMVER_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
ROOT = Path(__file__).resolve().parents[1]


def _release(manifest: Any) -> tuple[str, str] | None:
    if not isinstance(manifest, dict):
        return None
    release = manifest.get("release")
    if not isinstance(release, dict):
        return None
    release_id = release.get("release_id")
    version = release.get("version")
    if not isinstance(release_id, str) or not isinstance(version, str):
        return None
    if not SEMVER_RE.fullmatch(version) or release_id != f"legalos-v{version}":
        return None
    return release_id, version


def validate_release_pair(public_manifest: Any, private_manifest: Any) -> list[str]:
    """Check shared identity/version and each profile id only.

    Private inventory, hashes, paths, and payload fields are intentionally not
    inspected and are never included in returned diagnostics.
    """
    errors: list[str] = []
    public_identity = _release(public_manifest)
    private_identity = _release(private_manifest)

    if public_identity is None:
        errors.append("public release identity is missing or malformed")
    if private_identity is None:
        errors.append("private release identity is missing or malformed")

    public_profile = public_manifest.get("profile") if isinstance(public_manifest, dict) else None
    private_profile = private_manifest.get("profile") if isinstance(private_manifest, dict) else None
    public_profile_id = public_profile.get("profile_id") if isinstance(public_profile, dict) else None
    private_profile_id = private_profile.get("profile_id") if isinstance(private_profile, dict) else None
    if public_profile_id != "public-generic":
        errors.append("public profile id is not public-generic")
    if private_profile_id != "private-controlled":
        errors.append("private profile id is not private-controlled")
    if public_identity is not None and private_identity is not None and public_identity != private_identity:
        errors.append("public and private release identities do not match")
    return errors


def _read_manifest(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--private-manifest",
        required=True,
        type=Path,
        help="path to the private profile manifest; only release identity and profile id are checked",
    )
    parser.add_argument(
        "--public-manifest",
        type=Path,
        default=ROOT / "legalos.manifest.json",
    )
    args = parser.parse_args(argv)

    try:
        public_manifest = _read_manifest(args.public_manifest)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        print("Release pair validation: FAIL\n- public manifest could not be read")
        return 1
    try:
        private_manifest = _read_manifest(args.private_manifest)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        print("Release pair validation: FAIL\n- private manifest could not be read")
        return 1

    errors = validate_release_pair(public_manifest, private_manifest)
    if errors:
        print("Release pair validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Release pair validation: PASS (release identity and profile ids only)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
