---
name: cn-legal-research
description: Standard-library official-source research adapter for Chinese laws, regulations, treaties, policies, and article-level text retrieval with explicit source and access controls.
---

# 中国官方法源检索适配

这是一个公开的、基于 Python 标准库的官方来源访问适配。它把检索、详情、预览、条文定位、有限批量搜索、文件下载、地域分类和可选 JSON-RPC/MCP 风格接口放在同一个可核验边界内。它不打包法规正文、缓存、凭据或登录状态，也不声称拥有官方法规数据库。

## 路由定位

在公开包中，T-05 的 `current-law-research` 默认执行器是本 Skill；`case-research` 仍交 `cn-case-hub`。`cn-law-hub` 只为旧调用方保留兼容/过渡的元数据、查询计划和 authority-record 校验，不是现行法检索的默认入口。

## 职责边界

- 负责把法律问题转成官方来源检索，并保留标题、规范类型、机关、日期、效力状态、条文定位和访问地址。
- 支持法律、行政法规、地方性法规、规章、司法解释、条约、政策文件、党内法规以及指定部门官方发布材料的来源适配。
- 案例、裁判文书、裁判观点和本案诉讼策略分别交 `cn-case-hub`、`legal-os-litigation` 或对应主工作流。
- 检索结果必须回到实际打开的官方原文或详情页；搜索摘要、模型记忆和第三方摘要只能作为线索。

## 安全与公开边界

1. 默认只接受已登记的 HTTPS 官方来源；重定向到未登记主机时停止。
2. 不携带 `Authorization`、Cookie、登录状态或第三方凭据，不绕过验证码、robots、访问控制或限速。
3. 缓存只有在调用方显式提供缓存目录时启用；默认不写入用户目录或 Skill 源码目录。
4. 下载必须写入调用方明确指定的输出路径，不把法规数据、下载结果或缓存提交进仓库。
5. 在线执行由用户在有权限的环境中明确发起；本公开包的测试使用离线 mock/fixture，不自动联网。
6. 官方网站和法规内容是外部来源；本项目只维护适配器、来源元数据和解析逻辑，不主张对官方内容或数据库的所有权。

## 工作流

1. 写明检索命题、法域/地区、规范层级、事实与程序时间以及需要的条文或法律效果。
2. 选择登记的来源与检索范围；标题检索优先于正文检索，存在版本歧义时标记 `VERSION_UNRESOLVED`。
3. 使用 `scripts/` 中的来源适配器获得搜索、详情或下载结果；调用前先运行对应脚本的 `--help`。
4. 对官方原文核对机关、文号、公布日期、施行日期、状态、修改/废止关系和条号；缺失字段明确写 `未标注` 或 `待核验`。
5. 使用 `references/authority-record.md` 形成可审计记录，并运行本 Skill 的 `scripts/validate_authority_records.py`；旧调用方可以显式使用 `cn-law-hub` 的兼容验证器。
6. 将“已访问官方来源”“仅元数据”“线索”与事实、证据、推论和专业判断分开回流主工作流。

## 能力入口

| 入口 | 主要能力 |
|---|---|
| `scripts/download.py` | 国家法律法规数据库的搜索、详情、下载、预览、条文与正文关键词定位 |
| `scripts/article_search.py` | 跨法规正文/条文关键词搜索 |
| `scripts/gov_rules_crawler.py` | 国家规章库的搜索、详情和下载 |
| `scripts/treaty_crawler.py` | 外交部条约库的集合、详情和公开预览文件 |
| `scripts/gov_policy_library.py` | 国务院政策文件库的标题/正文、年份和部门筛选 |
| `scripts/moj_law_crawler.py` | 司法部行政法规库的搜索和详情 |
| `scripts/party_law_crawler.py` | 党内法规公开栏目搜索和详情 |
| `scripts/mod_law_crawler.py` | 国防领域公开法规栏目搜索和详情 |
| `scripts/tax_law_crawler.py` | 税务法规公开栏目搜索和详情 |
| `scripts/mee_law_crawler.py` | 生态环境法规规章公开栏目搜索和详情 |
| `scripts/court_law_crawler.py` | 最高人民法院发布栏目搜索和详情；不是完整案例库 |
| `scripts/region_classifier.py` | 按机关与标题对搜索结果进行国家/省/市级地域分类 |
| `scripts/mcp_server.py` | 无第三方 SDK 的可选 JSON-RPC stdio 工具入口；仍受同一官方来源边界约束 |

## 停止条件

- 找不到官方原文或详情页：返回 `BLOCKED_BY_SOURCE`，不得把摘要标成已核验法源。
- 同一规范存在多个版本但适用版本无法确认：返回 `VERSION_UNRESOLVED`。
- 来源主机、效力状态、条号、机关或日期冲突：并列记录冲突并停止确定性结论。
- 官方站点真实返回登录、验证码、访问拒绝或其他访问控制：记录限制并停止，不绕过。

## 来源与许可证说明

本目录的代码和文档是独立的标准库实现，未打包外部法规数据、第三方 SDK、复制的爬虫源代码或登录凭据。根目录 Apache-2.0 许可适用于本仓库可许可的原创代码；外部官方站点、页面、法规和文件仍受其自身法律和访问条件约束。必要的来源说明见 `NOTICE`、`references/source-registry.md` 和 `references/feature-coverage.md`。
