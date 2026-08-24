# Authority record

```json
{
  "title": "规范名称",
  "authority_type": "law | administrative-regulation | judicial-interpretation | department-rule | local-regulation | local-rule | treaty | other",
  "issuing_body": "制定/发布机关",
  "document_number": null,
  "promulgated_date": null,
  "effective_date": null,
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

正式法律命题原则上使用 `verified-source`。当版本链或时间适用不能确认时，状态必须保持 `unresolved` 或在 limitations 中说明，不得静默补齐。
