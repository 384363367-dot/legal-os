"""DOCX paragraph and article helpers using only the standard library."""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
ARTICLE_RE = re.compile(r"^\s*第\s*([0-9０-９一二三四五六七八九十百千万零〇两]+)\s*条")


def _zip_source(source: bytes | bytearray | Path | str) -> zipfile.ZipFile:
    if isinstance(source, (bytes, bytearray)):
        return zipfile.ZipFile(io.BytesIO(source))
    return zipfile.ZipFile(Path(source))


def extract_docx_paragraphs(source: bytes | bytearray | Path | str) -> list[str]:
    with _zip_source(source) as package:
        if "word/document.xml" not in package.namelist():
            raise ValueError("DOCX package has no word/document.xml")
        root = ET.fromstring(package.read("word/document.xml"))
    paragraphs: list[str] = []
    for paragraph in root.findall(".//w:p", NS):
        pieces: list[str] = []
        for node in paragraph.iter():
            local = node.tag.rsplit("}", 1)[-1]
            if local in {"t", "delText", "instrText"}:
                pieces.append(node.text or "")
            elif local == "tab":
                pieces.append("\t")
            elif local == "br":
                pieces.append("\n")
        text = "".join(pieces).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def extract_xml_paragraphs(source: bytes | bytearray | Path | str) -> list[str]:
    """Extract paragraph-like text from a standalone XML document.

    This is intentionally conservative: it understands common ``p``/``t``
    and WordprocessingML ``w:p``/``w:t`` shapes, but does not treat arbitrary
    XML text as a legal article without a paragraph boundary.
    """
    if isinstance(source, (bytes, bytearray)):
        raw = bytes(source)
    else:
        raw = Path(source).read_bytes()
    root = ET.fromstring(raw)
    paragraphs: list[str] = []
    for paragraph in root.iter():
        if paragraph.tag.rsplit("}", 1)[-1].lower() != "p":
            continue
        pieces: list[str] = []
        for node in paragraph.iter():
            local = node.tag.rsplit("}", 1)[-1].lower()
            if local in {"t", "text", "content", "deltext", "instrtext"}:
                pieces.append(node.text or "")
            elif local == "tab":
                pieces.append("\t")
            elif local == "br":
                pieces.append("\n")
        text = "".join(pieces).strip()
        if text:
            paragraphs.append(text)
    return paragraphs


def extract_xml_articles(source: bytes | bytearray | Path | str) -> list[tuple[str, str]]:
    """Parse article sections from a standalone XML document."""
    return split_into_articles(extract_xml_paragraphs(source))


def chinese_numeral_to_int(value: str) -> int | None:
    value = value.translate(str.maketrans("０１２３４５６７８９", "0123456789"))
    if value.isdigit():
        return int(value)
    digits = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    units = {"十": 10, "百": 100, "千": 1000, "万": 10000}
    if not value or any(ch not in digits and ch not in units for ch in value):
        return None
    total = 0
    section = 0
    number = 0
    for char in value:
        if char in digits:
            number = digits[char]
        else:
            unit = units[char]
            if unit == 10000:
                section += number
                total += section * unit
                section = 0
                number = 0
            elif number:
                section += number * unit
                number = 0
            else:
                section += unit if unit == 10 else 0
    return total + section + number


def article_number(label: str) -> int | None:
    match = ARTICLE_RE.match(label)
    return chinese_numeral_to_int(match.group(1)) if match else None


def split_into_articles(paragraphs: list[str]) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_label = "前言"
    current: list[str] = []
    for paragraph in paragraphs:
        if ARTICLE_RE.match(paragraph):
            if current:
                sections.append((current_label, "\n".join(current)))
            current_label = paragraph.split("。", 1)[0]
            current = [paragraph]
        else:
            current.append(paragraph)
    if current:
        sections.append((current_label, "\n".join(current)))
    return sections


def match_article_query(query: str, label: str) -> bool:
    query_number = chinese_numeral_to_int(query.strip().removeprefix("第").removesuffix("条"))
    return query_number is not None and article_number(label) == query_number


def detect_numbering(paragraphs: list[str]) -> dict[str, object]:
    chinese = any(re.match(r"^\s*第[一二三四五六七八九十百千万零〇两]+条", value) for value in paragraphs)
    arabic = any(re.match(r"^\s*第\d+条", value) for value in paragraphs)
    primary = "mixed" if chinese and arabic else "chinese" if chinese else "arabic" if arabic else "unknown"
    return {
        "primary": primary,
        "has_chinese": chinese,
        "has_arabic": arabic,
        "sample_titles": [value for value in paragraphs if ARTICLE_RE.match(value)][:5],
    }
