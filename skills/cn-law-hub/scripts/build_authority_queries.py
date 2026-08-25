#!/usr/bin/env python3
"""Build privacy-conscious official-source queries for Chinese current-law research."""
from __future__ import annotations
import argparse
import json

try:
    from .source_registry import OFFICIAL_SOURCES
except ImportError:
    from source_registry import OFFICIAL_SOURCES


def clean(value: str) -> str:
    return " ".join(value.split())


def build(proposition: str, name: str | None = None, article: str | None = None) -> dict[str, object]:
    proposition = clean(proposition)
    name = clean(name) if name else None
    article = clean(article) if article else None
    base = " ".join(value for value in (name, article, proposition) if value)

    queries = [
        f'site:flk.npc.gov.cn "{base}"',
        f'site:npc.gov.cn "{base}"',
        f'site:gov.cn "{base}"',
        f'site:court.gov.cn "{base}" 司法解释',
        f'site:gov.cn "{base}" 修改 废止 施行',
    ]
    source_plans = []
    for source in OFFICIAL_SOURCES:
        host = source["hosts"][0]
        source_plans.append(
            {
                "source_id": source["id"],
                "name": source["name"],
                "official_url": source["official_url"],
                "authority_types": list(source["authority_types"]),
                "scope": source["scope"],
                "query": f'site:{host} "{base}"',
            }
        )

    return {
        "proposition": proposition,
        "authority_name": name,
        "article": article,
        "queries": list(dict.fromkeys(queries)),
        "official_sources": source_plans,
        "source_count": len(source_plans),
        "verification_note": (
            "Search results are leads; open an authoritative source and verify "
            "version/effectiveness before relying on the rule. This public adapter "
            "only creates a query plan and does not fetch or cache external content. "
            "本公开适配仅生成查询计划，不自动抓取或缓存外部内容。"
        ),
    }


def main():
 ap = argparse.ArgumentParser()
 ap.add_argument("proposition")
 ap.add_argument("--name")
 ap.add_argument("--article")
 args = ap.parse_args()
 print(json.dumps(build(args.proposition, args.name, args.article), ensure_ascii=False, indent=2))
 return 0


if __name__=='__main__':raise SystemExit(main())
