#!/usr/bin/env python3
"""Search, inspect, preview and download from the National Laws Database."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from document_parser import detect_numbering, extract_docx_paragraphs, match_article_query, split_into_articles
from research_runtime import OfficialClient, SourceAccessError, SourceBoundaryError, write_json
from source_registry import official_source_for_url


BASE_URL = "https://flk.npc.gov.cn"
STATUS_LABELS = {1: "已废止", 2: "已修改", 3: "现行有效", 4: "尚未生效"}


def sxx_to_str(code: object) -> str:
    try:
        return STATUS_LABELS.get(int(code), "未标注")
    except (TypeError, ValueError):
        return str(code or "未标注")


def _active_client(client: OfficialClient | Any | None, **kwargs: object) -> OfficialClient | Any:
    return client or OfficialClient("npc-law", **kwargs)


def search_laws(
    keyword: str,
    *,
    page: int = 1,
    size: int = 20,
    search_range: int = 1,
    search_type: int = 2,
    status_filter: list[int] | None = None,
    client: OfficialClient | Any | None = None,
) -> dict[str, object]:
    payload = {
        "searchRange": search_range,
        "sxrq": [],
        "gbrq": [],
        "sxx": status_filter or [],
        "searchType": search_type,
        "xgzlSearch": False,
        "searchContent": keyword,
        "orderByParam": {"order": "-1", "sort": ""},
        "flfgCodeId": [],
        "zdjgCodeId": [],
        "gbrqYear": [],
        "pageNum": page,
        "pageSize": size,
    }
    response = _active_client(client).request(
        "POST",
        f"{BASE_URL}/law-search/search/list",
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8", "Referer": f"{BASE_URL}/search"},
    )
    return response.json()


def fetch_detail(bbbs_id: str, *, client: OfficialClient | Any | None = None) -> dict[str, object]:
    response = _active_client(client).request(
        "GET",
        f"{BASE_URL}/law-search/search/flfgDetails",
        params={"bbbs": bbbs_id},
    )
    return response.json()


def parse_detail(data: dict[str, object]) -> dict[str, object]:
    if not data or data.get("code") not in (200, "200"):
        return {}
    item = data.get("data") if isinstance(data.get("data"), dict) else {}
    oss = item.get("ossFile") if isinstance(item.get("ossFile"), dict) else {}
    def path_url(key: str) -> str | None:
        value = oss.get(key)
        return f"{BASE_URL}/{str(value).lstrip('/')}" if value else None
    status = item.get("sxx", 0)
    return {
        "bbbs": item.get("bbbs", ""),
        "title": item.get("title", ""),
        "category": item.get("flxz", ""),
        "authority": item.get("zdjgName", ""),
        "publish_date": item.get("gbrq", ""),
        "effective_date": item.get("sxrq", ""),
        "status_code": status,
        "status_str": sxx_to_str(status),
        "word_url": path_url("ossWordPath"),
        "pdf_url": path_url("ossPdfPath"),
        "word_ofd_url": path_url("ossWordOfdPath"),
        "pdf_ofd_url": path_url("ossPdfOfdPath"),
        "raw": item,
    }


def get_download_url(
    bbbs_id: str,
    fmt: str = "docx",
    *,
    client: OfficialClient | Any | None = None,
) -> str:
    response = _active_client(client).request(
        "GET",
        f"{BASE_URL}/law-search/download/pc",
        params={"format": fmt, "bbbs": bbbs_id},
        headers={"Referer": f"{BASE_URL}/detail?id={bbbs_id}"},
    )
    data = response.json()
    if data.get("code") not in (200, "200"):
        raise SourceAccessError(f"download endpoint returned {data.get('msg', 'an error')}")
    body = data.get("data") if isinstance(data.get("data"), dict) else {}
    url = body.get("url")
    if not isinstance(url, str) or not url:
        raise SourceAccessError(f"download endpoint returned no URL for format={fmt}")
    if official_source_for_url(url) is None:
        raise SourceBoundaryError("download endpoint returned an unregistered URL")
    return url


def download_file(
    url: str,
    output_path: str | Path | None = None,
    *,
    client: OfficialClient | Any | None = None,
) -> str:
    if output_path is None:
        raise ValueError("an explicit output path is required for downloads")
    source = official_source_for_url(url)
    if source is None:
        raise SourceBoundaryError("download URL is not a registered HTTPS official URL")
    active = client or OfficialClient(source.id)
    report = active.download(url, output_path)
    print(f"Downloaded: {report['path']} ({report['bytes']} bytes)")
    return str(report["path"])


def collect_search_urls(
    data: dict[str, object],
    fmt: str = "docx",
    *,
    client: OfficialClient | Any | None = None,
) -> list[dict[str, object]]:
    rows = data.get("rows", []) if data.get("code") in (200, "200") else []
    output: list[dict[str, object]] = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, dict):
            continue
        bbbs = row.get("bbbs")
        item = {
            "bbbs": bbbs,
            "title": row.get("title", ""),
            "category": row.get("flxz", ""),
            "authority": row.get("zdjgName", ""),
            "publish_date": row.get("gbrq", ""),
            "effective_date": row.get("sxrq", ""),
            "status_code": row.get("sxx"),
            "status_str": sxx_to_str(row.get("sxx")),
            "format": fmt,
            "url": None,
            "error": None,
        }
        try:
            item["url"] = get_download_url(str(bbbs), fmt, client=client)
        except Exception as exc:  # A row-specific signed URL failure should remain visible.
            item["error"] = str(exc)
        output.append(item)
    return output


def _download_docx_text(bbbs_id: str, *, client: OfficialClient | Any | None = None) -> tuple[list[str], dict[str, object]]:
    raw = fetch_detail(bbbs_id, client=client)
    info = parse_detail(raw)
    if not info:
        raise SourceAccessError(f"cannot fetch detail for {bbbs_id}")
    url = get_download_url(bbbs_id, "docx", client=client)
    response = _active_client(client).request("GET", url)
    return extract_docx_paragraphs(response.content), info


def preview_law(bbbs_id: str, *, client: OfficialClient | Any | None = None) -> dict[str, object]:
    paragraphs, info = _download_docx_text(bbbs_id, client=client)
    articles = split_into_articles(paragraphs)
    numbering = detect_numbering(paragraphs)
    payload = {
        "title": info.get("title", ""),
        "category": info.get("category", ""),
        "authority": info.get("authority", ""),
        "publish_date": info.get("publish_date", ""),
        "status": info.get("status_str", "未标注"),
        "paragraph_count": len(paragraphs),
        "article_count": sum(1 for label, _ in articles if label != "前言"),
        "numbering": numbering,
        "articles": [{"label": label, "preview": text[:180]} for label, text in articles[:20]],
    }
    return payload


def query_article(
    bbbs_id: str,
    query: str | None = None,
    grep: str | None = None,
    *,
    client: OfficialClient | Any | None = None,
) -> dict[str, object]:
    paragraphs, info = _download_docx_text(bbbs_id, client=client)
    articles = split_into_articles(paragraphs)
    if not query and not grep:
        raise ValueError("query_article requires query or grep")
    matches = []
    for label, text in articles:
        if grep and grep in text:
            matches.append({"label": label, "text": text})
        elif query and (match_article_query(query, label) or query in text):
            matches.append({"label": label, "text": text})
    return {"title": info.get("title", ""), "query": query, "grep": grep, "matches": matches}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", nargs="?", help="explicit official file URL; --output is required")
    parser.add_argument("--search", metavar="KEYWORD")
    parser.add_argument("--range", choices=("title", "content"), default="title")
    parser.add_argument("--size", type=int, default=20)
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--status", help="NPC status code: 1=废止, 2=修改, 3=有效, 4=未生效")
    parser.add_argument("--exact", action="store_true")
    parser.add_argument("--info", metavar="BBBS")
    parser.add_argument("--download", metavar="BBBS")
    parser.add_argument("--format", choices=("docx", "pdf", "ofd"), default="docx")
    parser.add_argument("--preview", metavar="BBBS")
    parser.add_argument("--article", nargs="+", metavar="BBBS_OR_QUERY", help="BBBS followed optionally by an article query")
    parser.add_argument("--grep", metavar="KEYWORD")
    parser.add_argument("--urls-only", action="store_true")
    parser.add_argument("--output", "-o", metavar="PATH", help="explicit download/result output path")
    parser.add_argument("--output-dir", metavar="DIR", help="explicit directory for search JSON")
    parser.add_argument("--cache-dir", metavar="DIR")
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--cache-stats", action="store_true")
    parser.add_argument("--cache-clear", action="store_true")
    parser.add_argument("--rate-limit", choices=("off", "fixed", "adaptive", "auto"), default="auto")
    parser.add_argument("--timeout", type=int, default=30)
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
        if args.cache_stats:
            payload = client.cache.stats() if client.cache else {"entries": 0, "bytes": 0, "cache": "disabled"}
        elif args.cache_clear:
            payload = {"removed": client.cache.clear() if client.cache else 0, "cache": "enabled" if client.cache else "disabled"}
        elif args.url:
            if not args.output:
                raise ValueError("an explicit --output path is required for direct URL downloads")
            payload: object = {"download": download_file(args.url, args.output, client=client)}
        elif args.info:
            payload = parse_detail(fetch_detail(args.info, client=client))
        elif args.download:
            if not args.output:
                raise ValueError("--download requires an explicit --output path")
            target_url = get_download_url(args.download, args.format, client=client)
            payload = {"download": download_file(target_url, args.output, client=client)}
        elif args.preview:
            payload = preview_law(args.preview, client=client)
        elif args.article:
            article_id = args.article[0]
            article_query = args.article[1] if len(args.article) > 1 else None
            payload = query_article(article_id, query=article_query, grep=args.grep, client=client)
        elif args.search is not None:
            raw = search_laws(
                args.search,
                page=max(1, args.page),
                size=max(1, min(args.size, 500)),
                search_range=2 if args.range == "content" else 1,
                search_type=1 if args.exact else 2,
                status_filter=[int(args.status)] if args.status and args.status.isdigit() else None,
                client=client,
            )
            payload = collect_search_urls(raw, args.format, client=client) if args.urls_only else raw
            if args.output_dir:
                write_json(Path(args.output_dir) / "search.json", payload)
        else:
            build_parser().print_help()
            return 2
    except (SourceBoundaryError, SourceAccessError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BLOCKED_BY_SOURCE", "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json or isinstance(payload, (dict, list)) else payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
