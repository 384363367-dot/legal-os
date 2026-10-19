# Legal OS v0.8.4 验证记录

执行日期：2026-10-19，Python 3.12.12。对象为本仓库独立标准库实现；其他实现的测试数字不作为本版通过证据。公开预发布版，非稳定版；本记录不证明外部 Tag/Release 已创建。

## 离线验证

| 命令 | 实际结果 |
| --- | --- |
| `python scripts/validate_public_surface.py` | PASS |
| `python scripts/validate_repo.py` | PASS |
| `python scripts/validate_routing_scenarios.py` | PASS，16 个合成路由场景 |
| 三个公开研究 Skill 的 `check_first_party_boundary.py` | PASS |
| `./install.sh --dry-run --target <caller-owned-directory>` | PASS，15 个 Skill；未实际安装 |
| `python -m unittest discover -s tests -v` | PASS，110 项 |
| `python -m unittest discover -s skills/legal-os-contract/tests -v` | PASS，50 项 |
| `python -m unittest discover -s skills/legal-quality-gate/tests -v` | PASS，75 项 |
| `python -m unittest discover -s skills/legal-os-unified-intake/tests -v` | PASS，5 项 |
| `python -m pip check` | PASS |
| `git diff --check` | PASS |

原有仓库基线 92 项测试通过。新增 18 项原创准确性/边界回归；最初 16 项对照在未修改基线上仅 1 项通过，另 15 项失败或报告缺少预期行为；修改后新增 18 项全部通过。覆盖完整标题与官方状态共同核验、缓存响应不原地修改、当前窗口计数、MOJ 查询回显/日期/计数冲突、历史状态不支持、gov-rules 标题 MATCH、条文/题注分计、详情状态再核验、偏移量与终页续查，以及精确主机和默认生产 opener 的预跳转边界。

默认生产 opener 在创建下一跳请求前核验 HTTPS 和当前来源的精确登记主机；跨域、HTTP 与 localhost 跳转合成测试确认拒绝发生在下一跳请求创建前。调用方显式注入自定义 opener 时仍需自行确保其重定向策略；最终响应 URL 的读取前核验保留。

## 本实现真实在线验证

以下为同日对本版的一次有界最终验证组。所有请求使用 TLS、无缓存、明确页数/条数，不把 HTTP 200 本身当作正确命中。公开仓库不分发原始法规数据或下载签名。

| 分支 | 实际结果与边界 |
| --- | --- |
| NPC 民法典完整标题 | 远端 30 候选、本页 20，严格完整标题返回 1 条 |
| NPC 劳动合同法 + 状态 2 | 远端 906 候选、本页 20，验证后 0 条；仅当前页，不推断全库无旧版本 |
| NPC 合同法 + 状态 1 | 远端 3 候选，严格返回已废止合同法 1 条 |
| NPC 上海 AI 条例完整标题 | 本页未命中；明确窗口限制，不放宽条件或声称全库不存在 |
| MOJ 标题 | 命中网络数据安全管理条例，并取得官方当前集合日期/状态 |
| MOJ 正文 | “保障农民工工资”返回官方正文候选；没有把列表命中当作条款适用判断 |
| MOJ 无结果 | 官方计数与页内记录一致为 0，返回空数组 |
| MOJ 历史失效条件 | 明确返回 unsupported，非零退出；不假造历史失效结果 |
| 国家规章库 MATCH | “管理办法”返回 2 条有标题和官方详情的部门规章 |
| 国家规章库已知完整标题空结果 | “道路危险货物运输管理规定”返回 0；保留官方页面回退需要，不宣称法规不存在 |
| NPC 单条 | 个人信息保护法第一条成功提取 1 条 |
| 跨法搜索默认全部状态 | 个人信息保护法窗口取得 70 个编号条文匹配、1 个其他段落匹配 |
| 跨法搜索显式状态 3 | 同一窗口取得 70 个编号条文匹配、1 个其他段落匹配；详情状态再次核验 |
| 题注/前言计数 | 完整通过日期关键词返回 0 个编号条文、1 个其他段落；较宽年份词的另一次查询也命中编号条文，未混作纯题注样本 |

在线访问能证明这些请求当时的响应，不能保证今后站点结构、全库召回、所有来源或法律适用。官方缺失状态字段、未支持集合、访问拒绝和解析异常应继续如实报告。

## 来源、许可与包边界

仅在本仓库原有一方架构内实现通用行为，不复制第三方爬虫源码或测试。保留原有许可与 NOTICE；不包含缓存、凭据、签名参数、具体事项材料或私有配置。精确委托资源主机只用于官方 API 的资源传输，法律身份与效力仍回到官方详情核验。

包校验以 `PACKAGE_MANIFEST.json` 与 `SHA256SUMS.txt` 为准；安装/升级与兼容说明见 `RELEASE_NOTES_v0.8.4.md`。
