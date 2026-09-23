# Legal OS v0.8.1 验证记录

状态：2026-09-23 本地公开预发布候选验证通过；不代表 GitHub Tag 或 Release 已发布。

## 环境与范围

- 基线：`main` 提交 `97c3a754610fabc45a74d47322bd635e4454ffd6`。
- 本次为现有规则和静态规则回归测试维护；未增业务 Skill、路由、模板、真实事项材料或第三方依赖。
- 规则测试验证 canonical 文本中的行为约束；未运行真实模型输出评测，不将静态通过视为任何法律结论的正确性证明。

## CI 等价门禁

| 检查 | 结果 |
| --- | --- |
| `python3 -m pip check` | PASS，无损坏依赖 |
| `python3 scripts/validate_public_surface.py` | PASS |
| `python3 scripts/validate_repo.py` | PASS |
| `python3 scripts/validate_routing_scenarios.py` | PASS，16 个合成场景 |
| 三个研究 Skill 的 `check_first_party_boundary.py` | PASS |
| `./install.sh --dry-run --target /tmp/legal-os-v081-install-dry-run` | PASS，15 个 Skill；只列出目标，不安装（macOS `/tmp` 对应实际临时目录） |
| `python3 -m unittest discover -s tests -v` | PASS，83 项，含 7 项 v0.8.1 规则回归和包清单/校验和验证 |
| `python3 -m unittest discover -s skills/legal-os-contract/tests -v` | PASS，27 项 |
| `python3 -m unittest discover -s skills/legal-quality-gate/tests -v` | PASS，9 项 |
| `python3 -m unittest discover -s skills/legal-os-unified-intake/tests -v` | PASS，5 项 |
| `git diff --check` | PASS |

新增测试覆盖重复风险唯一归位与简短引用、事项重要性与 R0–R3 区分、合同只审核路径、正式成品位置与正式版本例外、领导风险方案结构、中文图中文字生产边界、证据证明层级，以及当前包清单和校验和一致性。

## 范围限制

- 上述新规则测试为静态 policy regressions；实际法律文稿仍须按材料、证据、法源和人工质量门逐件核验。
- 未在本次离线门内访问法律站点、执行真实合同审核、签署、提交或对外发送。
