"""Machine-readable registry for public Chinese official-source adapters.

The registry stores routing metadata only.  It never fetches or embeds source
content and is intentionally independent from any external crawler project.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
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
        "party-rule",
        "policy",
        "official-publication",
        "other",
    }
)


@dataclass(frozen=True)
class OfficialSource:
    id: str
    name: str
    official_url: str
    hosts: tuple[str, ...]
    authority_types: tuple[str, ...]
    scope: str
    search_url: str
    access_mode: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


OFFICIAL_SOURCES: tuple[OfficialSource, ...] = (
    OfficialSource(
        "npc-law",
        "国家法律法规数据库",
        "https://flk.npc.gov.cn/",
        ("flk.npc.gov.cn", "npc.gov.cn", "www.npc.gov.cn"),
        ("law", "administrative-regulation", "local-regulation", "local-rule", "other"),
        "法律、行政法规、地方性法规及相关规范文本",
        "https://flk.npc.gov.cn/law-search/search/list",
        "json-api",
    ),
    OfficialSource(
        "gov-rules",
        "国家规章库",
        "https://www.gov.cn/zhengce/xxgk/gjgzk/",
        ("gov.cn", "www.gov.cn"),
        ("administrative-regulation", "department-rule", "official-publication", "other"),
        "国务院部门规章及国家规章公开信息",
        "https://www.gov.cn/zhengce/xxgk/gjgzk/",
        "html-or-json",
    ),
    OfficialSource(
        "mfa-treaty",
        "外交部条约数据库",
        "https://treaty.mfa.gov.cn/",
        ("treaty.mfa.gov.cn",),
        ("treaty",),
        "条约身份、缔约方、生效和文本信息",
        "https://treaty.mfa.gov.cn/web/allinfos.jsp",
        "html",
    ),
    OfficialSource(
        "state-council-policy",
        "国务院政策文件库",
        "https://sousuo.www.gov.cn/",
        ("sousuo.www.gov.cn",),
        ("policy", "official-publication", "administrative-regulation"),
        "国务院及部门政策文件和公开说明",
        "https://sousuo.www.gov.cn/search-gov/data",
        "json-api",
    ),
    OfficialSource(
        "moj-regulations",
        "司法部行政法规库",
        "https://xzfg.moj.gov.cn/",
        ("xzfg.moj.gov.cn",),
        ("administrative-regulation", "official-publication", "other"),
        "行政法规和相关法规公开信息",
        "https://xzfg.moj.gov.cn/search2.html",
        "html",
    ),
    OfficialSource(
        "party-rules",
        "党内法规库",
        "https://www.12371.cn/special/dnfg/",
        ("www.12371.cn", "12371.cn"),
        ("party-rule", "official-publication", "other"),
        "党内法规公开文本",
        "https://www.12371.cn/special/dnfg/",
        "html",
    ),
    OfficialSource(
        "mod-regulations",
        "国防部法规文库",
        "https://www.mod.gov.cn/gfbw/fgwx/",
        ("www.mod.gov.cn", "mod.gov.cn"),
        ("department-rule", "official-publication", "other"),
        "国防领域法规、文件和公开司法解释",
        "https://www.mod.gov.cn/gfbw/fgwx/",
        "html",
    ),
    OfficialSource(
        "tax-rules",
        "税务法规库",
        "https://fgk.chinatax.gov.cn/",
        ("fgk.chinatax.gov.cn", "chinatax.gov.cn", "www.chinatax.gov.cn"),
        ("law", "administrative-regulation", "department-rule", "official-publication", "other"),
        "税收法律、行政法规、部门规章和财税文件",
        "https://fgk.chinatax.gov.cn/",
        "html-or-json",
    ),
    OfficialSource(
        "mee-regulations",
        "生态环境部法规规章",
        "https://www.mee.gov.cn/ywgz/fgbz/",
        ("www.mee.gov.cn", "mee.gov.cn"),
        ("administrative-regulation", "department-rule", "official-publication", "other"),
        "生态环境领域法规、规章和执法解释",
        "https://www.mee.gov.cn/ywgz/fgbz/",
        "html",
    ),
    OfficialSource(
        "spc-publications",
        "最高人民法院发布栏目",
        "https://www.court.gov.cn/fabu/",
        ("www.court.gov.cn", "court.gov.cn"),
        ("judicial-interpretation", "official-publication", "other"),
        "司法解释、司法文件及最高人民法院公开材料",
        "https://www.court.gov.cn/fabu/",
        "html",
    ),
)

SOURCE_BY_ID = {source.id: source for source in OFFICIAL_SOURCES}


def source_for_id(source_id: str) -> OfficialSource:
    try:
        return SOURCE_BY_ID[source_id]
    except KeyError as exc:
        raise KeyError(f"unknown official source: {source_id}") from exc


def _host_matches(host: str, allowed: tuple[str, ...]) -> bool:
    # Registry entries are concrete official hosts.  Treating a parent domain
    # such as ``gov.cn`` as an implicit wildcard would admit unrelated hosts.
    return host in allowed


def official_source_for_url(url: str) -> OfficialSource | None:
    """Return a source only for an HTTPS URL on a registered official host."""

    parsed = urlparse(url)
    if parsed.scheme.lower() != "https":
        return None
    if parsed.username or parsed.password:
        return None
    try:
        if parsed.port not in (None, 443):
            return None
    except ValueError:
        return None
    host = (parsed.hostname or "").lower().rstrip(".")
    matches = [source for source in OFFICIAL_SOURCES if _host_matches(host, source.hosts)]
    if not matches:
        return None
    return max(matches, key=lambda source: max(len(item) for item in source.hosts))


def validate_official_url(
    url: str,
    authority_type: str | None = None,
) -> tuple[bool, str, str | None]:
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https":
        return False, "official source URL must use HTTPS", None
    source = official_source_for_url(url)
    if source is None:
        return False, "host not in the official-source registry", None
    if authority_type and authority_type not in source.authority_types:
        return False, f"host is not registered for authority type {authority_type!r}", source.id
    return True, "", source.id


def registry_payload() -> list[dict[str, object]]:
    return [source.as_dict() for source in OFFICIAL_SOURCES]
