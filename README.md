<p align="center">
  <img src="./legal-os-banner.png" alt="Legal OS" width="100%">
</p>

<h1 align="center">Legal OS</h1>

<p align="center">
  <strong>面向中国法律工作的可安装、可组合、可审计 AI 工作流</strong>
</p>

<p align="center">
  把材料受理、合同、诉讼、现行法与类案研究、函件、数据、Office 交付和质量控制，组织成一条可复用的工作路径。
</p>

<p align="center">
  <img src="https://img.shields.io/badge/release-v0.8.0-blue" alt="v0.8.0 public prerelease">
  <img src="https://img.shields.io/badge/Skills-15-2563eb" alt="15 Skills">
  <img src="https://img.shields.io/badge/routes-12-0f766e" alt="12 routes">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache--2.0-blue" alt="Apache 2.0 License"></a>
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> ·
  <a href="#核心能力">核心能力</a> ·
  <a href="docs/architecture.md">查看架构</a> ·
  <a href="docs/capability-matrix.md">能力矩阵</a> ·
  <a href="docs/current-law-public-adaptation-v0.8.md">v0.8.0 研究适配</a> ·
  <a href="CHANGELOG.md">版本记录</a>
</p>

---

## 当前版本

**v0.8.0 公开适配版（公开候选）**。当前公开包包含 **15 个 Skills、12 条路由和 24 个标准 Office 模板**。版本边界、安装方式和已知限制以本仓库文件为准。

## Legal OS 是什么

Legal OS 不是一组零散提示词，也不是替代律师判断的无人值守系统。它把正式法律工作中容易断裂的环节接起来：

- 从用户请求和材料开始，先判断事项类型、代表立场、风险和缺口；
- 选择一个主工作流，只加载完成当前任务所需的辅助能力；
- 将事实、证据、金额、日期、现行法律和类案结果保持可追溯；
- 以模板、源文件质量门和人工授权状态约束正式交付。

核心目标是让 AI 产出更容易复核、修改、交接和留痕，而不是把法律判断交给自动化流程。

## 核心能力

| 工作结果 | Legal OS 提供的能力 |
| --- | --- |
| 从一条请求开始 | 统一受理、风险分流、材料缺口识别和主工作流选择 |
| 把法律问题查清楚 | 现行法效力/版本核验、官方类案研究、争点与裁判变量整理 |
| 把正式文书做出来 | 合同审核、诉讼/仲裁、律师函与正式函件、业务沟通、报告和演示结构 |
| 把数字与文件交付稳住 | 金额/付款/日期核验、模板解析、Office 源文件检查、版本与归档 |
| 把风险留在可控范围 | 证据回流、法律质量门、事实与策略分层、外部动作单独授权 |

### v0.8.0 重点升级

- **研究更可核验**：`cn-legal-research` 作为 T-05 现行法检索默认执行器，覆盖官方来源搜索、详情、预览、条文、下载、跨法规搜索和十个主要来源适配；`cn-case-hub` 负责官方类案研究；
- **公开适配更安全**：`cn-legal-research` 使用独立的 Python 标准库适配器，运行时才访问登记的官方 HTTPS 来源，不捆绑法规数据、缓存、凭据或第三方 SDK；`cn-law-hub` 仅保留为兼容/过渡的元数据、查询计划和 authority record 能力，不再是默认入口；
- **研究能回到案件**：把裁判变量连接到本案事实、证据缺口、补证动作和诉讼策略，而不把检索样本包装成胜诉率；
- **交付更可控**：统一入口、模板运行时、Office 源文件质量门和法律质量门共同约束正式成果；
- **改进可持续**：`legal-os-learning-maintenance` 把可复用流程改进沉淀为规则，同时将具体事项事实留在事项范围内。

研究模块也可以作为合同或诉讼工作流的辅助能力使用。详细设计见 [`docs/case-and-law-research-v0.7.md`](docs/case-and-law-research-v0.7.md)。

## 工作方式

```mermaid
flowchart LR
    A["用户请求与材料"] --> B["统一受理与风险分流"]
    B --> C["一个主工作流"]
    C --> D["事实 / 数据 / 法源核验"]
    D --> E["现行法 / 类案研究"]
    E --> F["证据与策略回流"]
    F --> G["模板解析与成果制作"]
    G --> H["质量门与人工复核"]
    H --> I["授权后交付"]
```

系统入口为 `legal-os-unified-intake`。它识别事项类型、代表角色、风险、材料缺口、输出对象和授权边界，选择一个主工作流，并只组合必要辅助模块。

## 15 个可安装 Skills

| Skill | 角色 | 主要能力 |
|---|---|---|
| [`legal-os-unified-intake`](skills/legal-os-unified-intake/) | Router | 统一受理、风险/缺口识别、一个 primary route + 必要 auxiliaries |
| [`legal-os-contract`](skills/legal-os-contract/) | Primary | 合同审核、最小必要修改、tracked-changes DOCX 与质量门 |
| [`legal-os-litigation`](skills/legal-os-litigation/) | Primary | 诉讼/仲裁分析、证据映射、研究回流、诉辩文书与证据目录 |
| [`cn-case-hub`](skills/cn-case-hub/) | Primary/Auxiliary | 官方案例核验、双轴类案矩阵、程序链、裁判分叉变量 |
| [`cn-legal-research`](skills/cn-legal-research/) | T-05 Default/Auxiliary | 官方现行法搜索、详情、预览、条文、下载、跨法规搜索和来源适配 |
| [`cn-law-hub`](skills/cn-law-hub/) | Compatibility | 兼容/过渡的官方来源元数据、查询计划和 authority record 核验；不是默认入口 |
| [`legal-os-correspondence`](skills/legal-os-correspondence/) | Primary | 律师函、催款/履约通知、回复函、情况说明 |
| [`legal-os-business-communication`](skills/legal-os-business-communication/) | Primary | 微信、邮件、会议/电话口径与承诺风险控制 |
| [`legal-os-data-verification`](skills/legal-os-data-verification/) | Primary/Auxiliary | 金额、付款、发票、日期节点、数据冲突 |
| [`legal-os-file-delivery`](skills/legal-os-file-delivery/) | Primary/Auxiliary | 文件转换、打包、版本、归档、交付检查 |
| [`legal-os-reporting-presentation`](skills/legal-os-reporting-presentation/) | Primary | 周报/月报、领导汇报、客户报告、PPT 结构 |
| [`legal-os-matter-memory`](skills/legal-os-matter-memory/) | Primary/Auxiliary | 事项记忆、动态事实状态、可复用与事项信息分层 |
| [`legal-os-template-runtime`](skills/legal-os-template-runtime/) | Cross-cutting | 24 个模板解析、版本绑定和缺模板阻断 |
| [`legal-quality-gate`](skills/legal-quality-gate/) | Cross-cutting | 正式法律成果最终复核和交付锁定 |
| [`legal-os-learning-maintenance`](skills/legal-os-learning-maintenance/) | Governance | 受控复盘、规则增量和长期维护 |

更完整的路由边界见 [`docs/capability-matrix.md`](docs/capability-matrix.md)。

## 快速开始

### 安装 Skills

```bash
./install.sh --dry-run
./install.sh
```

默认安装到 `~/.codex/skills`。安装脚本不会静默覆盖已有 Skill。

```bash
./install.sh --replace
```

安装器会先备份原有 Skill，不会静默覆盖。

也可以只复制 `skills/` 下所需的完整目录。不要只复制 `SKILL.md`，因为 references、scripts、templates 和 `agents/openai.yaml` 都是 Skill 的组成部分。

## 使用示例

```text
使用 $legal-os-unified-intake 读取材料，判断事项类型、风险、缺口和下一步工作流。
```

```text
使用 $cn-case-hub 针对这个争点查正反类案，按 A/B/C/D × +/±/0/- 分类，并提炼可能改变裁判结果的事实变量。
```

```text
使用 $cn-legal-research 核验这条规定当前是否有效、历史版本、适用时间以及准确条文；输出必须回到实际访问的官方原文。
```

```text
使用 $cn-law-hub 生成兼容查询计划或核验 authority record；它不替代 cn-legal-research 的默认检索入口。
```

```text
使用 $legal-os-litigation 把已核验案例和法源结果映射到本案证据缺口、补证动作和诉讼策略。
```

## 法律与研究边界

- 本项目不构成法律意见，不替代律师、法务或其他专业人员判断；
- 事实、证据、金额、日期、案件状态和现行法律必须根据具体事项重新核验；
- 搜索摘要、模型记忆和二手材料只能作为线索；
- 外部官方站点的登录、验证码、robots 或权限限制不得绕过；
- “第一方 Skill”是指工作流/脚本由本仓库维护，不意味着 Legal OS 自行拥有一套完整法规/裁判数据库；
- 起草不等于发送，完成不等于签署，内部审查不等于提交；外部动作需要独立授权。

## 开发者验证

贡献或修改公开包后，可运行：

```bash
python3 scripts/validate_public_surface.py
python3 scripts/validate_repo.py
python3 scripts/validate_routing_scenarios.py
python3 -m unittest discover -s tests -v
./install.sh --dry-run
```

具体命令、环境和结果见 [`TEST_REPORT_v0.8.0.md`](TEST_REPORT_v0.8.0.md)。首页与版本文案的固定更新规则见 [`docs/public-homepage-and-release-rules.md`](docs/public-homepage-and-release-rules.md)。

## 文档导航

- [系统架构](docs/architecture.md)
- [能力矩阵](docs/capability-matrix.md)
- [统一入口与路由](docs/unified-intake-routing.md)
- [v0.8.0 现行法公开适配](docs/current-law-public-adaptation-v0.8.md)
- [公开候选清单](PUBLIC_CANDIDATE_MANIFEST.json)
- [v0.7.0 案例/现行法研究架构](docs/case-and-law-research-v0.7.md)
- [诉讼工作空间](docs/litigation-workspace.md)
- [证据工作空间](docs/evidence-workspace.md)
- [模板运行时](docs/template-runtime.md)
- [Office 质量门](docs/native-office-quality-gate.md)
- [公开首页与版本更新规则](docs/public-homepage-and-release-rules.md)
- [版本记录](CHANGELOG.md)
- [贡献指南](CONTRIBUTING.md)

## 许可证

版本变化见 [`CHANGELOG.md`](CHANGELOG.md)，单个版本的升级说明和验证记录见仓库根目录的对应文档。除文件或子目录另有说明外，本仓库采用 [Apache License 2.0](LICENSE) 许可。

## 致谢

感谢 [`cn-law-hub`](https://github.com/ZongziForu/cn-law-hub) 公开项目及其维护者分享中国官方法源组织和法律检索的实践经验。Legal OS 的公开适配保持独立实现，不复制该项目的源代码、爬虫或运行时，并不表示双方存在隶属、背书或官方合作关系。
