"""Public official-source registry for Legal OS current-law research.

This module contains source metadata and URL/type checks only.  It deliberately
does not fetch, cache, parse or redistribute material from any external site.
"""
from __future__ import annotations

from urllib.parse import urlparse


ALL_AUTHORITY_TYPES = frozenset(
    {
        "law",
        "administrative-regulation",
        "judicial-interpretation",
        "department-rule",
        "local-regulation",
        "local-rule",
        "treaty",
        "other",
    }
)


OFFICIAL_SOURCES = (
    {
        "id": "npc-law",
        "name": "国家法律法规数据库",
        "official_url": "https://flk.npc.gov.cn/",
        "hosts": ("flk.npc.gov.cn", "npc.gov.cn", "www.npc.gov.cn"),
        "authority_types": (
            "law",
            "administrative-regulation",
            "local-regulation",
            "local-rule",
            "other",
        ),
        "scope": "法律、行政法规、地方性法规及相关规范文本",
    },
    {
        "id": "gov-rules",
        "name": "国家规章库",
        "official_url": "https://www.gov.cn/zhengce/xxgk/gjgzk/",
        "hosts": ("gov.cn", "www.gov.cn"),
        "authority_types": ("administrative-regulation", "department-rule", "other"),
        "scope": "国务院部门规章及国家规章公开信息",
    },
    {
        "id": "mfa-treaty",
        "name": "外交部条约数据库",
        "official_url": "https://treaty.mfa.gov.cn/",
        "hosts": ("treaty.mfa.gov.cn",),
        "authority_types": ("treaty",),
        "scope": "条约身份、缔约方、生效和文本信息",
    },
    {
        "id": "state-council-policy",
        "name": "国务院政策文件库",
        "official_url": "https://sousuo.www.gov.cn/",
        "hosts": ("sousuo.www.gov.cn",),
        "authority_types": ("other", "administrative-regulation"),
        "scope": "国务院及部门政策文件和公开说明",
    },
    {
        "id": "moj-regulations",
        "name": "司法部行政法规库",
        "official_url": "https://xzfg.moj.gov.cn/",
        "hosts": ("xzfg.moj.gov.cn",),
        "authority_types": ("administrative-regulation", "other"),
        "scope": "行政法规和相关法规公开信息",
    },
    {
        "id": "party-rules",
        "name": "党内法规库",
        "official_url": "https://www.12371.cn/special/dnfg/",
        "hosts": ("www.12371.cn", "12371.cn"),
        "authority_types": ("other",),
        "scope": "党内法规公开文本",
    },
    {
        "id": "mod-regulations",
        "name": "国防部法规文库",
        "official_url": "https://www.mod.gov.cn/gfbw/fgwx/",
        "hosts": ("www.mod.gov.cn", "mod.gov.cn"),
        "authority_types": ("department-rule", "other"),
        "scope": "国防领域法规、文件和公开司法解释",
    },
    {
        "id": "tax-rules",
        "name": "税务法规库",
        "official_url": "https://fgk.chinatax.gov.cn/",
        "hosts": ("fgk.chinatax.gov.cn",),
        "authority_types": ("department-rule", "other"),
        "scope": "税收法律、行政法规、部门规章和财税文件",
    },
    {
        "id": "mee-regulations",
        "name": "生态环境部法规规章",
        "official_url": "https://www.mee.gov.cn/ywgz/fgbz/",
        "hosts": ("www.mee.gov.cn", "mee.gov.cn"),
        "authority_types": ("department-rule", "other"),
        "scope": "生态环境领域法规、规章和执法解释",
    },
    {
        "id": "spc-publications",
        "name": "最高人民法院发布栏目",
        "official_url": "https://www.court.gov.cn/fabu/",
        "hosts": ("www.court.gov.cn", "court.gov.cn"),
        "authority_types": ("judicial-interpretation", "other"),
        "scope": "司法解释、司法文件及最高人民法院公开材料",
    },
)


def _host_matches(host: str, allowed: tuple[str, ...]) -> bool:
    return any(host == item or host.endswith("." + item) for item in allowed)


def official_source_for_url(url: str) -> dict[str, object] | None:
    """Return the registered source for an HTTPS URL, if any."""

    parsed = urlparse(url)
    if parsed.scheme.lower() != "https":
        return None
    host = (parsed.hostname or "").lower()
    matches = [
        source
        for source in OFFICIAL_SOURCES
        if _host_matches(host, source["hosts"])
    ]
    if not matches:
        return None
    # Prefer the most specific registered host over a broad parent such as
    # ``gov.cn``.  This keeps treaty.mfa.gov.cn in the treaty registry rather
    # than classifying it as a generic government-rule source.
    return max(matches, key=lambda source: max(len(item) for item in source["hosts"]))


def validate_official_url(
    url: str,
    authority_type: str | None = None,
) -> tuple[bool, str, str | None]:
    """Validate official host and, when supplied, authority-type binding."""

    parsed = urlparse(url)
    if parsed.scheme.lower() != "https":
        return False, "official source URL must use HTTPS", None
    source = official_source_for_url(url)
    if source is None:
        return False, "host not in official-source registry", None
    if authority_type and authority_type not in source["authority_types"]:
        return (
            False,
            f"host is not registered for authority type {authority_type!r}",
            str(source["id"]),
        )
    return True, "", str(source["id"])
