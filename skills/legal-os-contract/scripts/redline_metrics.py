#!/usr/bin/env python3
"""Report true DOCX tracked-change counts and length distribution."""
from pathlib import Path
from zipfile import ZipFile
from lxml import etree
import argparse
import json

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

def stats(values):
    values = sorted(values)
    if not values:
        return {"count": 0, "median": 0, "max": 0, "mean": 0, "le5": 0, "le15": 0}
    return {
        "count": len(values),
        "median": values[len(values) // 2],
        "max": max(values),
        "mean": round(sum(values) / len(values), 1),
        "le5": sum(value <= 5 for value in values),
        "le15": sum(value <= 15 for value in values),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("docx")
    parser.add_argument("--max-median-delete", type=int, default=15)
    args = parser.parse_args()
    with ZipFile(args.docx) as archive:
        root = etree.fromstring(archive.read("word/document.xml"))
        settings = archive.read("word/settings.xml")
    insertions = ["".join(node.xpath(".//w:t/text()", namespaces=NS)) for node in root.xpath("//w:ins", namespaces=NS)]
    deletions = ["".join(node.xpath(".//w:delText/text()", namespaces=NS)) for node in root.xpath("//w:del", namespaces=NS)]
    result = {
        "file": str(Path(args.docx)),
        "track_revisions": b"<w:trackRevisions" in settings,
        "insert": stats([len(value) for value in insertions]),
        "delete": stats([len(value) for value in deletions]),
        "authors": sorted(set(root.xpath("//w:ins/@w:author|//w:del/@w:author", namespaces=NS))),
    }
    result["granularity_gate"] = "PASS" if result["track_revisions"] and result["delete"]["count"] and result["delete"]["median"] <= args.max_median_delete else "REVIEW"
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
