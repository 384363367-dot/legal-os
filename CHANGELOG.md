# Changelog

本文件记录 Legal OS 公开预发布版本的主要变化。

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
[v0.1.0]: https://github.com/384363367-dot/legal-os/releases/tag/v0.1.0
