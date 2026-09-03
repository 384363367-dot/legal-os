from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/cn-legal-research/scripts"
sys.path.insert(0, str(SCRIPTS))

from document_parser import extract_xml_articles  # noqa: E402
from html_parser import extract_records  # noqa: E402
from mcp_server import call_tool, handle_message  # noqa: E402
from region_classifier import classify_by_authority  # noqa: E402
from research_runtime import OfficialClient, SourceBoundaryError, SourceResponse  # noqa: E402
from site_adapters import fetch_detail, search_source  # noqa: E402
from source_registry import official_source_for_url, validate_official_url  # noqa: E402
from validate_authority_records import validate_record  # noqa: E402


class _FakeResponse:
    def __init__(self, url: str, content: bytes, *, status: int | None = 200, headers: dict[str, str] | None = None) -> None:
        self._url = url
        self._content = content
        self.status = status
        self.headers = headers or {"Content-Type": "application/json; charset=utf-8"}

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def geturl(self) -> str:
        return self._url

    def getcode(self) -> int:
        return 200

    def read(self, limit: int = -1) -> bytes:
        return self._content if limit < 0 else self._content[:limit]


class _FakeOpener:
    def __init__(self, response_factory) -> None:
        self.response_factory = response_factory
        self.calls: list[tuple[str, str, bytes | None]] = []

    def open(self, request, timeout: int):  # noqa: ANN001
        self.calls.append((request.method, request.full_url, request.data))
        return self.response_factory(request)


class PublicRuntimeTests(unittest.TestCase):
    def test_registry_rejects_parent_domain_wildcards_and_non_default_ports(self):
        self.assertIsNone(official_source_for_url("https://unrelated.gov.cn/path"))
        self.assertIsNone(official_source_for_url("https://flk.npc.gov.cn:8443/path"))
        self.assertEqual(validate_official_url("https://www.chinatax.gov.cn/getFileListByCodeId")[2], "tax-rules")

    def test_explicit_cache_caches_post_and_preserves_response(self):
        payload = b'{"code":200,"rows":[]}'
        opener = _FakeOpener(lambda request: _FakeResponse(request.full_url, payload))
        with tempfile.TemporaryDirectory() as directory:
            client = OfficialClient("npc-law", cache_dir=directory, requests_per_second=None, opener=opener)
            first = client.request("POST", "https://flk.npc.gov.cn/law-search/search/list", data={"q": "合同"})
            second = client.request("POST", "https://flk.npc.gov.cn/law-search/search/list", data={"q": "合同"})
            self.assertEqual(first.content, second.content)
            self.assertEqual(len(opener.calls), 1)
            self.assertEqual(client.cache.stats()["entries"], 1)

    def test_redirect_is_rejected_before_content_is_accepted(self):
        opener = _FakeOpener(lambda request: _FakeResponse("https://unrelated.gov.cn/redirect", b"blocked"))
        client = OfficialClient("npc-law", requests_per_second=None, opener=opener)
        with self.assertRaises(SourceBoundaryError):
            client.request("GET", "https://flk.npc.gov.cn/law-search/search/list")

    def test_xml_articles_and_html_records_are_parsed_without_dependencies(self):
        xml = """<root xmlns='urn:test'><p><t>第一条 甲。</t></p><p><t>第二条 乙。</t><br/><t>续文。</t></p></root>""".encode()
        articles = extract_xml_articles(xml)
        self.assertEqual([item[0] for item in articles], ["第一条 甲", "第二条 乙"])
        self.assertIn("续文", articles[1][1])
        html = '<html><title>示例</title><a href="detail/1.html">合同规则</a><a href="javascript:void(0)">忽略</a></html>'
        rows = extract_records(html, "https://www.gov.cn/", keyword="合同", url_pattern=r"detail/")
        self.assertEqual(rows[0]["detail_url"], "https://www.gov.cn/detail/1.html")

    def test_html_and_json_source_adapters_return_source_locked_records(self):
        treaty_url = "https://treaty.mfa.gov.cn/web/allinfos.jsp?nPageIndex_=1"
        policy_url = "https://sousuo.www.gov.cn/search-gov/data"

        class FakeClient:
            def request(self, method: str, url: str, **kwargs: object) -> SourceResponse:
                if url == treaty_url:
                    content = '<title>条约库</title><a href="detail.jsp?id=1">双边条约</a>'.encode()
                    return SourceResponse(200, treaty_url, {"content-type": "text/html"}, content)
                if url == policy_url:
                    content = json.dumps({"data": [{"title": "政策文件", "url": "https://sousuo.www.gov.cn/policy/1.html", "department": "国务院"}]}).encode()
                    return SourceResponse(200, policy_url, {"content-type": "application/json"}, content)
                raise AssertionError(url)

        client = FakeClient()
        treaty_rows = search_source("mfa-treaty", "双边", client=client)
        policy_rows = search_source("state-council-policy", "政策", client=client)
        self.assertEqual(treaty_rows[0]["source_id"], "mfa-treaty")
        self.assertEqual(treaty_rows[0]["detail_url"], "https://treaty.mfa.gov.cn/web/detail.jsp?id=1")
        self.assertEqual(policy_rows[0]["source_id"], "state-council-policy")
        self.assertEqual(policy_rows[0]["title"], "政策文件")

    def test_treaty_detail_keeps_official_preview_links_only(self):
        url = "https://treaty.mfa.gov.cn/web/detail.jsp?id=1"

        class FakeClient:
            def request(self, method: str, request_url: str, **kwargs: object) -> SourceResponse:
                content = '<title>示例条约</title><p>我国签署时间：2020年1月1日</p><a href="preview.pdf">文本</a><a href="https://example.com/x.pdf">外链</a>'
                return SourceResponse(200, url, {"content-type": "text/html"}, content.encode())

        result = fetch_detail(url, client=FakeClient())
        self.assertEqual(result["sign_date"], "2020年1月1日")
        self.assertEqual([item["url"] for item in result["preview_links"]], ["https://treaty.mfa.gov.cn/web/preview.pdf"])

    def test_region_classifier_handles_autonomous_prefecture(self):
        result = classify_by_authority("临夏回族自治州人大常务委员会")
        self.assertEqual(result["level"], "city")
        self.assertEqual(result["province"], "甘肃省")

    def test_authority_record_validator_checks_source_and_required_fields(self):
        record = {
            "title": "示例规范",
            "authority_type": "law",
            "issuing_body": "全国人民代表大会",
            "document_number": None,
            "promulgated_date": None,
            "effective_date": None,
            "status": "effective",
            "proposition": "待核验命题",
            "source_url": "https://flk.npc.gov.cn/",
            "accessed_at": "2026-09-03",
            "verification_status": "verified-source",
            "limitations": [],
            "supersedes": [],
            "superseded_by": [],
        }
        self.assertEqual(validate_record(record, 0), [])
        record["source_url"] = "https://example.com/record"
        self.assertTrue(validate_record(record, 0))

    def test_mcp_offline_tools_cover_validation_and_region_classification(self):
        listed = handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
        names = {tool["name"] for tool in listed["result"]["tools"]}
        self.assertTrue({"preview_npc_law", "query_npc_article", "search_articles", "classify_regions"}.issubset(names))
        valid = call_tool("validate_official_url", {"url": "http://example.com"})
        self.assertIn('"valid": false', valid["content"][0]["text"])
        classified = call_tool("classify_regions", {"records": [{"authority": "国务院", "title": "示例"}]})
        self.assertIn("national", classified["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
