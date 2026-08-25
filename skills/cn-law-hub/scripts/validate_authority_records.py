#!/usr/bin/env python3
"""Validate current-law authority records using the standard library."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
try:
    from .source_registry import ALL_AUTHORITY_TYPES, validate_official_url
except ImportError:
    from source_registry import ALL_AUTHORITY_TYPES, validate_official_url

STATUSES = {"effective", "amended", "repealed", "expired", "pending", "unresolved"}
VERIFICATION_STATUSES = {
    "verified-source",
    "verified-metadata-only",
    "lead-only",
    "blocked",
}
REQUIRED_FIELDS = {
    "title",
    "authority_type",
    "issuing_body",
    "document_number",
    "promulgated_date",
    "effective_date",
    "status",
    "proposition",
    "source_url",
    "accessed_at",
    "verification_status",
    "limitations",
}


def _unique_list(value: object) -> bool:
    if not isinstance(value, list):
        return False
    try:
        return len(value) == len(set(value))
    except TypeError:
        return False


def validate_record(record: object, index: int) -> list[str]:
    prefix = f"record[{index}]"
    errors: list[str] = []
    if not isinstance(record, dict):
        return [f"{prefix}: must be an object"]

    missing = sorted(REQUIRED_FIELDS - record.keys())
    if missing:
        errors.append(f"{prefix}: missing fields: {', '.join(missing)}")
    if record.get("authority_type") not in ALL_AUTHORITY_TYPES:
        errors.append(f"{prefix}: invalid authority_type")
    if record.get("status") not in STATUSES:
        errors.append(f"{prefix}: invalid status")
    if record.get("verification_status") not in VERIFICATION_STATUSES:
        errors.append(f"{prefix}: invalid verification_status")

    source_url = record.get("source_url")
    if not isinstance(source_url, str) or not source_url.strip():
        errors.append(f"{prefix}: source_url must be a non-empty string")
    elif record.get("verification_status") == "verified-source":
        ok, reason, _ = validate_official_url(source_url, record.get("authority_type"))
        if not ok:
            errors.append(f"{prefix}: {reason}")

    if record.get("status") in {"amended", "repealed", "expired"} and not (
        record.get("superseded_by") or record.get("limitations")
    ):
        errors.append(
            f"{prefix}: changed/ended status requires supersession or limitation information"
        )

    for key in ("limitations", "supersedes", "superseded_by"):
        if key in record and not isinstance(record[key], list):
            errors.append(f"{prefix}: {key} must be an array")
        elif key in record and not _unique_list(record[key]):
            errors.append(f"{prefix}: {key} must not contain duplicate IDs")

    for key in ("promulgated_date", "effective_date", "accessed_at"):
        if key in record and record[key] is not None and not isinstance(record[key], str):
            errors.append(f"{prefix}: {key} must be a date string or null")
    return errors


def main():
 ap = argparse.ArgumentParser()
 ap.add_argument("json_file", type=Path)
 args = ap.parse_args()
 try:
  data = json.loads(args.json_file.read_text(encoding="utf-8"))
 except Exception as exc:
  print(f"ERROR: {exc}", file=sys.stderr)
  return 2
 records = data if isinstance(data, list) else data.get("authorities") if isinstance(data, dict) else None
 if not isinstance(records, list):
  print("ERROR: top level must be an array or object with authorities", file=sys.stderr)
  return 2
 errors = [error for index, record in enumerate(records) for error in validate_record(record, index)]
 if errors:
  print("\n".join(errors), file=sys.stderr)
  return 1
 print(f"OK: {len(records)} authority record(s) validated")
 return 0


if __name__=='__main__':raise SystemExit(main())
