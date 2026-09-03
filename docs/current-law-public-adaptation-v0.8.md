# v0.8.0 现行法公开适配

## 目标

v0.8.0 将现行法研究公开能力收敛为一个可审计、可独立维护的公开适配层。T-05 的默认执行器是 `cn-legal-research`；`cn-law-hub` 仅保留兼容的元数据、查询计划和 authority record 能力：

- 登记可核验的官方法源入口和法源类型范围；
- 根据法律命题、规范名称和条号生成官方检索计划；
- 对 authority record 的必备字段、效力状态、版本日期、官方 HTTPS 来源和来源/法源类型绑定进行确定性校验；
- 在实际使用环境中访问官方来源，处理详情、预览、条文、下载、跨法规搜索和来源适配；不把来源数据、缓存、凭据或第三方 SDK 打进公开安装包。

## 公开接口

```bash
python3 skills/cn-law-hub/scripts/build_authority_queries.py \
  "合同违约金调整" \
  --name "民法典" \
  --article "第五百八十五条"
```

该兼容命令输出五条通用搜索线索和十个登记官方来源的逐源查询计划。默认执行器应使用 `cn-legal-research` 的 CLI；搜索结果只能作为线索，正式引用必须打开官方原文并记录访问时间、版本、效力、条号和时间适用。

```bash
python3 skills/cn-legal-research/scripts/download.py --search "合同违约金调整" --exact --json
python3 skills/cn-legal-research/scripts/article_search.py "违约金" --range content --max-laws 5 --context 1
```

`cn-legal-research` 还提供国家法律法规数据库的详情、预览、条文和下载接口，以及国家规章、条约、国务院政策、司法部、党内法规、国防、税务、生态环境和最高人民法院发布栏目适配。下载与批量采集必须由调用者明确指定输出路径，并遵守官方访问控制和限速。

```bash
python3 skills/cn-legal-research/scripts/validate_authority_records.py record.json
```

当前默认验证器要求 `document_number`、`promulgated_date`、`effective_date` 等字段存在；未知值可以明确使用 `null`，但不能删除字段。`verified-source` 只能使用登记的 HTTPS 官方来源，且来源主机必须与 `authority_type` 匹配。旧调用方仍可显式使用 `cn-law-hub` 的同形兼容验证器。

## 与案例研究的关系

T-05 仍然按输入类型分流：

- `current-law-research` → `cn-legal-research`；
- `case-research` → `cn-case-hub`。

`cn-law-hub` 仍可显式用于旧调用方的元数据、查询计划和 authority record 兼容校验，但不是 T-05 默认入口。

案例研究可以提出需要核验的法源命题，但不能把案例摘要、搜索摘要或模型记忆直接当作现行法依据。诉讼、合同和其他实体工作流仍然是研究结果的主工作流。

## 公开边界

本公开适配不复制或重新分发第三方爬虫、商业数据库 SDK、外部站点数据或私有运行时；可选 MCP 接口为独立的标准库 JSON-RPC 实现。官方来源是运行时检索数据来源，不是 Legal OS 所有的法规数据库；访问受限时必须记录 `blocked` 并停止，不得绕过控制。

## 限制

来源登记覆盖面不等于全国法律或裁判文书的穷尽覆盖。地方规范、历史版本、司法解释的时间适用和案例关联度仍需针对具体事项逐项核验。该适配也不构成法律意见。
