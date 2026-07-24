#!/usr/bin/env python3
"""Validate cn-case-hub JSON case records using only the standard library."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse


OFFICIAL_SUFFIXES = (".court.gov.cn", ".chinacourt.gov.cn")
OFFICIAL_HOSTS = {
    "court.gov.cn",
    "www.court.gov.cn",
    "rmfyalk.court.gov.cn",
    "gongbao.court.gov.cn",
    "wenshu.court.gov.cn",
    "dyjfalk.court.gov.cn",
}
SOURCE_GRADES = {"A1", "A2", "B", "C", "D"}
STATUSES = {
    "verified-source",
    "verified-metadata-only",
    "official-summary",
    "lead-only",
    "blocked",
}
SIMILARITY = {"high", "medium", "low"}
BASE_REQUIRED = {
    "title",
    "source_type",
    "source_grade",
    "verification_status",
    "issuing_body",
    "case_numbers",
    "courts",
    "issues",
    "key_facts",
    "holding",
    "result",
    "direction",
    "similarity",
    "source_url",
    "accessed_at",
    "limitations",
}


def is_official(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return host in OFFICIAL_HOSTS or any(host.endswith(suffix) for suffix in OFFICIAL_SUFFIXES)


def validate(record: object, index: int) -> list[str]:
    prefix = f"record[{index}]"
    if not isinstance(record, dict):
        return [f"{prefix}: must be an object"]

    errors: list[str] = []
    missing = sorted(BASE_REQUIRED - record.keys())
    if missing:
        errors.append(f"{prefix}: missing fields: {', '.join(missing)}")

    if record.get("source_grade") not in SOURCE_GRADES:
        errors.append(f"{prefix}: invalid source_grade")
    status = record.get("verification_status")
    if status not in STATUSES:
        errors.append(f"{prefix}: invalid verification_status")

    url = record.get("source_url")
    if status in {"verified-source", "verified-metadata-only", "official-summary"}:
        if not isinstance(url, str) or not is_official(url):
            errors.append(f"{prefix}: verified/official record requires an official court URL")

    if status == "verified-source":
        for key in ("holding", "result", "accessed_at"):
            if not record.get(key):
                errors.append(f"{prefix}: verified-source requires {key}")

    if status == "official-summary" and not record.get("limitations"):
        errors.append(f"{prefix}: official-summary requires limitations")

    similarity = record.get("similarity")
    if not isinstance(similarity, dict):
        errors.append(f"{prefix}: similarity must be an object")
    else:
        for key in (
            "overall",
            "legal_relationship",
            "issue",
            "key_facts",
            "procedure_and_level",
            "time_and_law",
        ):
            if similarity.get(key) not in SIMILARITY:
                errors.append(f"{prefix}: invalid similarity.{key}")
        if not similarity.get("reason"):
            errors.append(f"{prefix}: similarity.reason is required")

    for key in ("case_numbers", "courts", "issues", "key_facts", "limitations"):
        if key in record and not isinstance(record[key], list):
            errors.append(f"{prefix}: {key} must be an array")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_file", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.json_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    records = payload if isinstance(payload, list) else payload.get("cases") if isinstance(payload, dict) else None
    if not isinstance(records, list):
        print("ERROR: top level must be an array or an object with a cases array", file=sys.stderr)
        return 2
    errors = [error for index, record in enumerate(records) for error in validate(record, index)]
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"OK: {len(records)} case record(s) validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
