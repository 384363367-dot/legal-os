#!/usr/bin/env python3
"""Compute the profile payload inventory used by Legal OS release manifests."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

IGNORED_DIRECTORIES = {"__pycache__", ".venv", ".git"}


def _payload_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for current, directories, filenames in os.walk(root, topdown=True):
        directories[:] = sorted(name for name in directories if name not in IGNORED_DIRECTORIES)
        for filename in filenames:
            path = Path(current) / filename
            if path.suffix.lower() != ".pyc" and path.is_file():
                files.append(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def profile_payload(skills_root: Path) -> dict[str, int | str]:
    """Return skill/file counts and the canonical Skills-only tree hash.

    The tree hash is SHA-256 over sorted relative Skill file paths encoded as
    ``path + NUL + lowercase-file-sha256 + LF``. Paths are relative to the
    supplied Skills directory, allowing each profile to keep its own payload
    inventory and hash while sharing the same identity/version contract.
    """
    root = skills_root.resolve()
    if not root.is_dir():
        raise ValueError("Skills payload directory is missing")

    skill_dirs = sorted(
        (
            path for path in root.iterdir()
            if path.is_dir() and path.name not in IGNORED_DIRECTORIES
        ),
        key=lambda path: path.name,
    )
    files = _payload_files(root)
    digest = hashlib.sha256()
    for path in files:
        relative_path = path.relative_to(root).as_posix()
        file_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_digest.encode("ascii"))
        digest.update(b"\n")

    return {
        "skill_count": len(skill_dirs),
        "file_count": len(files),
        "tree_sha256": digest.hexdigest(),
    }
