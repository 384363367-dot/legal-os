# Authority record contract

Each formal legal proposition should be recorded with at least:

```text
检索命题：
法源名称/文号：
文件类型：
来源数据库及官方 URL：
发布/制定机关：
发布日期：
施行日期：
效力状态：
条文/原文定位：
与命题的关系：直接依据 / 相关依据 / 仅为线索
未核事项与限制：
检索日期：
```

For machine validation, use the same record shape accepted by `scripts/validate_authority_records.py`:

```json
{
  "title": "示例规范",
  "authority_type": "law",
  "issuing_body": "制定机关",
  "document_number": null,
  "promulgated_date": "2026-01-01",
  "effective_date": "2026-02-01",
  "status": "effective",
  "proposition": "待核验的法律命题",
  "source_url": "https://flk.npc.gov.cn/",
  "accessed_at": "2026-09-02",
  "verification_status": "verified-metadata-only",
  "limitations": ["条文原文尚待打开核验"],
  "supersedes": [],
  "superseded_by": []
}
```

`verified-source` requires an HTTPS URL whose host and authority type match the source registry. If the official page does not state an effect status or date, preserve that absence as `未标注`/`未找到`/`待核验`; do not infer it from a downloadable file or page recency.
