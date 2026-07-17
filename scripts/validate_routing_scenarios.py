#!/usr/bin/env python3
"""Validate synthetic Unified Intake decisions against the public manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


RISKS = {"R0", "R1", "R2", "R3"}
GAPS = {"G0", "G1", "G2", "G3"}
MODES = {"route-only", "route-and-run"}
STATUSES = {"routed", "ready", "stopped", "awaiting-authorization"}


def validate_scenarios(manifest: dict[str, Any], scenarios: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    routes = {route["id"]: route for route in manifest["routes"]}

    for index, scenario in enumerate(scenarios):
        label = scenario.get("id", f"scenario-{index}")
        decision = scenario.get("expected_decision", {})
        mode = decision.get("mode")
        primary = decision.get("primary_route")
        auxiliaries = decision.get("auxiliary_routes", [])
        risk = decision.get("risk")
        gap = decision.get("gap")
        status = decision.get("status")

        if mode not in MODES:
            errors.append(f"{label}: invalid execution mode {mode!r}")
        if primary not in routes:
            errors.append(f"{label}: exactly one known primary_route is required")
            continue
        if not isinstance(auxiliaries, list) or len(auxiliaries) != len(set(auxiliaries)):
            errors.append(f"{label}: auxiliary_routes must be a unique list")
            auxiliaries = []
        if primary in auxiliaries:
            errors.append(f"{label}: primary route cannot also be auxiliary")
        unknown_auxiliaries = sorted(set(auxiliaries) - set(routes))
        if unknown_auxiliaries:
            errors.append(f"{label}: unknown auxiliary routes {unknown_auxiliaries}")
        if risk not in RISKS:
            errors.append(f"{label}: invalid risk {risk!r}")
        if gap not in GAPS:
            errors.append(f"{label}: invalid gap {gap!r}")
        if status not in STATUSES:
            errors.append(f"{label}: invalid status {status!r}")

        requested_types = set(scenario.get("intake", {}).get("task_types", []))
        covered_types: set[str] = set()
        for route_id in [primary, *auxiliaries]:
            if route_id in routes:
                covered_types.update(routes[route_id].get("intake_types", []))
        uncovered = sorted(requested_types - covered_types)
        if uncovered:
            errors.append(f"{label}: requested task types are not covered by the decision: {uncovered}")

        flags = set(scenario.get("intake", {}).get("flags", []))
        if "core-conflict" in flags and (gap != "G3" or status != "stopped"):
            errors.append(f"{label}: a core conflict must produce G3/stopped")
        if gap == "G3" and status != "stopped":
            errors.append(f"{label}: G3 must stop execution")
        if mode == "route-only" and status not in {"routed", "stopped"}:
            errors.append(f"{label}: route-only may only return routed or stopped")
        if mode == "route-and-run" and status == "routed":
            errors.append(f"{label}: route-and-run cannot end with routed status")
        if "external-action-requested" in flags and mode == "route-and-run" and status != "awaiting-authorization":
            errors.append(f"{label}: external actions require awaiting-authorization")
        if "high-impact" in flags and risk not in {"R2", "R3"}:
            errors.append(f"{label}: high-impact tasks must be R2 or R3")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--manifest", type=Path, default=root / "legalos.manifest.json")
    parser.add_argument("--scenarios", type=Path, default=root / "tests" / "fixtures" / "unified_intake_scenarios.json")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    scenarios = json.loads(args.scenarios.read_text(encoding="utf-8"))
    errors = validate_scenarios(manifest, scenarios)
    if errors:
        print("Routing scenario validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"Routing scenario validation: PASS ({len(scenarios)} synthetic scenarios)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
