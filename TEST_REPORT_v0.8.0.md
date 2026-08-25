# Legal OS v0.8.0 公开适配测试报告

## 测试环境

- Python：LegalOS canonical runtime Python 3.12.12；测试只依赖 Python 标准库。
- 网络：本报告中的自动化测试不访问外部网站，不包含任何抓取或缓存步骤。
- 范围：公开源文件、manifest、Skill 边界、查询计划、authority record、路由、安装 dry-run 和全仓测试。

## 固定门禁

```bash
python3 scripts/validate_public_surface.py
python3 scripts/validate_repo.py
python3 scripts/validate_routing_scenarios.py
python3 -m unittest discover -s tests -v
./install.sh --dry-run
```

实测结果（2026-08-25）：

- `validate_public_surface.py`：PASS；
- `validate_repo.py`：PASS；
- `validate_routing_scenarios.py`：PASS（16 个合成场景）；
- 两个 first-party boundary 脚本：PASS；
- `python -m unittest discover -s tests -v`：`60 tests`，全部 PASS；
- `./install.sh --dry-run`：14 个 Skill，全部列出，退出码 `0`。

所有命令退出码均为 `0`；提交前的差异检查通过，变更仅限本版本列明的公开文件；未发现私有路径、私有 Skill 名称、来源爬虫或第三方运行时硬依赖。

## 研究适配定向覆盖

- 十个登记官方来源均出现在查询计划中；
- 缺失 `document_number`、`promulgated_date`、`effective_date` 的记录被拒绝；
- 非官方主机、官方主机与法源类型错配被拒绝；
- authority record 的重复 supersession ID 被拒绝；
- 公开边界脚本通过，未发现来源爬虫、私有路径或硬依赖；
- `T-05 current-law-research` 仍指向 `cn-law-hub`，案例研究仍指向 `cn-case-hub`。

## 解释边界

通过本报告不表示 Legal OS 已经拥有或完整覆盖所有法规、司法解释或裁判文书。正式法律命题仍必须打开实际官方原文，记录版本、效力、条号、访问时间和时间适用；本项目不替代律师判断。
