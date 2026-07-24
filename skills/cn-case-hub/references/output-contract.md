# 案例记录与类案报告规范

## 案例记录

案例记录使用以下字段；未知值用 `null` 或 `[]`，不得猜测：

```json
{
  "title": "案例名称",
  "source_type": "guiding-case | database-reference | gazette-case | judgment | typical-case | official-interpretation | lead",
  "source_grade": "A1 | A2 | B | C | D",
  "verification_status": "verified-source | verified-metadata-only | official-summary | lead-only | blocked",
  "issuing_body": "发布机关",
  "database_number": null,
  "case_numbers": [],
  "courts": [],
  "decision_dates": [],
  "publication_date": null,
  "cause": null,
  "procedural_posture": null,
  "issues": [],
  "key_facts": [],
  "holding": null,
  "result": null,
  "direction": "supports | adverse | mixed | neutral",
  "similarity": {
    "overall": "high | medium | low",
    "legal_relationship": "high | medium | low",
    "issue": "high | medium | low",
    "key_facts": "high | medium | low",
    "procedure_and_level": "high | medium | low",
    "time_and_law": "high | medium | low",
    "reason": "简要理由"
  },
  "current_law_check": null,
  "source_url": "https://...",
  "accessed_at": "YYYY-MM-DD",
  "limitations": []
}
```

## 验证状态

- `verified-source`：已打开官方原文并核对支撑本记录的字段。
- `verified-metadata-only`：只核对了官方元数据，未取得足以概括实体内容的正文。
- `official-summary`：官方典型案例或新闻摘要；按其公开范围使用。
- `lead-only`：搜索或二手材料线索，不能支持正式结论。
- `blocked`：被登录、验证码、维护或权限阻断。

## 类案报告顺序

1. 结论摘要：最相关案例、主要裁判分歧、检索边界。
2. 检索策略：争点、关键词、来源和访问日期。
3. 案例矩阵：正向、反向、混合案例并列。
4. 重点案例：关键事实、裁判理由、结果、相似度、用途、限制。
5. 当前法源衔接：现行法、司法解释及可能冲突。
6. 证据/事实缺口：哪些事实会改变相似度或结论。
7. Verification Notes。

## 引用纪律

- 案号、法院、日期只能从实际访问的官方材料抄录。
- 区分法院“认为”、最高法发布机关“概括”和检索者“推断”。
- 不大段复制原文；用准确释义并紧邻官方链接。
- 不把案例数量、命中数或排序当成裁判趋势，除非检索范围和样本方法足以支持。
