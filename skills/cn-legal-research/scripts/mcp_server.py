#!/usr/bin/env python3
"""Optional dependency-free JSON-RPC stdio interface for the public adapter."""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from article_search import search_articles
from download import preview_law, query_article
from region_classifier import classify_search_results
from research_runtime import OfficialClient, SourceAccessError, SourceBoundaryError
from site_adapters import download_source_file, fetch_detail, search_source
from source_registry import official_source_for_url, registry_payload, source_for_id, validate_official_url
from validate_authority_records import validate_record


TOOLS = [
    {
        "name": "list_official_sources",
        "description": "List registered official-source metadata without fetching external content.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "validate_official_url",
        "description": "Check whether a URL is HTTPS and belongs to a registered official source.",
        "inputSchema": {
            "type": "object",
            "required": ["url"],
            "properties": {"url": {"type": "string"}, "authority_type": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "search_official_source",
        "description": "Search one registered official source with a bounded result window.",
        "inputSchema": {
            "type": "object",
            "required": ["source_id", "keyword"],
            "properties": {
                "source_id": {"type": "string"},
                "keyword": {"type": "string"},
                "page": {"type": "integer", "minimum": 1},
                "size": {"type": "integer", "minimum": 1, "maximum": 100},
                "range": {"type": "string", "enum": ["title", "content"]},
                "category": {"type": "string"},
                "year": {"type": "string"},
                "department": {"type": "string"},
                "status": {"type": "string"},
                "sort": {"type": "string"},
                "max_pages": {"type": "integer", "minimum": 1, "maximum": 20},
                "cache_dir": {"type": "string"},
                "no_cache": {"type": "boolean"},
                "timeout": {"type": "integer", "minimum": 1},
                "requests_per_second": {"type": ["number", "null"], "minimum": 0},
                "log_file": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "get_official_detail",
        "description": "Fetch one official detail URL after host validation.",
        "inputSchema": {"type": "object", "required": ["url"], "properties": {"url": {"type": "string"}, "source_id": {"type": "string"}, "cache_dir": {"type": "string"}, "no_cache": {"type": "boolean"}, "timeout": {"type": "integer", "minimum": 1}, "requests_per_second": {"type": ["number", "null"], "minimum": 0}, "log_file": {"type": "string"}}, "additionalProperties": False},
    },
    {
        "name": "download_official_file",
        "description": "Download one registered official file to an explicitly supplied path.",
        "inputSchema": {"type": "object", "required": ["url", "output"], "properties": {"url": {"type": "string"}, "output": {"type": "string"}, "source_id": {"type": "string"}, "cache_dir": {"type": "string"}, "no_cache": {"type": "boolean"}, "timeout": {"type": "integer", "minimum": 1}, "requests_per_second": {"type": ["number", "null"], "minimum": 0}, "log_file": {"type": "string"}}, "additionalProperties": False},
    },
    {
        "name": "preview_npc_law",
        "description": "Fetch and preview article headings from one NPC law document.",
        "inputSchema": {"type": "object", "required": ["bbbs"], "properties": {"bbbs": {"type": "string"}, "cache_dir": {"type": "string"}, "no_cache": {"type": "boolean"}, "timeout": {"type": "integer", "minimum": 1}, "requests_per_second": {"type": ["number", "null"], "minimum": 0}, "log_file": {"type": "string"}}, "additionalProperties": False},
    },
    {
        "name": "query_npc_article",
        "description": "Locate one article number or exact text in an NPC law document.",
        "inputSchema": {"type": "object", "required": ["bbbs"], "properties": {"bbbs": {"type": "string"}, "query": {"type": "string"}, "grep": {"type": "string"}, "cache_dir": {"type": "string"}, "no_cache": {"type": "boolean"}, "timeout": {"type": "integer", "minimum": 1}, "requests_per_second": {"type": ["number", "null"], "minimum": 0}, "log_file": {"type": "string"}}, "additionalProperties": False},
    },
    {
        "name": "search_articles",
        "description": "Search a bounded set of official NPC law texts for an article-level keyword.",
        "inputSchema": {"type": "object", "required": ["keyword"], "properties": {"keyword": {"type": "string"}, "law_keyword": {"type": "string"}, "range": {"type": "string", "enum": ["title", "content"]}, "max_laws": {"type": "integer", "minimum": 1, "maximum": 100}, "context": {"type": "integer", "minimum": 0}, "status": {"type": "integer"}, "offset": {"type": "integer", "minimum": 0}, "cache_dir": {"type": "string"}, "no_cache": {"type": "boolean"}, "timeout": {"type": "integer", "minimum": 1}, "requests_per_second": {"type": ["number", "null"], "minimum": 0}, "log_file": {"type": "string"}}, "additionalProperties": False},
    },
    {
        "name": "classify_regions",
        "description": "Classify supplied records by national, provincial or city-level issuing authority without network access.",
        "inputSchema": {"type": "object", "required": ["records"], "properties": {"records": {"type": "array", "items": {"type": "object"}}, "authority_key": {"type": "string"}, "title_key": {"type": "string"}}, "additionalProperties": False},
    },
    {
        "name": "validate_authority_record",
        "description": "Validate one source-locked authority record against the public authority schema and source registry.",
        "inputSchema": {"type": "object", "required": ["record"], "properties": {"record": {"type": "object"}}, "additionalProperties": False},
    },
]


def _text_result(payload: object, *, is_error: bool = False) -> dict[str, object]:
    return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)}], "isError": is_error}


def _client(source_id: str, params: dict[str, Any]) -> OfficialClient:
    configured_rate = params.get("requests_per_second", 2.0)
    rate = None if configured_rate is None else max(0.0, float(configured_rate))
    return OfficialClient(
        source_id,
        cache_dir=params.get("cache_dir"),
        no_cache=bool(params.get("no_cache", False)),
        requests_per_second=rate,
        timeout=int(params.get("timeout", 30)),
        log_file=params.get("log_file"),
    )


def call_tool(name: str, params: dict[str, Any]) -> dict[str, object]:
    if name == "list_official_sources":
        return _text_result(registry_payload())
    if name == "validate_official_url":
        url = str(params.get("url", ""))
        authority_type = params.get("authority_type")
        valid, reason, source_id = validate_official_url(url, str(authority_type) if authority_type else None)
        return _text_result({"valid": valid, "source_id": source_id, "url": url, "reason": reason})
    if name == "search_official_source":
        source_id = str(params["source_id"])
        results = search_source(
            source_id,
            str(params["keyword"]),
            page=max(1, int(params.get("page", 1))),
            size=max(1, min(100, int(params.get("size", 20)))),
            search_range=str(params.get("range", "title")),
            filters={
                "category": params.get("category"),
                "year": params.get("year"),
                "department": params.get("department"),
                "status": params.get("status"),
                "sort": params.get("sort"),
                "max_pages": params.get("max_pages", 1),
            },
            client=_client(source_id, params),
        )
        return _text_result(results)
    if name == "get_official_detail":
        url = str(params["url"])
        source = source_for_id(str(params["source_id"])) if params.get("source_id") else official_source_for_url(url)
        if source is None:
            raise SourceBoundaryError("detail URL is not registered")
        return _text_result(fetch_detail(url, source_id=source.id, client=_client(source.id, params)))
    if name == "download_official_file":
        url = str(params["url"])
        source = source_for_id(str(params["source_id"])) if params.get("source_id") else official_source_for_url(url)
        if source is None:
            raise SourceBoundaryError("download URL is not registered")
        return _text_result(download_source_file(url, str(params["output"]), source_id=source.id, client=_client(source.id, params)))
    if name == "preview_npc_law":
        return _text_result(preview_law(str(params["bbbs"]), client=_client("npc-law", params)))
    if name == "query_npc_article":
        return _text_result(
            query_article(
                str(params["bbbs"]),
                query=str(params["query"]) if params.get("query") is not None else None,
                grep=str(params["grep"]) if params.get("grep") is not None else None,
                client=_client("npc-law", params),
            )
        )
    if name == "search_articles":
        return _text_result(
            search_articles(
                str(params["keyword"]),
                law_keyword=str(params["law_keyword"]) if params.get("law_keyword") is not None else None,
                search_range=2 if params.get("range") == "content" else 1,
                max_laws=max(1, min(100, int(params.get("max_laws", 5)))),
                context=max(0, int(params.get("context", 0))),
                status=int(params["status"]) if params.get("status") is not None else None,
                offset=max(0, int(params.get("offset", 0))),
                client=_client("npc-law", params),
            )
        )
    if name == "classify_regions":
        records = params.get("records")
        if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
            raise ValueError("records must be an array of objects")
        return _text_result(
            classify_search_results(
                records,
                authority_key=str(params.get("authority_key", "authority")),
                title_key=str(params.get("title_key", "title")),
            )
        )
    if name == "validate_authority_record":
        record = params.get("record")
        errors = validate_record(record, 0)
        return _text_result({"valid": isinstance(record, dict) and not errors, "errors": errors})
    raise ValueError(f"unknown tool: {name}")


def handle_message(message: dict[str, Any]) -> dict[str, object] | None:
    method = message.get("method")
    request_id = message.get("id")
    if method in {"notifications/initialized", "notifications/cancelled"}:
        return None
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "legalos-cn-legal-research", "version": "0.1.0"}}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = message.get("params") if isinstance(message.get("params"), dict) else {}
        try:
            result = call_tool(str(params.get("name", "")), params.get("arguments", {}) if isinstance(params.get("arguments"), dict) else {})
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except (SourceAccessError, SourceBoundaryError, ValueError, OSError, KeyError) as exc:
            return {"jsonrpc": "2.0", "id": request_id, "result": _text_result({"status": "BLOCKED_BY_SOURCE", "error": str(exc)}, is_error=True)}
    if request_id is None:
        return None
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"method not found: {method}"}}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="read one JSON-RPC request and exit")
    args = parser.parse_args(argv)
    count = 0
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
            response = handle_message(message)
        except (json.JSONDecodeError, TypeError) as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
        if response is not None:
            print(json.dumps(response, ensure_ascii=False, separators=(",", ":")), flush=True)
        count += 1
        if args.once:
            break
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
