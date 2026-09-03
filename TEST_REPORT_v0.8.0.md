# Legal OS v0.8.0 发布前测试报告

状态：本报告记录公开预发布前的本地可复核结果；在线官方来源访问、外部发布动作和视觉渲染均不在本次离线门内。

## 测试环境与范围

- Python：使用当前环境的 `python3`；适配器和测试仅依赖 Python 标准库。
- 网络：适配器测试使用 mock/fixture，不访问外部网站，不下载法规正文，不写入默认缓存。
- 范围：manifest、公开文档/链接、15 个 Skill、T-01 至 T-12 路由、`cn-legal-research` 运行时、authority record、十源登记、MCP 工具清单、13 个候选 DOCX、24 个模板哈希和全仓回归。

## 固定门禁

```bash
python3 scripts/validate_public_surface.py
python3 scripts/validate_repo.py
python3 scripts/validate_routing_scenarios.py
python3 skills/cn-legal-research/scripts/check_first_party_boundary.py
python3 -m unittest discover -s tests -v
./install.sh --dry-run --target /private/tmp/legalos-public-candidate-install-dryrun-20260903
```

实测结果（2026-09-03）：

- `validate_public_surface.py`：PASS；
- `validate_repo.py`：PASS；
- `validate_routing_scenarios.py`：PASS（16 个合成场景）；
- `cn-legal-research/scripts/check_first_party_boundary.py`：PASS；
- `python3 -m unittest discover -s tests -v`：75 项通过；
- `./install.sh --dry-run --target /private/tmp/legalos-public-candidate-install-dryrun-20260903`：15 个 Skill，全部列出，退出码 `0`；显式临时目标避免触碰默认已存在的用户 Skill 目录。

## `cn-legal-research` 定向覆盖

- 十个登记官方来源、来源类型绑定和税务 API 官方主机均通过离线登记检查；未把任何来源正文、缓存、凭据或下载文件打入公开包；
- T-05 `current-law-research` → `cn-legal-research`；`cn-law-hub` 仅为显式兼容/过渡路径；
- 国家法律法规数据库的搜索 payload、详情字段、预览、条文定位、跨法规文章匹配和显式输出路径有标准库测试；
- 国家规章、条约、国务院政策、司法部、党内法规、国防、税务、生态环境和最高人民法院发布栏目的适配入口、分类参数或 HTML/JSON 解析逻辑均已纳入公开 Skill；
- HTML、JSON、DOCX/XML 合成解析、地域分类、authority record、缓存、限速/重定向边界、MCP JSON-RPC 工具清单和外链过滤有离线测试；
- 访问拒绝、重定向离开登记主机、来源字段缺失或版本冲突时，适配器保留阻断/待核验状态，不把线索升级为 `verified-source`。

## DOCX 源文件检查

- 13 个候选 DOCX 均为可打开的 ZIP/OOXML 包，必需包部件和关系可读；
- 13 个候选路径的公共文件 SHA-256 与模板目录绑定值一致；
- 已检查正文段落、表格、编号、样式、页眉/页脚和包级关系/宏/嵌入/修订等结构性特征；未重建文件、未改写正文、未默认渲染；
- 13 个候选均保持 `candidate` 状态，模板候选不等于已启用、已替换或已发布。

## 未验证项与剩余风险

- 未在线访问十类官方站点；真实站点的认证参数、页面字段、分类路径、限速、访问条款和当前有效性仍需在获准环境中逐项验证；
- 未运行 PDF/OCR、原生 Office 视觉预览或打印检查；当前没有明确视觉触发，DOCX 以包结构/源文件保真为主；
- 在本报告所覆盖的离线门禁阶段，尚未执行提交、推送、PR、合并、打 tag 或 Release；本报告本身不构成外部发布结果证明；
- `NOTICE`/署名记录来源边界，不单独构成第三方代码再分发许可；当前公开适配采用独立标准库实现，后续如引入外部组件必须重新完成许可和来源核验；
- 官方内容、法规效力、时间适用、真实性、证据能力和法律结论仍须由具体事项的法律工作流和有权人员核验。
