# Authority record

```json
{
  "title": "规范名称",
  "authority_type": "law | administrative-regulation | judicial-interpretation | department-rule | local-regulation | local-rule | treaty | other",
  "issuing_body": "制定/发布机关",
  "document_number": null,
  "promulgated_date": "YYYY-MM-DD",
  "effective_date": "YYYY-MM-DD",
  "status": "effective | amended | repealed | expired | pending | unresolved",
  "version_date": null,
  "article": null,
  "proposition": "本次需要验证的法律命题",
  "temporal_application": "为什么这个版本适用于该事实/程序时点",
  "source_url": "https://...",
  "source_locator": null,
  "accessed_at": "YYYY-MM-DD",
  "verification_status": "verified-source | verified-metadata-only | lead-only | blocked",
  "supersedes": [],
  "superseded_by": [],
  "limitations": []
}
```

`document_number`、`promulgated_date` 和 `effective_date` 即使暂时未知也必须保留字段，并使用 `null` 或在 `limitations` 中记录缺口；不得因缺字段而静默补齐。正式法律命题原则上使用 `verified-source`。当版本链或时间适用不能确认时，状态必须保持 `unresolved` 或在 `limitations` 中说明，不得静默补齐。

`verified-source` 记录的 `source_url` 必须使用 `source-registry.md` 登记的 HTTPS 官方来源，并且法源类型必须与来源登记的权限范围一致。搜索引擎摘要、商业数据库和二手文章只能作为线索，不能单独提升为 `verified-source`。
