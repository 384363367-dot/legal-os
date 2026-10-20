# Legal OS v0.8.6

公开预发布版，非稳定版。Release ID 为 `legalos-v0.8.6`，版本为 `0.8.6`。

本版统一公开包的版本身份，并改进 Skill 套件安装过程。法律工作流内容、Skill 数量、路由、模板和成熟度标签不变；`cn-law-hub` 继续作为公开兼容 Skill。

## 同步版本身份与 profile 清单

公开 `legalos.manifest.json` 与 `PACKAGE_MANIFEST.json` 使用相同的 Release ID/版本，并分别记录公开 profile `public-generic` 的 Skills 数量、Skill payload 文件数和 payload 树哈希。payload 树哈希只覆盖 `skills/` 下的文件，按相对路径排序，以 `path + NUL + file SHA-256 + LF` 计算；本机生成的 `__pycache__`、`.pyc`、`.venv` 与 `.git` 不计入 profile payload。`PACKAGE_MANIFEST.json` 的 `files` 仍完整记录公开仓库文件的路径、大小、mode 和 SHA-256。

本地 pair-validator 可用私有 manifest 核对共享 Release ID/版本与 profile id。它不读取、输出或保存私有 payload inventory、文件路径、哈希或内容。

公开首页 banner 的 `caBX` C2PA/JUMBF 元数据块已移除，保留其余 PNG chunks。结构与 CRC 检查通过，清理前后的解码 RGB 像素完全一致。

## 安装事务与回滚

安装器先规范化目标的绝对物理路径；根目录、系统保护目录、用户主目录和无效父路径会在 dry-run 与写入前拒绝。目标的父目录含符号链接或缺失组件时，路径会按实际物理目录安全规范化。安装器随后在目标目录同级临时目录完整暂存并核对 15 个 Skills，再执行替换。任一替换步骤失败，会删除本轮已安装项并恢复本轮已移动的旧 Skill；成功替换时旧 Skill 留在目标目录 `.backup/<transaction>/` 作为回滚材料。无论成功还是失败都会清理临时 staging。

`--setup-runtime` 仍是可选的独立依赖安装步骤，在 Skill payload 事务开始前运行；Skill 套件事务不覆盖 Python 环境的依赖变更。

## 安装

```bash
./install.sh --dry-run --target <skills-directory>
./install.sh --replace --target <skills-directory>
```

如果目标目录已有同名 Skill，必须显式使用 `--replace`。安装器不会修改目标目录之外的其他 Skill。
