#!/usr/bin/env python3
"""Classify public-source records by national, provincial or city-level issuer."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


PROVINCES = (
    "北京市", "天津市", "上海市", "重庆市", "河北省", "山西省", "辽宁省", "吉林省", "黑龙江省",
    "江苏省", "浙江省", "安徽省", "福建省", "江西省", "山东省", "河南省", "湖北省", "湖南省",
    "广东省", "海南省", "四川省", "贵州省", "云南省", "陕西省", "甘肃省", "青海省", "台湾省",
    "内蒙古自治区", "广西壮族自治区", "西藏自治区", "宁夏回族自治区", "新疆维吾尔自治区",
    "香港特别行政区", "澳门特别行政区",
)

PROVINCE_ALIASES = {
    "北京": "北京市", "天津": "天津市", "上海": "上海市", "重庆": "重庆市", "内蒙古": "内蒙古自治区",
    "广西": "广西壮族自治区", "西藏": "西藏自治区", "宁夏": "宁夏回族自治区", "新疆": "新疆维吾尔自治区",
    "黑龙江": "黑龙江省", "吉林": "吉林省", "辽宁": "辽宁省", "河北": "河北省", "山西": "山西省",
    "江苏": "江苏省", "浙江": "浙江省", "安徽": "安徽省", "福建": "福建省", "江西": "江西省",
    "山东": "山东省", "河南": "河南省", "湖北": "湖北省", "湖南": "湖南省", "广东": "广东省",
    "海南": "海南省", "四川": "四川省", "贵州": "贵州省", "云南": "云南省", "陕西": "陕西省",
    "甘肃": "甘肃省", "青海": "青海省", "台湾": "台湾省", "香港": "香港特别行政区", "澳门": "澳门特别行政区",
}

CITY_TO_PROVINCE = {
    "广州市": "广东省", "深圳市": "广东省", "珠海市": "广东省", "佛山市": "广东省", "东莞市": "广东省",
    "杭州市": "浙江省", "宁波市": "浙江省", "南京市": "江苏省", "苏州市": "江苏省", "厦门市": "福建省",
    "福州市": "福建省", "济南市": "山东省", "青岛市": "山东省", "郑州市": "河南省", "武汉市": "湖北省",
    "长沙市": "湖南省", "成都市": "四川省", "西安市": "陕西省", "昆明市": "云南省", "贵阳市": "贵州省",
    "兰州市": "甘肃省", "西宁市": "青海省", "太原市": "山西省", "石家庄市": "河北省", "沈阳市": "辽宁省",
    "长春市": "吉林省", "哈尔滨市": "黑龙江省", "南昌市": "江西省", "海口市": "海南省", "合肥市": "安徽省",
    "呼和浩特市": "内蒙古自治区", "银川市": "宁夏回族自治区", "乌鲁木齐市": "新疆维吾尔自治区", "拉萨市": "西藏自治区",
    "南宁市": "广西壮族自治区", "唐山市": "河北省", "温州市": "浙江省", "无锡市": "江苏省", "烟台市": "山东省",
    "延边朝鲜族自治州": "吉林省", "临夏回族自治州": "甘肃省", "甘南藏族自治州": "甘肃省",
    "昌吉回族自治州": "新疆维吾尔自治区", "博尔塔拉蒙古自治州": "新疆维吾尔自治区",
    "伊犁哈萨克自治州": "新疆维吾尔自治区", "克孜勒苏柯尔克孜自治州": "新疆维吾尔自治区",
    "巴音郭楞蒙古自治州": "新疆维吾尔自治区", "海西蒙古族藏族自治州": "青海省",
    "恩施土家族苗族自治州": "湖北省", "湘西土家族苗族自治州": "湖南省",
    "黔东南苗族侗族自治州": "贵州省", "黔南布依族苗族自治州": "贵州省",
    "黔西南布依族苗族自治州": "贵州省", "阿坝藏族羌族自治州": "四川省",
    "凉山彝族自治州": "四川省", "红河哈尼族彝族自治州": "云南省",
    "文山壮族苗族自治州": "云南省", "大理白族自治州": "云南省",
    "西双版纳傣族自治州": "云南省", "迪庆藏族自治州": "云南省", "怒江傈僳族自治州": "云南省",
}


def _find_province(text: str) -> str | None:
    for name in sorted(PROVINCES, key=len, reverse=True):
        if name in text:
            return name
    for alias, name in sorted(PROVINCE_ALIASES.items(), key=lambda pair: len(pair[0]), reverse=True):
        if alias in text:
            return name
    return None


def _find_city(text: str) -> str | None:
    for city in sorted(CITY_TO_PROVINCE, key=len, reverse=True):
        if city in text:
            return city
    for suffix in ("自治州", "地区", "盟"):
        for part in text.replace("、", " ").split():
            if suffix in part:
                return part[: part.index(suffix) + len(suffix)]
    return None


def classify_by_authority(authority: str, title: str = "") -> dict[str, object]:
    authority = str(authority or "").strip()
    title = str(title or "").strip()
    combined = authority + " " + title
    if not authority and not title:
        return {"level": "unknown", "province": None, "city": None, "authority": authority, "title": title}
    if any(marker in combined for marker in ("国务院", "全国人民代表大会", "最高人民法院", "最高人民检察院", "中央人民政府")):
        return {"level": "national", "province": "全国", "city": "全国", "authority": authority, "title": title}
    province = _find_province(combined)
    city = _find_city(combined)
    if city and not province:
        province = CITY_TO_PROVINCE.get(city)
    if city:
        level = "city"
    elif province:
        level = "provincial"
    else:
        level = "unknown"
    return {"level": level, "province": province, "city": city, "authority": authority, "title": title}


def classify_search_results(items: list[dict[str, Any]], authority_key: str = "authority", title_key: str = "title") -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for item in items:
        row = dict(item)
        row.update({f"classified_{key}": value for key, value in classify_by_authority(row.get(authority_key, ""), row.get(title_key, "")).items() if key in {"level", "province", "city"}})
        output.append(row)
    return output


def build_existence_matrix(items: list[dict[str, Any]], province_key: str = "classified_province", title_key: str = "title") -> list[dict[str, object]]:
    matrix: dict[str, dict[str, object]] = {}
    for item in items:
        province = str(item.get(province_key) or "未分类")
        row = matrix.setdefault(province, {"province": province, "count": 0, "titles": []})
        row["count"] = int(row["count"]) + 1
        if len(row["titles"]) < 20:
            row["titles"].append(str(item.get(title_key) or ""))
    return [matrix[key] for key in sorted(matrix)]


def save_classified_items(items: list[dict[str, Any]], output_path: Path | str) -> Path:
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def save_existence_matrix(matrix: list[dict[str, object]], output_path: Path | str) -> Path:
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["province", "count", "titles"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in matrix:
            writer.writerow({"province": row.get("province", ""), "count": row.get("count", 0), "titles": " | ".join(row.get("titles", []))})
    return path


def _self_test() -> int:
    cases = [
        ("国务院", "national", "全国", "全国"),
        ("北京市人民代表大会常务委员会", "provincial", "北京市", None),
        ("广州市人民代表大会常务委员会", "city", "广东省", "广州市"),
        ("临夏回族自治州人大常务委员会", "city", "甘肃省", "临夏回族自治州"),
        ("", "unknown", None, None),
    ]
    failures = []
    for authority, expected_level, expected_province, expected_city in cases:
        result = classify_by_authority(authority)
        ok = result["level"] == expected_level and result["province"] == expected_province and (expected_city is None or result["city"] == expected_city)
        print(f"[{ 'PASS' if ok else 'FAIL' }] {authority!r} -> {result}")
        if not ok:
            failures.append(authority)
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help"}:
        print(__doc__)
        print("Usage: region_classifier.py --test | --classify [output.json] | --matrix output.csv")
        return 0
    if args[0] == "--test":
        return _self_test()
    if args[0] == "--classify":
        items = json.load(sys.stdin)
        classified = classify_search_results(items)
        rendered = json.dumps(classified, ensure_ascii=False, indent=2) + "\n"
        if len(args) > 1:
            save_classified_items(classified, args[1])
        else:
            print(rendered, end="")
        return 0
    if args[0] == "--matrix" and len(args) > 1:
        items = json.load(sys.stdin)
        save_existence_matrix(build_existence_matrix(classify_search_results(items)), args[1])
        return 0
    print("Unknown command. Use --help.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
