#!/usr/bin/env python3
"""Build privacy-conscious search queries for free official Chinese case sources."""

from __future__ import annotations

import argparse
import json
from urllib.parse import quote


def build(issue: str, fact: str | None = None) -> dict[str, object]:
    issue = " ".join(issue.split())
    fact = " ".join(fact.split()) if fact else None
    if not issue:
        raise ValueError("issue must not be empty")

    base = issue if not fact else f"{issue} {fact}"
    queries = [
        f'site:court.gov.cn "{issue}" 指导案例',
        f'site:court.gov.cn "{issue}" 入库参考案例',
        f'site:court.gov.cn "{base}" 典型案例 裁判结果',
        f'site:gongbao.court.gov.cn "{issue}" 案例',
        f'site:court.gov.cn "{base}" (不予支持 OR 驳回 OR 不构成 OR 无效 OR 未证明)',
        f'site:ipc.court.gov.cn "{base}" 案例',
        f'site:yyfx.court.gov.cn "{base}" 裁判要旨',
        f'site:chinacourt.gov.cn "{base}" 案例',
    ]
    return {
        "issue": issue,
        "fact": fact,
        "privacy_note": "Only submit de-identified legal issues and necessary fact patterns.",
        "queries": queries,
        "official_entry_urls": {
            "people_court_case_database": "https://rmfyalk.court.gov.cn/",
            "spc_search": f"https://www.court.gov.cn/search.html?content={quote(issue)}",
            "spc_gazette": "https://gongbao.court.gov.cn/",
            "judgments_online": "https://wenshu.court.gov.cn/",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("issue", help="De-identified cause or core legal issue")
    parser.add_argument("--fact", help="Optional de-identified decisive fact pattern")
    args = parser.parse_args()
    print(json.dumps(build(args.issue, args.fact), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
