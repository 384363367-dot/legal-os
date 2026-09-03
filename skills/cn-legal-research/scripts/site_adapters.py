"""Source-specific official-source adapters for the public research Skill.

The adapters use the common HTTPS client and standard-library parsers. They
recreate the public request/parse contracts without bundling source data or
copying third-party crawler implementations.
"""
from __future__ import annotations

import base64
import csv
import json
import re
import secrets
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import quote, urljoin

from html_parser import extract_detail, extract_records, parse_html
from research_runtime import (
    OfficialClient,
    SourceAccessError,
    SourceBoundaryError,
    SourceResponse,
    clean_text,
    safe_filename,
    write_json,
)
from source_registry import OfficialSource, official_source_for_url, source_for_id
from source_specs import (
    GOV_RULES_INDEX,
    GOV_RULES_QUERY_PATH,
    NPC_BASE,
    TAX_API,
    TAX_BASE,
    CATEGORY_MAPS,
    category_code,
    category_label,
    category_options,
    mee_list_url,
    mod_list_url,
    party_list_url,
    spc_list_url,
    tax_category_url,
    treaty_list_url,
)


def _first(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return None


def _plain(value: object) -> str:
    if isinstance(value, Mapping):
        value = _first(value, "value", "text", "name", "label", "content") or ""
    text = str(value or "")
    return clean_text(re.sub(r"<[^>]+>", "", text))


def _registered_detail_url(raw_url: object, base_url: str, source: OfficialSource) -> str | None:
    if not raw_url:
        return None
    candidate = urljoin(base_url, str(raw_url))
    registered = official_source_for_url(candidate)
    return candidate if registered is not None and registered.id == source.id else None


def _iter_record_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, list):
        for item in value:
            yield from _iter_record_dicts(item)
    elif isinstance(value, dict):
        title = _first(value, "title", "name", "lawName", "documentTitle", "subject", "articleTitle", "titleHtml")
        if title:
            yield value
        for key, child in value.items():
            if key not in {"title", "name", "lawName", "documentTitle", "subject", "articleTitle", "titleHtml"}:
                yield from _iter_record_dicts(child)


def _record_from_mapping(item: Mapping[str, Any], source: OfficialSource, base_url: str, *, category: str = "") -> dict[str, object] | None:
    title = _plain(_first(item, "title", "name", "lawName", "documentTitle", "subject", "articleTitle", "titleHtml"))
    raw_url = _first(item, "detail_url", "detailUrl", "url", "link", "href", "sourceUrl", "piclinksurl", "doc_pub_url")
    detail_url = _registered_detail_url(raw_url, base_url, source)
    if not title and not detail_url:
        return None
    return {
        "source_id": source.id,
        "source_name": source.name,
        "category": category or _plain(_first(item, "category", "cat_name", "type", "lawType")),
        "title": title or detail_url or "未命名记录",
        "detail_url": detail_url,
        "source_url": detail_url or source.official_url,
        "document_number": _plain(_first(item, "document_number", "documentNumber", "wenhao", "fileNo", "pcode", "pno")),
        "issuing_body": _plain(_first(item, "issuing_body", "issuingBody", "authority", "department", "issuer", "source")),
        "promulgated_date": _plain(_first(item, "promulgated_date", "publish_date", "publishDate", "gbrq", "publishTime", "pubtime", "publishedTimeStr")),
        "effective_date": _plain(_first(item, "effective_date", "effectiveDate", "sxrq", "effectivedate")),
        "status": normalize_status(_first(item, "status", "statusText", "sxx", "effectiveness", "effect")),
        "content": _plain(_first(item, "content", "summary", "body_excerpt", "subTitleHtml")),
        "raw": dict(item),
    }
def _json_records(payload: Any, source: OfficialSource, base_url: str, limit: int, *, category: str = "") -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in _iter_record_dicts(payload):
        record = _record_from_mapping(item, source, base_url, category=category)
        if record is None:
            continue
        key = str(record.get("detail_url") or record["title"])
        if key in seen:
            continue
        seen.add(key)
        results.append(record)
        if len(results) >= limit:
            break
    return results


def _response_is_json(response: SourceResponse) -> bool:
    content_type = response.headers.get("content-type", "").lower()
    return "json" in content_type or response.content.lstrip().startswith((b"{", b"["))


def _search_params(source_id: str, keyword: str, page: int, size: int, search_range: str, filters: Mapping[str, object] | None) -> dict[str, object]:
    field = "content" if search_range == "content" else "title"
    params: dict[str, object] = {
        "keyword": keyword,
        "q": keyword,
        "search": keyword,
        "searchfield": field,
        "searchField": field,
        "page": page,
        "pageIndex": page,
        "pageNum": page,
        "pageSize": size,
        "size": size,
    }
    filters = filters or {}
    if source_id == "state-council-policy":
        params = {
            "t": "zhengcelibrary",
            "q": keyword,
            "searchfield": field,
            "sort": {"date": "pubtime"}.get(str(filters.get("sort") or "score"), str(filters.get("sort") or "score")),
            "sortType": 1,
            "p": max(0, page - 1),
            "n": size,
            "type": "gwyzcwjk",
        }
        if filters.get("category"):
            params["childtype"] = category_code(source_id, str(filters["category"]))
        if filters.get("year"):
            params["pubtimeyear"] = filters["year"]
        if filters.get("department"):
            params["bmfl"] = filters["department"]
    elif source_id == "moj-regulations":
        params = {
            "SearchWord": keyword,
            "pageIndex": page,
            "pageSize": size,
            "searchField": "2" if field == "content" else "1",
        }
        status = str(filters.get("status") or "all")
        if status in {"effective", "invalid"}:
            params["effect"] = {"effective": "1", "invalid": "2"}[status]
    return {key: value for key, value in params.items() if value not in (None, "")}


def make_client(source_id: str, **kwargs: object) -> OfficialClient:
    return OfficialClient(source_for_id(source_id), **kwargs)


def _read_der_tlv(data: bytes, offset: int = 0) -> tuple[int, bytes, int]:
    if offset >= len(data):
        raise ValueError("truncated DER value")
    tag = data[offset]
    offset += 1
    if offset >= len(data):
        raise ValueError("truncated DER length")
    length = data[offset]
    offset += 1
    if length & 0x80:
        count = length & 0x7F
        if not count or offset + count > len(data):
            raise ValueError("invalid DER length")
        length = int.from_bytes(data[offset : offset + count], "big")
        offset += count
    end = offset + length
    if end > len(data):
        raise ValueError("truncated DER content")
    return tag, data[offset:end], end


def _rsa_public_numbers(public_key_b64: str) -> tuple[int, int]:
    raw = base64.b64decode(re.sub(r"\s+", "", public_key_b64), validate=True)
    tag, content, _ = _read_der_tlv(raw)
    if tag != 0x30:
        raise ValueError("public key is not a DER sequence")
    children: list[tuple[int, bytes]] = []
    position = 0
    while position < len(content):
        child_tag, child_content, position = _read_der_tlv(content, position)
        children.append((child_tag, child_content))
    if len(children) >= 2 and children[1][0] == 0x03:
        bit_string = children[1][1]
        if not bit_string:
            raise ValueError("empty RSA public key bit string")
        _, rsa_content, _ = _read_der_tlv(bit_string[1:])
    else:
        rsa_content = content
    ints: list[int] = []
    position = 0
    while position < len(rsa_content):
        tag, value, position = _read_der_tlv(rsa_content, position)
        if tag == 0x02:
            ints.append(int.from_bytes(value, "big"))
    if len(ints) < 2 or not ints[0] or not ints[1]:
        raise ValueError("RSA modulus/exponent not found")
    return ints[0], ints[1]


def _rsa_pkcs1_v15_encrypt(public_key_b64: str, message: str) -> str:
    modulus, exponent = _rsa_public_numbers(public_key_b64)
    key_size = (modulus.bit_length() + 7) // 8
    message_bytes = message.encode("utf-8")
    padding_length = key_size - len(message_bytes) - 3
    if padding_length < 8:
        raise ValueError("RSA seed is too long for the discovered public key")
    padding_bytes = bytearray()
    while len(padding_bytes) < padding_length:
        padding_bytes.extend(byte for byte in secrets.token_bytes(padding_length - len(padding_bytes)) if byte)
    encoded = b"\x00\x02" + bytes(padding_bytes[:padding_length]) + b"\x00" + message_bytes
    cipher = pow(int.from_bytes(encoded, "big"), exponent, modulus).to_bytes(key_size, "big")
    return quote(base64.b64encode(cipher).decode("ascii"), safe="")


class GovRulesAuth:
    """Discover the public Athena request parameters without a crypto package."""

    def __init__(self, client: OfficialClient) -> None:
        self.client = client
        self.base_url = ""
        self.app_name = ""
        self.app_key = ""

    def discover(self) -> "GovRulesAuth":
        index = self.client.request("GET", GOV_RULES_INDEX)
        match = re.search(r'<script[^>]+src=["\'](index\.js\?[^"\']+)["\']', index.text, flags=re.I)
        if not match:
            raise SourceAccessError("国家规章库 index.js 未找到")
        script = self.client.request("GET", urljoin(GOV_RULES_INDEX, match.group(1)))
        auth_match = re.search(
            r'var\s+s=["\'](?P<base>https://[^"\']+)["\'].*?a\(["\'](?P<pub>[^"\']+)["\'],["\'](?P<seed>[^"\']+)["\']\).*?encodeURIComponent\(["\'](?P<name>[^"\']+)["\']\)',
            script.text,
            flags=re.S,
        )
        if not auth_match:
            raise SourceAccessError("国家规章库公开认证参数未找到")
        self.base_url = auth_match.group("base").rstrip("/")
        self.app_key = _rsa_pkcs1_v15_encrypt(auth_match.group("pub"), auth_match.group("seed"))
        self.app_name = quote(auth_match.group("name"), safe="")
        return self

    def headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json, text/javascript, */*;q=0.01",
            "Content-Type": "application/json;charset=UTF-8",
            "Referer": "https://www.gov.cn/",
            "athenaappname": self.app_name,
            "athenaappkey": self.app_key,
        }


def _field(item: Mapping[str, Any], key: str) -> str:
    value = item.get(key, "")
    if isinstance(value, Mapping):
        value = _first(value, "value", "text", "name") or ""
    return _plain(value)


def _search_gov_rules(client: OfficialClient, keyword: str, page: int, size: int, category: str) -> list[dict[str, object]]:
    if not category or category == "全部":
        records: list[dict[str, object]] = []
        for label in category_options("gov-rules"):
            records.extend(_search_gov_rules(client, keyword, page, size - len(records), label))
            if len(records) >= size:
                break
        return records[:size]
    auth = GovRulesAuth(client).discover()
    category_name = category or "部门规章"
    title_search: dict[str, object] = {"fieldName": "f_202321360426", "withHighLight": True}
    if keyword:
        title_search.update({"searchWord": keyword, "searchType": "TERM"})
    payload = {
        "code": "18258ab0ac9",
        "preference": None,
        "searchFields": [
            {"fieldName": "f_202321807875", "searchWord": category_name, "searchType": "TERM", "withHighLight": True},
            title_search,
            {"fieldName": "f_202321758948", "withHighLight": True},
            {"fieldName": "f_202321423473", "searchType": "TERM", "withHighLight": True},
            {"fieldName": "f_202321159816", "searchWord": "", "searchType": "TERM"},
            {"fieldName": "f_20232380533", "searchType": "TERM", "withHighLight": True},
            {"fieldName": "f_202328191239", "withHighLight": True, "searchType": "TERM"},
            {"fieldName": "f_20221110222856", "withHighLight": True, "searchType": "TERM"},
        ],
        "sorts": [{}, {"sortField": "f_202321915922", "sortOrder": "DESC"}],
        "resultFields": [
            "f_202355832506", "f_20232124962", "f_202321124775", "f_202321159816",
            "f_202321360426", "f_202321423473", "f_202321758948", "f_202321807875",
            "f_202321864401", "f_202321915922", "f_202323394765", "f_202328191239",
            "f_202344311304", "f_2023425676953", "f_2023425808265", "f_202321136868",
            "f_20232380533", "f_20232151076", "doc_pub_url",
        ],
        "trackTotalHits": "true",
        "tableName": "t_1860c735d31",
        "pageSize": size,
        "pageNo": page,
        "granularity": "ALL",
    }
    response = client.request("POST", auth.base_url + GOV_RULES_QUERY_PATH, data=payload, headers=auth.headers())
    body = response.json()
    result_code = body.get("resultCode", {}).get("code") if isinstance(body, Mapping) else None
    if result_code not in (200, "200"):
        raise SourceAccessError(f"国家规章库搜索失败: {body.get('resultCode', 'unknown')}")
    data = body.get("result", {}).get("data", {}) if isinstance(body, Mapping) else {}
    items = data.get("list", []) if isinstance(data, Mapping) else []
    source = source_for_id("gov-rules")
    records: list[dict[str, object]] = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, Mapping):
            continue
        detail_url = _registered_detail_url(_field(item, "doc_pub_url"), GOV_RULES_INDEX, source)
        record = {
            "source_id": source.id,
            "source_name": source.name,
            "category": category_name,
            "title": _field(item, "f_202321360426"),
            "issuing_body": _field(item, "f_202323394765"),
            "document_number": _field(item, "f_202321124775"),
            "promulgated_date": _field(item, "f_202344311304"),
            "effective_date": _field(item, "f_202321423473"),
            "status": _field(item, "f_202321159816") or "未标注",
            "detail_url": detail_url,
            "source_url": detail_url,
            "content": _field(item, "f_202321758948")[:500],
            "raw": dict(item),
        }
        if record["title"] or record["detail_url"]:
            records.append(record)
    return records[:size]


def _search_tax(client: OfficialClient, keyword: str, page: int, size: int, category: str) -> list[dict[str, object]]:
    source = source_for_id("tax-rules")
    codes = [category_code("tax-rules", category)] if category and category != "全部" else [value for value in CATEGORY_MAPS["tax-rules"].values() if value]
    records: list[dict[str, object]] = []
    for code in codes:
        channel_id = ""
        for variant in ("listflfg.html", "listflfg_fg.html", "list_guizhang.html"):
            try:
                page_response = client.request("GET", tax_category_url(code, variant))
            except (SourceAccessError, SourceBoundaryError):
                continue
            match = re.search(r"channelId\s*=\s*[\"']([^\"']+)", page_response.text)
            if match:
                channel_id = match.group(1)
                break
        if not channel_id:
            raise SourceAccessError(f"税务法规库未发现分类 {code} 的 channelId")
        payload = {"codeId": code, "channelId": channel_id, "page": page, "size": size, "sort": [], "relateSubChannels": False}
        response = client.request("POST", TAX_API, data=payload, headers={"Content-Type": "application/json", "Referer": tax_category_url(code)})
        body = response.json()
        items = body.get("results", {}).get("data", {}).get("results", []) if isinstance(body, Mapping) else []
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, Mapping):
                continue
            metadata: dict[str, str] = {}
            groups = item.get("domainMetaList", [])
            for group in groups if isinstance(groups, list) else []:
                entries = group.get("resultList", []) if isinstance(group, Mapping) else []
                for entry in entries if isinstance(entries, list) else []:
                    if isinstance(entry, Mapping) and entry.get("key"):
                        metadata[str(entry["key"])] = _plain(entry.get("value"))
            raw_url = _plain(item.get("url"))
            detail_url = _registered_detail_url(raw_url, TAX_BASE, source)
            record = {
                "source_id": source.id,
                "source_name": source.name,
                "category": category_label("tax-rules", code),
                "title": _plain(item.get("titleHtml")),
                "sub_title": _plain(item.get("subTitleHtml")),
                "detail_url": detail_url,
                "source_url": detail_url or source.official_url,
                "promulgated_date": _plain(item.get("publishedTimeStr")),
                "effective_date": metadata.get("effectivedate", ""),
                "document_number": metadata.get("fz", metadata.get("writeno", "")),
                "issuing_body": metadata.get("issuerDepartment", metadata.get("source", "")),
                "status": "未标注",
                "raw": dict(item),
            }
            search_text = " ".join(str(record.get(key, "")) for key in ("title", "sub_title", "document_number"))
            if record["title"] and (not keyword or keyword.casefold() in search_text.casefold()):
                records.append(record)
                if len(records) >= size:
                    return records
    return records[:size]


def _html_pattern(source_id: str) -> str | None:
    return {
        "mfa-treaty": r"(?:detail\.jsp|detail/)",
        "moj-regulations": r"(?:detail|\.html)",
        "party-rules": r"/\d{4}/\d{2}/\d{2}/[^/]+\.shtml$",
        "mod-regulations": r"/gfbw/fgwx/[^/]+/\d+\.html$",
        "mee-regulations": r"/t20\d+",
        "spc-publications": r"/fabu/xiangqing/\d+\.html$",
    }.get(source_id)


def _html_categories(source_id: str, filters: Mapping[str, object] | None) -> list[str]:
    category = str((filters or {}).get("category") or "")
    if source_id == "mfa-treaty":
        return [category or "全部"]
    if category and category != "全部":
        return [category]
    if source_id == "spc-publications":
        return [label for label in category_options(source_id) if label != "全部"]
    return [label for label in category_options(source_id) if label != "全部"]


def _search_html_source(source_id: str, keyword: str, page: int, size: int, search_range: str, filters: Mapping[str, object] | None, client: OfficialClient) -> list[dict[str, object]]:
    source = source_for_id(source_id)
    records: list[dict[str, object]] = []
    categories = _html_categories(source_id, filters)
    max_pages = max(1, int((filters or {}).get("max_pages") or 1))
    for label in categories:
        code = category_code(source_id, label)
        for page_number in range(max(1, page), max(1, page) + max_pages):
            if source_id == "mfa-treaty":
                url = treaty_list_url(label, page_number)
            elif source_id == "party-rules":
                url = party_list_url(code, page_number)
            elif source_id == "mod-regulations":
                url = mod_list_url(code, page_number)
            elif source_id == "mee-regulations":
                url = mee_list_url(code)
            elif source_id == "spc-publications":
                url = spc_list_url(code, page_number)
            else:
                url = source.search_url
            params = _search_params(source_id, keyword, page_number, size, search_range, filters)
            response = client.request("GET", url, params=params if source_id == "moj-regulations" else None)
            items = extract_records(response.text, response.url, keyword=keyword if search_range != "content" else "", limit=size, url_pattern=_html_pattern(source_id))
            for item in items:
                record = _record_from_mapping(item, source, response.url, category=label)
                if record is None:
                    continue
                if search_range == "content" and keyword:
                    record["content_search"] = "需要详情页正文核验"
                records.append(record)
                if len(records) >= size:
                    return records
            if not items or len(records) >= size:
                break
    return records[:size]


def search_source(
    source_id: str,
    keyword: str = "",
    *,
    page: int = 1,
    size: int = 20,
    search_range: str = "title",
    filters: Mapping[str, object] | None = None,
    client: OfficialClient | Any | None = None,
) -> list[dict[str, object]]:
    source = source_for_id(source_id)
    active_client = client or make_client(source_id)
    filters = filters or {}
    size = max(1, min(int(size), 500))
    if source_id == "npc-law":
        from download import collect_search_records, search_laws

        raw = search_laws(
            keyword,
            page=max(1, page),
            size=size,
            search_range=2 if search_range == "content" else 1,
            search_type=1 if filters.get("exact") else 2,
            status_filter=[int(filters["status"])] if str(filters.get("status", "")).isdigit() else None,
            client=active_client,
        )
        return collect_search_records(raw, source=source, limit=size)
    if source_id == "gov-rules":
        return _search_gov_rules(active_client, keyword, page, size, str(filters.get("category") or ""))
    if source_id == "tax-rules":
        return _search_tax(active_client, keyword, page, size, str(filters.get("category") or ""))
    if source_id == "state-council-policy":
        response = active_client.request("GET", source.search_url, params=_search_params(source_id, keyword, page, size, search_range, filters))
        if _response_is_json(response):
            try:
                payload = response.json()
            except ValueError:
                payload = {}
            return _json_records(payload, source, response.url, size, category=str(filters.get("category") or ""))
        return [item for item in (_record_from_mapping(row, source, response.url) for row in extract_records(response.text, response.url, keyword=keyword, limit=size)) if item]
    return _search_html_source(source_id, keyword, page, size, search_range, filters, active_client)


def _parse_treaty_detail(html: str, url: str, source: OfficialSource) -> dict[str, object]:
    document = parse_html(html)
    text = document.text
    labels = {
        "类别": "category", "领域": "domain", "我国签署时间": "sign_date",
        "条约生效时间": "effective_date", "对我国生效时间": "effective_to_china",
        "保存机关": "depositary", "签署地点": "sign_place", "港澳情况": "hong_kong_macau",
        "我国声明保留情况": "statement_reservation", "其他": "other_info",
        "条约通过时间": "adoption_date", "我国批准/核准/接受/加入时间": "ratification_date",
        "条约适用于": "applies_to",
    }
    date_keys = {"sign_date", "effective_date", "effective_to_china", "adoption_date", "ratification_date"}
    result: dict[str, object] = {
        "source_id": source.id,
        "source_name": source.name,
        "title": document.title or (document.links[0].text if document.links else ""),
        "detail_url": url,
        "source_url": url,
        "content": text,
    }
    for label, key in labels.items():
        value_pattern = r"(20\d{2}[年/-]\d{1,2}[月/-]\d{1,2}日?)" if key in date_keys else r"([^；;。]{1,160})"
        match = re.search(re.escape(label) + r"\s*[：:]\s*" + value_pattern, text)
        result[key] = clean_text(match.group(1)) if match else ""
    result["preview_links"] = []
    for index, link in enumerate(document.links, 1):
        preview_url = _registered_detail_url(link.href, url, source)
        if preview_url and preview_url.lower().split("?", 1)[0].endswith(".pdf"):
            result["preview_links"].append({"label": link.text or f"preview_{index}", "url": preview_url})
    return result


def fetch_detail(url: str, *, source_id: str | None = None, client: OfficialClient | Any | None = None) -> dict[str, object]:
    source = source_for_id(source_id) if source_id else official_source_for_url(url)
    if source is None:
        raise SourceBoundaryError(f"detail URL is not a registered official URL: {url}")
    if official_source_for_url(url) != source:
        raise SourceBoundaryError(f"detail URL is outside the {source.id} source boundary: {url}")
    active_client = client or make_client(source.id)
    response = active_client.request("GET", url)
    if official_source_for_url(response.url) != source:
        raise SourceBoundaryError(f"detail response left the {source.id} source boundary")
    if source.id == "mfa-treaty" and not _response_is_json(response):
        return _parse_treaty_detail(response.text, response.url, source)
    if _response_is_json(response):
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw_text": response.text}
        return {"source_id": source.id, "source_name": source.name, "detail_url": response.url, "source_url": response.url, "payload": payload}
    return {"source_id": source.id, "source_name": source.name, **extract_detail(response.text, response.url)}


def download_source_file(url: str, output: str, *, source_id: str | None = None, client: OfficialClient | Any | None = None) -> dict[str, object]:
    source = source_for_id(source_id) if source_id else official_source_for_url(url)
    if source is None:
        raise SourceBoundaryError(f"download URL is not a registered official URL: {url}")
    if official_source_for_url(url) != source:
        raise SourceBoundaryError(f"download URL is outside the {source.id} source boundary: {url}")
    active_client = client or make_client(source.id)
    return active_client.download(url, output)


def normalize_status(value: object) -> str:
    if isinstance(value, int) or (isinstance(value, str) and value.isdigit()):
        return {1: "已废止", 2: "已修改", 3: "现行有效", 4: "尚未生效"}.get(int(value), "未标注")
    text = _plain(value)
    return text or "未标注"


def filter_records(records: Iterable[Mapping[str, object]], *, keyword: str = "", year: str | None = None, department: str | None = None) -> list[dict[str, object]]:
    needle = clean_text(keyword).casefold()
    output: list[dict[str, object]] = []
    for raw in records:
        record = dict(raw)
        haystack = " ".join(str(record.get(key, "")) for key in ("title", "content", "issuing_body", "source_url", "document_number")).casefold()
        if needle and needle not in haystack:
            continue
        if year and year not in " ".join(str(record.get(key, "")) for key in ("promulgated_date", "effective_date", "publish_date")):
            continue
        if department and clean_text(department).casefold() not in str(record.get("issuing_body", "")).casefold():
            continue
        record["status"] = normalize_status(record.get("status"))
        output.append(record)
    return output


def collect_search_records(payload: Mapping[str, object], *, source: OfficialSource, limit: int = 20) -> list[dict[str, object]]:
    """Normalize NPC rows while preserving the raw response contract."""
    rows = payload.get("rows", []) if payload.get("code") in (200, "200") else []
    results: list[dict[str, object]] = []
    for row in rows if isinstance(rows, list) else []:
        if not isinstance(row, Mapping):
            continue
        item = _record_from_mapping(row, source, NPC_BASE)
        if item is not None:
            item["bbbs"] = row.get("bbbs")
            item["status_code"] = row.get("sxx")
            item["status"] = normalize_status(row.get("sxx"))
            results.append(item)
        if len(results) >= limit:
            break
    return results


def write_result_bundle(records: list[Mapping[str, object]], output_dir: Path | str, *, source_id: str, keyword: str = "", category: str = "") -> Path:
    """Write explicit caller-requested JSON/JSONL/CSV metadata outputs."""
    root = Path(output_dir).expanduser().resolve() / safe_filename(f"{source_id}_{keyword or category or 'all'}", source_id)
    root.mkdir(parents=True, exist_ok=True)
    rows = [dict(record) for record in records]
    write_json(root / "metadata.json", rows)
    with (root / "metadata.jsonl").open("w", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    columns = sorted({key for row in rows for key, value in row.items() if not isinstance(value, (dict, list))})
    with (root / "metadata.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns or ["title"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    status_counts: dict[str, int] = {}
    for row in rows:
        status = normalize_status(row.get("status"))
        status_counts[status] = status_counts.get(status, 0) + 1
    write_json(root / "stats.json", {"source_id": source_id, "keyword": keyword, "category": category, "record_count": len(rows), "status_distribution": status_counts})
    return root
