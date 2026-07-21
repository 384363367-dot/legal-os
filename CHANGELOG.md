# Changelog

本文件记录 Legal OS 公开预发布版本的主要变化。

## [v0.2.0] - Unreleased

### 公开更新提示

- 2026-07-21：在 README 增加醒目的候选版更新摘要和下载口径，明确从 `main` 克隆或 Download ZIP 获得当前候选内容，从 GitHub Releases 获得最近稳定公开版。

### 新增

- 增加 `legalos.manifest.json` 及其 Schema，统一公开版本、profiles、Skills、T-routes、调用策略和质量门清单。
- 为统一入口增加 `route-only` / `route-and-run` 执行契约。
- 增加 15 个合成路由场景以及 G3、外部动作授权、混合任务覆盖测试。
- 增加 `legal-os-template-runtime`、24 个去身份化 Office 模板、哈希绑定注册表、确定性模板解析器和 DOCX 版式审计。
- 新增劳动人事争议仲裁申请书和答辩状专用模板，避免与商事仲裁模板混用；劳动仲裁模板不设置仲裁费用承担请求。
- 所有起诉状、申请书和答辩状改为与独立证据目录成对解析和生成，诉状正文不再设置独立“证据和证据来源”章节。
- 合同诉讼、函件、数据、受理、沟通、交付、汇报和事项记忆工作流统一接入模板解析；无适用模板时返回 `TEMPLATE_REQUIRED`，不得自行设计正式版式。

### 治理

- 明确 `public-generic` 与未公开的 `private-controlled` overlay 边界。
- 由验证器检查 manifest、仓库 Skill 清单、Agent 调用元数据及文档版本投影的一致性。
- 统一 Office 文件质量门：结构化检查优先，macOS Quick Look 原生预览，WPS/经批准的原生应用仅作中文字体、分页、表格、修订显示和打印版式的定向抽检；未经用户明确授权不得切换其他渲染器。
- 增加原生 Office 质量门回归测试，阻止已停用的渲染路径和笼统旧式渲染指令重新进入公开规则或 Skills。
- 明确“固定版式、弹性正文”：模板约束页眉页脚、字体、段落、表格等版式及最低内容骨架，不构成正文内容上限；具体事实、证据、履行节点、法律后果和风险提示应按事项充分展开。

## [v0.1.1] - 2026-07-16

### 修复

- 明确九个可安装公开 Skill 与 T-01 至 T-12 路由之间的对应关系。
- 删除合同工作流中对公开包未附带脚本和参考文件的执行性引用。
- 将证据映射明确为诉讼工作流阶段，将现行法检索和组织级最终发布审批明确为外部依赖。

### 新增

- 增加仓库结构验证器及对应的合成测试。
- 增加 DOCX 修订质量门的通过、缺少修订跟踪和清洁版不一致测试。
- 增加 Python 3.12 GitHub Actions CI、依赖一致性检查和可复现安装说明。

### 安全与发布治理

- 将 `lxml` 升级到 `6.1.0`，修复默认 `iterparse()` 和 `ETCompatXMLParser()` 配置可能读取本地文件的高危 XXE 问题（CVE-2026-41066）。
- 固定第三方 GitHub Actions 的提交 SHA，并关闭 checkout 凭据持久化。
- 增加对缺失本地资源、未打包具名 Skill 依赖、不完整 Agent 元数据和内部 Agent 指令的自动拦截。

## [v0.1.0] - 2026-07-15

- 首次公开预发布，提供 Legal OS 通用法律工作流、质量控制规则和公私边界说明。

[v0.1.1]: https://github.com/384363367-dot/legal-os/compare/v0.1.0...v0.1.1
[v0.2.0]: https://github.com/384363367-dot/legal-os/compare/v0.1.1...HEAD
[v0.1.0]: https://github.com/384363367-dot/legal-os/releases/tag/v0.1.0
