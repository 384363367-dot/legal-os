"""Shared command-line behavior for the non-NPC official-source adapters."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from research_runtime import OfficialClient, SourceAccessError, SourceBoundaryError, write_json
from site_adapters import download_source_file, fetch_detail, search_source, write_result_bundle
from source_registry import source_for_id
from source_specs import category_options


def build_parser(source_id: str, description: str) -> argparse.ArgumentParser:
    source = source_for_id(source_id)
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--search", metavar="KEYWORD", help="Search keyword")
    parser.add_argument("--range", choices=("title", "content"), default="title")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--size", type=int, default=20)
    options = category_options(source_id)
    parser.add_argument("--category", choices=options or None)
    parser.add_argument("--year")
    parser.add_argument("--department")
    parser.add_argument("--status", choices=("effective", "invalid", "all"), default="all")
    parser.add_argument("--sort", choices=("score", "date", "title"), default="score")
    parser.add_argument("--max-pages", type=int, default=1)
    parser.add_argument("--info", metavar="URL", help="Fetch one official detail page")
    parser.add_argument("--download", metavar="URL", help="Download an official file")
    parser.add_argument("--output", "-o", metavar="PATH", help="Explicit download or JSON output path")
    parser.add_argument("--output-dir", metavar="DIR", help="Explicit directory for result JSON")
    parser.add_argument("--cache-dir", metavar="DIR", help="Opt-in caller-owned cache directory")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--cache-stats", action="store_true")
    parser.add_argument("--cache-clear", action="store_true")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--rate-limit", choices=("off", "fixed", "adaptive", "auto"), default="auto")
    parser.add_argument("--log-file", metavar="PATH", help="explicit JSON-lines request audit log")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.set_defaults(_source=source)
    return parser


def _rate_value(mode: str) -> float | None:
    return {"off": None, "fixed": 1.0, "adaptive": 1.0, "auto": 2.0}[mode]


def _emit(payload: object, json_mode: bool = True) -> None:
    if json_mode:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    elif isinstance(payload, list):
        for index, row in enumerate(payload, 1):
            print(f"{index}. {row.get('title', '未命名记录')}")
            if row.get("detail_url"):
                print(f"   {row['detail_url']}")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def main_for_source(source_id: str, description: str, argv: list[str] | None = None) -> int:
    parser = build_parser(source_id, description)
    args = parser.parse_args(argv)
    client = OfficialClient(
        source_id,
        cache_dir=args.cache_dir,
        no_cache=args.no_cache,
        requests_per_second=_rate_value(args.rate_limit),
        timeout=args.timeout,
        log_file=args.log_file,
    )
    if args.cache_stats:
        _emit(client.cache.stats() if client.cache else {"entries": 0, "bytes": 0, "cache": "disabled"}, args.json)
        return 0
    if args.cache_clear:
        _emit({"removed": client.cache.clear() if client.cache else 0, "cache": "enabled" if client.cache else "disabled"}, args.json)
        return 0
    try:
        if args.info:
            payload = fetch_detail(args.info, source_id=source_id, client=client)
        elif args.download:
            if not args.output:
                parser.error("--download requires an explicit --output path")
            payload = download_source_file(args.download, args.output, source_id=source_id, client=client)
        elif args.search is not None:
            filters = {
                "category": args.category,
                "year": args.year,
                "department": args.department,
                "status": args.status,
                "sort": args.sort,
                "max_pages": max(1, min(args.max_pages, 20)),
            }
            payload = search_source(
                source_id,
                args.search,
                page=max(1, args.page),
                size=max(1, min(args.size, 500)),
                search_range=args.range,
                filters=filters,
                client=client,
            )
        else:
            parser.print_help()
            return 2
    except (SourceBoundaryError, SourceAccessError, ValueError, OSError) as exc:
        payload = {"status": "BLOCKED_BY_SOURCE", "source_id": source_id, "error": str(exc)}
        _emit(payload, True)
        return 1

    if args.output_dir and isinstance(payload, list):
        output_path = write_json(Path(args.output_dir).expanduser().resolve() / "results.json", payload)
        bundle_path = write_result_bundle(payload, args.output_dir, source_id=source_id, keyword=args.search or "", category=args.category or "")
        payload = {"records": payload, "output": str(output_path), "bundle": str(bundle_path)}
    elif args.output and args.download is None and args.output_dir is None:
        write_json(args.output, payload)
    _emit(payload, args.json or not isinstance(payload, list))
    return 0
