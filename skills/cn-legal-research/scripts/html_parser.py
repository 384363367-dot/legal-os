"""Minimal HTML parsing helpers based on :mod:`html.parser`."""
from __future__ import annotations

import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin

from research_runtime import clean_text


@dataclass(frozen=True)
class Link:
    href: str
    text: str


@dataclass(frozen=True)
class HTMLDocument:
    title: str
    text: str
    links: tuple[Link, ...]


class _DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.links: list[Link] = []
        self._title_depth = 0
        self._skip_depth = 0
        self._anchor_href: str | None = None
        self._anchor_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "template"}:
            self._skip_depth += 1
        if tag == "title":
            self._title_depth += 1
        if tag == "a" and self._anchor_href is None:
            self._anchor_href = dict(attrs).get("href")
            self._anchor_parts = []

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "a" and self._anchor_href is not None:
            self.links.append(Link(self._anchor_href, clean_text(" ".join(self._anchor_parts))))
            self._anchor_href = None
            self._anchor_parts = []
        if tag == "title" and self._title_depth:
            self._title_depth -= 1
        if tag in {"script", "style", "noscript", "template"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        value = clean_text(unescape(data))
        if not value:
            return
        self.text_parts.append(value)
        if self._title_depth:
            self.title_parts.append(value)
        if self._anchor_href is not None:
            self._anchor_parts.append(value)


def parse_html(html: str) -> HTMLDocument:
    parser = _DocumentParser()
    parser.feed(html)
    parser.close()
    return HTMLDocument(
        title=clean_text(" ".join(parser.title_parts)),
        text=clean_text(" ".join(parser.text_parts)),
        links=tuple(parser.links),
    )


def extract_records(
    html: str,
    base_url: str,
    *,
    keyword: str = "",
    limit: int = 20,
    url_pattern: str | None = None,
) -> list[dict[str, object]]:
    document = parse_html(html)
    needle = clean_text(keyword).casefold()
    pattern = re.compile(url_pattern) if url_pattern else None
    records: list[dict[str, object]] = []
    seen: set[str] = set()
    for link in document.links:
        if not link.href or link.href.startswith(("#", "javascript:", "mailto:")):
            continue
        detail_url = urljoin(base_url, link.href)
        title = clean_text(link.text) or detail_url.rsplit("/", 1)[-1]
        if pattern and not pattern.search(detail_url):
            continue
        if needle and needle not in f"{title} {detail_url}".casefold():
            continue
        if detail_url in seen:
            continue
        seen.add(detail_url)
        records.append({"title": title, "detail_url": detail_url, "source_url": detail_url})
        if len(records) >= limit:
            break
    return records


def extract_detail(html: str, url: str) -> dict[str, object]:
    document = parse_html(html)
    text = document.text
    date_matches = re.findall(r"20\d{2}[年/-]\d{1,2}[月/-]\d{1,2}日?", text)
    publish_date = date_matches[0] if date_matches else None
    effective_date = next((item for item in date_matches[1:] if "施行" in text), None)
    source_match = re.search(r"(?:来源|发布机关|制定机关)[：:]\s*([^，。;；]{2,80})", text)
    status_match = re.search(r"(现行有效|已修改|已废止|尚未生效|失效|有效)", text)
    return {
        "title": document.title or (document.links[0].text if document.links else ""),
        "detail_url": url,
        "source_url": url,
        "content": text,
        "publish_date": publish_date,
        "effective_date": effective_date,
        "issuing_body": clean_text(source_match.group(1)) if source_match else None,
        "status": status_match.group(1) if status_match else "未标注",
        "links": [{"href": link.href, "text": link.text} for link in document.links],
    }
