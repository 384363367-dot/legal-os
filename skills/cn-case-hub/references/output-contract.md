# 案例记录、双轴矩阵与裁判分叉变量规范

## 案例记录

未知值使用 `null` 或 `[]`，不得猜测。v0.7.0 在兼容旧字段的基础上增加双轴分类与程序链字段。

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
  "procedure_chain_id": null,
  "procedure_chain": [],
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
  "relevance_grade": "A | B | C | D",
  "direction_grade": "+ | ± | 0 | -",
  "matrix_grade": "A+ | A± | A0 | A- | B+ ...",
  "decisive_variables": [],
  "current_law_check": null,
  "source_url": "https://...",
  "source_locator": null,
  "accessed_at": "YYYY-MM-DD",
  "limitations": []
}
```

旧记录没有 v0.7.0 扩展字段时仍可进入兼容模式；一旦用于新的正式类案报告，建议补齐三项矩阵字段。

## 裁判分叉变量记录

```json
{
  "variable": "可能改变裁判结果的事实/证据/法律条件",
  "supporting_cases": [],
  "adverse_cases": [],
  "matter_status": "confirmed | disputed | unknown | not-applicable",
  "evidence_status": "supported | partial | missing | conflicting",
  "likely_effect": "对裁判方向的可能影响，必须基于案例比较而非概率猜测",
  "action": "补证、区分案例、调整请求/抗辩或继续检索"
}
```

## 验证状态

- `verified-source`：已打开官方原文并核对支撑记录的字段；
- `verified-metadata-only`：只核对官方元数据；
- `official-summary`：官方典型案例或摘要，只按公开范围使用；
- `lead-only`：线索，不能支持正式结论；
- `blocked`：访问受限。

## 类案报告顺序

1. 结论摘要与检索边界；
2. 检索策略和访问日期；
3. 3—5 个核心案例；
4. 双轴矩阵；
5. 裁判分叉变量；
6. `A-` 等不利案例；
7. 本案证据/事实缺口；
8. 当前法源衔接；
9. Verification Notes。

## 引用纪律

- 案号、法院、日期、程序链必须来自实际核验材料；
- 法院观点、发布机关概括、研究者推断必须分开；
- 重要裁判理由应记录原文定位信息；
- 不把检索命中数量称为胜诉率；
- 不隐藏高相关不利案例。
