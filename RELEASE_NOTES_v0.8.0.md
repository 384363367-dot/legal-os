# Legal OS v0.8.0

状态：公开适配版（公开预发布，非稳定版）。

## 本次范围

v0.8.0 将现行法研究的公开接口适配为第一方、可审计的官方来源查询和 authority record 核验层：

- 为十个主要官方来源提供机器可读登记和逐源查询计划；
- 校验 authority record 的必备元数据、来源 HTTPS、法源类型绑定、状态变更说明、日期字段和重复链接；
- 保持 T-05 现行法/案例双 Skill 分流，不改变 T-01 至 T-12 的路由编号；
- 保持公开包不包含第三方爬虫、MCP、商业数据库 SDK、缓存数据和私有运行时；
- 在 README 最底部加入对 `cn-law-hub` 的明确致谢，并说明独立实现和无隶属/背书关系。

## 不在本版本范围内

- 不提供全国法规或裁判文书镜像；
- 不自动绕过登录、验证码、robots 或其他访问控制；
- 不把外部官方网站或数据库内容重新分发为 Legal OS 自有数据；
- 不修改私有 LegalOS 正式版本或私有 runtime。

## 使用入口

- [现行法公开适配说明](docs/current-law-public-adaptation-v0.8.md)
- [能力矩阵](docs/capability-matrix.md)
- [公开边界](OPEN_SOURCE_BOUNDARY.md)
- [测试报告](TEST_REPORT_v0.8.0.md)
