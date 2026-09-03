#!/usr/bin/env python3
"""Search an article keyword across a bounded set of official laws."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from document_parser import extract_docx_paragraphs, split_into_articles
from download import fetch_detail, get_download_url, parse_detail, search_laws
from research_runtime import OfficialClient, SourceAccessError, SourceBoundaryError


def _article_matches(sections: list[tuple[str, str]], keyword: str, context: int) -> list[dict[str, object]]:
    matched_indices = [index for index, (_, text) in enumerate(sections) if keyword in text]
    output: list[dict[str, object]] = []
    selected: set[int] = set()
    for index in matched_indices:
        for candidate in range(max(0, index - context), min(len(sections), index + context + 1)):
            selected.add(candidate)
    for index in sorted(selected):
        label, text = sections[index]
        output.append({"label": label, "text": text, "is_match": index in matched_indices})
    return output


def search_articles(
    keyword: str,
    *,
    law_keyword: str | None = None,
    search_range: int = 1,
    max_laws: int = 5,
    context: int = 0,
    status: int | None = None,
    offset: int = 0,
    client: OfficialClient | Any | None = None,
) -> dict[str, object]:
    if not keyword.strip():
        raise ValueError("keyword must not be empty")
    active = client or OfficialClient("npc-law")
    page = max(1, offset // max(1, max_laws) + 1)
    raw = search_laws(
        law_keyword or keyword,
        page=page,
        size=max(1, min(max_laws, 100)),
        search_range=search_range,
        status_filter=[status] if status is not None else None,
        client=active,
    )
    rows = raw.get("rows", []) if raw.get("code") in (200, "200") else []
    results: list[dict[str, object]] = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict) or not row.get("bbbs"):
            continue
        law = {"title": row.get("title", ""), "bbbs": row.get("bbbs"), "status": row.get("sxx"), "articles": [], "error": None}
        try:
            info = parse_detail(fetch_detail(str(row["bbbs"]), client=active))
            url = get_download_url(str(row["bbbs"]), "docx", client=active)
            response = active.request("GET", url)
            sections = split_into_articles(extract_docx_paragraphs(response.content))
            law["metadata"] = info
            law["articles"] = _article_matches(sections, keyword, max(0, context))
            law["matched_articles"] = sum(1 for item in law["articles"] if item["is_match"])
        except (SourceAccessError, SourceBoundaryError, ValueError, OSError) as exc:
            law["error"] = {"status": "BLOCKED_BY_SOURCE", "message": str(exc)}
            law["matched_articles"] = 0
        results.append(law)
    return {
        "keyword": keyword,
        "law_keyword": law_keyword or keyword,
        "search_range": "content" if search_range == 2 else "title",
        "offset": offset,
        "max_laws": max_laws,
        "results": results,
        "matched_laws": sum(1 for law in results if law.get("matched_articles", 0)),
        "verification_note": "每个条文仍须回到对应官方详情/全文核验；下载或解析失败保留为 BLOCKED_BY_SOURCE。",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("keyword")
    parser.add_argument("--law", dest="law_keyword")
    parser.add_argument("--range", choices=("title", "content"), default="title")
    parser.add_argument("--max-laws", type=int, default=5)
    parser.add_argument("--context", type=int, default=0)
    parser.add_argument("--status", type=int)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--resume", action="store_true", help="compatibility flag; caller still controls the offset")
    parser.add_argument("--cache-dir")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--rate-limit", choices=("off", "fixed", "adaptive", "auto"), default="auto")
    parser.add_argument("--log-file", metavar="PATH", help="explicit JSON-lines request audit log")
    parser.add_argument("--json", action="store_true")
    return parser


def _rate_value(mode: str) -> float | None:
    return {"off": None, "fixed": 1.0, "adaptive": 1.0, "auto": 2.0}[mode]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    client = OfficialClient(
        "npc-law",
        cache_dir=args.cache_dir,
        no_cache=args.no_cache,
        requests_per_second=_rate_value(args.rate_limit),
        timeout=args.timeout,
        log_file=args.log_file,
    )
    try:
        payload = search_articles(
            args.keyword,
            law_keyword=args.law_keyword,
            search_range=2 if args.range == "content" else 1,
            max_laws=max(1, min(args.max_laws, 100)),
            context=max(0, args.context),
            status=args.status,
            offset=max(0, args.offset),
            client=client,
        )
    except (SourceAccessError, SourceBoundaryError, ValueError, OSError) as exc:
        print(json.dumps({"status": "BLOCKED_BY_SOURCE", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
