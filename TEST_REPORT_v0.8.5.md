# Legal OS v0.8.5 验证记录

执行日期：2026-10-20，Python 3.9.6。对象为本仓库公开预发布包中的独立标准库实现；测试通过不等于保证未来远端结构或法律适用结果。

## 离线验证

| 命令 | 实际结果 |
| --- | --- |
| `python3 scripts/validate_public_surface.py` | PASS |
| `python3 scripts/validate_manifest.py` | PASS |
| `python3 scripts/validate_repo.py` | PASS |
| `python3 scripts/validate_routing_scenarios.py` | PASS，16 个合成路由场景 |
| `python3 skills/cn-legal-research/scripts/check_first_party_boundary.py` | PASS，标准库实现且只访问登记的 HTTPS 来源 |
| `./install.sh --dry-run --target <caller-owned-directory>` | PASS，15 个 Skills；未执行实际安装 |
| `python3 -m unittest discover -s tests -v` | PASS，111 项 |
| `python3 -m unittest discover -s skills/legal-os-contract/tests -v` | PASS，50 项 |
| `python3 -m unittest discover -s skills/legal-quality-gate/tests -v` | PASS，75 项 |
| `python3 -m unittest discover -s skills/legal-os-unified-intake/tests -v` | PASS，5 项 |
| `python3 -m pip check` | PASS，无破损依赖 |
| `git diff --check` | PASS |

新增离线回归覆盖司法部搜索详情链接中的中文参数编码，以及详情页法规标题、公布日、施行日的提取。测试确认详情页没有标注效力状态时保持“未标注”，不从正文推断现行状态。

## 司法部官方来源在线验证

使用 `moj_law_crawler.py` 以标题搜索“保障农民工工资支付条例”，只请求一页并关闭缓存。官方搜索页返回一条记录，状态为“现行有效”，公布日为 2019-12-30，施行日为 2020-05-01。搜索生成的详情 URL 全部为 ASCII 字符且可直接传给详情入口；详情页返回准确法规标题、国务院令第724号、2019年12月30日公布日和2020年5月1日施行日。详情页本身未标注效力状态，因此输出仍为“未标注”，由搜索页的当前行政法规集合记录提供状态证据。

验证回到[司法部法规详情页](https://xzfg.moj.gov.cn/front/law/detail?LawID=449)及[司法部官方标题搜索页](https://xzfg.moj.gov.cn/SearchTitleFront?QueryAll=%E4%BF%9D%E9%9A%9C%E5%86%9C%E6%B0%91%E5%B7%A5%E5%B7%A5%E8%B5%84%E6%94%AF%E4%BB%98%E6%9D%A1%E4%BE%8BZVING1)。该次在线结果只证明验证时页面可访问、字段可提取，不证明其他法规、其他页面结构或未来页面响应。

## 公开包与边界

包校验以 `PACKAGE_MANIFEST.json` 与 `SHA256SUMS.txt` 为准。公开更新仅改变 `cn-legal-research` 的司法部适配、对应工作说明、回归测试和本版本发布文档；不增加 Skill、路由、模板、第三方依赖、法规数据、缓存、凭据或签名参数。
