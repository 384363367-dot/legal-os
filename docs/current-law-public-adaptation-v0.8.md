# v0.8.0 现行法公开适配

## 目标

v0.8.0 将现行法研究公开能力收敛为一个可审计、可独立维护的第一方适配层：

- 登记可核验的官方法源入口和法源类型范围；
- 根据法律命题、规范名称和条号生成官方检索计划；
- 对 authority record 的必备字段、效力状态、版本日期、官方 HTTPS 来源和来源/法源类型绑定进行确定性校验；
- 将外部站点访问、登录、验证码、限速、数据保存和具体法条读取留在实际使用环境中，不把来源爬虫、缓存数据或第三方 SDK 打进公开安装包。

## 公开接口

```bash
python3 skills/cn-law-hub/scripts/build_authority_queries.py \
  "合同违约金调整" \
  --name "民法典" \
  --article "第五百八十五条"
```

该命令输出五条通用搜索线索和十个登记官方来源的逐源查询计划。搜索结果只能作为线索；正式引用必须打开官方原文并记录访问时间、版本、效力、条号和时间适用。

```bash
python3 skills/cn-law-hub/scripts/validate_authority_records.py record.json
```

验证器要求 `document_number`、`promulgated_date`、`effective_date` 等字段存在；未知值可以明确使用 `null`，但不能删除字段。`verified-source` 只能使用登记的 HTTPS 官方来源，且来源主机必须与 `authority_type` 匹配。

## 与案例研究的关系

T-05 仍然按输入类型分流：

- `current-law-research` → `cn-law-hub`；
- `case-research` → `cn-case-hub`。

案例研究可以提出需要核验的法源命题，但不能把案例摘要、搜索摘要或模型记忆直接当作现行法依据。诉讼、合同和其他实体工作流仍然是研究结果的主工作流。

## 公开边界

本适配不复制或重新分发任何第三方爬虫、MCP server、商业数据库 SDK、外部站点数据或私有运行时。官方来源是检索数据来源，不是公开包内的代码依赖；访问受限时必须记录 `blocked` 并停止，不得绕过控制。

## 限制

来源登记覆盖面不等于全国法律或裁判文书的穷尽覆盖。地方规范、历史版本、司法解释的时间适用和案例关联度仍需针对具体事项逐项核验。该适配也不构成法律意见。
