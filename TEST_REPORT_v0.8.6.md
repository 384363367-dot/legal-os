# Legal OS v0.8.6 验证记录

执行日期：2026-10-20，Python 3.9.6。对象为指定临时 checkout 中的公开侧实现。本记录只说明本地验证结果，不证明 GitHub Tag、Release 或外部发布已完成。

## 本地验证

| 命令 | 实际结果 |
| --- | --- |
| `python3 scripts/validate_public_surface.py` | PASS |
| `python3 scripts/validate_manifest.py` | PASS；核对公开 Release ID/版本、15 个 Skills、139 个 payload 文件和树哈希 `94470aba83c4055669584359e3f928f8b3a3ef383f6f4eab4f7fa77030dfe1eb` |
| `python3 scripts/validate_repo.py` | PASS |
| `python3 scripts/validate_routing_scenarios.py` | PASS，16 个合成路由场景 |
| 三个 `check_first_party_boundary.py`（`cn-case-hub`、`cn-law-hub`、`cn-legal-research`） | PASS |
| `./install.sh --dry-run --target /tmp/legalos-v086-public-dry-run-final` | PASS，15 个 Skills；未执行实际安装 |
| `python3 -m unittest discover -s tests -q` | PASS，126 项 |
| `python3 -m unittest discover -s tests -p 'test_installer.py' -q` | PASS，7 项，包括危险目标拒绝、临时路径规范化和注入失败后的整套回滚 |
| `python3 -m unittest discover -s tests -p 'test_release_pair.py' -q` | PASS，5 项，包括私有字段不回显检查 |
| `python3 -m unittest discover -s skills/legal-os-contract/tests -q` | PASS，50 项 |
| `python3 -m unittest discover -s skills/legal-quality-gate/tests -q` | PASS，75 项 |
| `python3 -m unittest discover -s skills/legal-os-unified-intake/tests -q` | PASS，5 项 |
| `python3 -m pip check` | PASS，无破损依赖 |
| `bash -n install.sh` 与 `git diff --check` | PASS |
| `legal-os-banner.png` 结构和解码像素复核 | PASS；移除 23,597 字节 `caBX` 元数据，所有保留 chunks 的 CRC 有效，4,720,614 个 RGB 字节逐字节一致 |
| 项目 `scan_public_candidate.sh` | REVIEW_REQUIRED；扫描命中项经人工分类为哈希数字串、通用安装/边界防护文字，以及压缩 IDAT 字节中的邮箱样式随机串；须由项目发布闸门登记人工处置后再决定是否放行 |
| 项目 `license_boundary_gate.py` | PASS，扫描 218 个文件，无依赖边界命中 |

脱敏扫描完整命中项：`PACKAGE_MANIFEST.json`、`SHA256SUMS.txt`（SHA-256 字符串中偶然出现的手机号样式数字）；`UPGRADE_REPORT_v0.7.0.md`（通用 Codex 默认安装目录说明）；`install.sh`（拒绝系统保护目录的安全清单）；`skills/cn-legal-research/scripts/check_first_party_boundary.py`、`skills/cn-law-hub/scripts/check_first_party_boundary.py` 和 `skills/legal-os-unified-intake/tests/test_external_expression_boundary.py`（合成的路径边界检查字符串）；`legal-os-banner.png`（压缩 IDAT 中的邮箱样式随机串，文件偏移 2,175,188，拼接 IDAT 负载偏移 2,174,751）。PNG 清理只移除了 `caBX` 块；原始与候选 PNG 的拼接 IDAT SHA-256 均为 `66eab2e5401b5d3f3a9e85ceccc6cfe55526e17078dd2edc12737f3697acb4b0`，所有 PNG CRC 有效，解码后的 RGB 像素逐字节相同。上述命中均为通用内容或扫描器对压缩像素数据的误报；扫描器状态仍为 `REVIEW_REQUIRED`，本文件不替代项目闸门的人工处置。

公开 profile 共 15 个 Skills、139 个 payload 文件；独立的 Git 索引计算也得到同一树哈希。回归测试确认 `__pycache__`、`.pyc`、`.venv`、`.git` 文件不会改变 profile payload。公开安装器测试确认根路径别名在 dry-run 和实际写入前均被拒绝、真实临时目录别名可规范化安装，并通过中途替换失败的故障注入验证套件回滚与 staging 清理。pair-validator 测试使用合成私有 manifest，确认只核对共享 Release ID/版本和 profile id，且不会输出哨兵私有路径、哈希或内容。

## 范围与限制

本次是公开侧本地验证，没有读取或输出真实私有 manifest，也没有执行本地私有安装、推送、打 Tag、创建 GitHub Release 或在线来源核验。真实公私 Release ID/版本对账及私有运行时验收由主控在私有侧完成。
