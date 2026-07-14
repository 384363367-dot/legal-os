---
name: legal-os-contract
description: Legal OS合同工作台。用于中国法语境下的合同审核、风险扫描、甲方或乙方立场判断、逐字逐句最小颗粒度修订、真实Word修订痕迹、清洁版、合同履行风险和文件质量门。用户说审核合同、修改合同、出修订版、清洁版、保留修订痕迹、从甲方或乙方角度处理，或提供DOCX合同要求直接交付时使用。
---

# Legal OS Contract Workspace

## 当前边界

P0-R1 仅供用户本人在本机 Codex 中受控使用。合同能力是 `tool-assisted-pilot`，不是无人值守法律服务；旧 Frozen 文档只作治理与规则来源，不代表真实合同结果已通过端到端验证。

## 必须组合使用

- 修改 DOCX 时同时使用 `documents`，执行 render → inspect → iterate；批注另做 OOXML 结构检查。
- 正式或高风险交付前使用 `legal-quality-gate`，并运行本 Skill 的 `scripts/release_gate.py`。
- 需要现行中国法时使用 `cn-law-hub`；合同事实只来自当次材料。

## 受控工作流

1. 建立 matter manifest：登记事项、我方立场、阶段、风险、输出意图、全部文件版本和原件 SHA-256。原件只读，派生文件另存。
2. 读取合同、附件、报价、澄清、补充协议及履行材料；不同版本不得静默合并，缺失事实保持待核验。
3. 建立交易模型与付款—交付—验收—质保—违约—解除闭环，只加载触发的问题域。
4. 形成事项级 negotiation policy。比例、期限、责任上限等商业参数必须来自用户当次指示、事项材料或已批准策略；不得使用隐藏全局默认值。
5. 先形成目标清洁文本，再用 `scripts/minimal_redline.py` 生成字符／词语级真实修订。人工 `old/new` 整句替换只能是临时中间态。
6. 全部正文修订完成后再添加批注；锚定后不得继续替换同一段文字。
7. 运行红线硬门；任一错误只能保留 Draft。长修订必须完成精确台账和具名人工批准。
8. 完成内容、金额、OOXML、渲染、可访问性及隐私检查，再运行 release gate。只有脚本 `PASS`、退出码 `0` 且所需签核匹配当前文件哈希时，才可标 Final。
9. 用户纠正只记录为 Learning Observation／Rule Candidate，不自动改写全局规则或绕过质量门。

详细标准见 [runtime.md](references/runtime.md) 和 [redline-quality.md](references/redline-quality.md)。

## 逐字逐句硬规则

- 能改一字，不改一句；能改一句，不改一段。未变化文字不得进入 `w:del`／`w:ins`。
- 原文缺少必要机制，或局部修补无法形成完整可执行条款时，可以整句或整段新增。
- 15 字符是人工例外台账的触发阈值，不是长条款禁令。每个超过 15 字符的连续新增／删除必须精确绑定 fragment ID、位置、完整文字、原文上下文、结果段落、缺口和必要性，并由具名人员批准。
- 长新增只允许 `necessary_addition` 或 `structural_completion`；长删除只允许 `necessary_deletion`。原文已有同一机制时，必须回到局部修改，不能借例外整句润色。
- 修订作者默认“法务”。`redline_metrics.py` 仅作诊断，正式结论只认 `redline_quality_gate.py`。

## 必跑命令

```bash
python scripts/migrate_change_ledger.py \
  --original ORIGINAL.docx --redline REDLINE.docx \
  --old-ledger OLD.json --output LEDGER_V2.json --review-md REVIEW.md

python scripts/redline_quality_gate.py \
  --original ORIGINAL.docx --redline REDLINE.docx --clean CLEAN.docx \
  --ledger LEDGER_V2.json --out-json REDLINE_REPORT.json

python scripts/release_gate.py \
  --artifact REDLINE.docx --output-path DELIVERY.docx \
  --intent external-final --risk-level R2 --contract \
  --redline-report REDLINE_REPORT.json --matter-manifest MATTER.json \
  --signoff SIGNOFF.json --out-json RELEASE_REPORT.json
```

若没有长片段，可省略 ledger；如果迁移工具输出 `REVIEW_REQUIRED`，不得自动批准。

## 默认输出

- 内部审核：结论、核心风险、必须修改、建议文字、业务动作和待核事项。
- Word：修订版 + 清洁版；保留原结构、编号、表格和版式。
- Final：仅限签核哈希、用途和风险等级完全匹配的版本；发送、签署、提交或发布仍需单独授权。

## 硬停止

- 我方立场、关键版本、付款／验收／权利处分材料存在核心冲突；
- 需要现行法律但未核验，或正式案件观点无可核验来源；
- 原文拒绝本次修订后的视图与源合同不一致；
- 接受修订后的视图与清洁版不一致；
- 长修订未精确批准、批注引用／范围锚点异常、渲染未目检；
- `redline_quality_gate.py` 或 `release_gate.py` 退出码非 `0`。
