# Legal OS

Legal OS is an open, modular workflow framework for reliable legal work with AI agents.

## 中文介绍

Legal OS 是一个面向中国法务工作场景、以 AI Agent 协作为入口的开源法律工作流框架。它不是单纯的提示词集合，也不是替代律师判断的自动化系统，而是把法律事项从受理、分流、材料整理、事实与法律核验、起草审查，到质量控制、版本管理和成果交付，组织成一套可复用、可追溯、可持续迭代的工作方法。

它的核心亮点包括：

- **统一受理与风险分流**：围绕事项类型、风险等级、授权状态、材料完整性、目标受众和交付要求，选择合适的工作路径，并在权限不清、事实冲突、材料不足或需要外部行动时暂停复核。
- **最小上下文加载**：按任务只加载必要的规则、材料和工作模块，减少无关信息混入，降低隐私暴露、事实错配和不必要推理的风险。
- **模块化法律工作空间**：覆盖合同审查与修订、诉讼与仲裁、证据整理、正式函件、商业沟通、金额与数据核验、文件交付、汇报展示、事项记忆和统一受理分流等场景。
- **来源锁定与可核验工作流**：要求事实、金额、日期、法律命题和输出结论尽可能回到明确来源；无法核验、存在冲突或当前法律状态不明时，保留待核验状态，不用旧记忆或推测填补空白。
- **事实—证据—法律—请求/抗辩对齐**：把材料事实、证据支持、法律依据、程序位置和最终请求放在同一质量检查链条中，便于发现缺口、矛盾和越权结论。
- **可审查的合同与文档交付**：支持最小颗粒度合同修订规则、真实 DOCX 修订痕迹、清洁版与修订版区分，以及文件清单、质量闸门和交付验证。
- **质量闸门与版本治理**：通过测试、依赖检查、隐私和秘密扫描、来源核验、版本记录、Frozen/Candidate 边界和发布前检查，避免把未经审查的草稿直接当成正式成果。
- **公私仓分离**：公开仓只保留通用 Skills、可复用脚本、规则结构、质量闸门、合成或不可逆匿名化示例；客户资料、真实案件事实、内部策略、个人偏好、私有路径、凭据和保密模板留在私有环境。
- **面向 AI 协作而非盲目自动化**：把 AI 放在受控的受理、整理、核验、起草和复核流程中，保留人工判断、授权、签发、发送、提交和签署等关键控制点。

Legal OS 适合作为律师、法务团队和法律 AI 工具开发者搭建可复用法律工作流的基础框架。仓库中的内容是通用流程、规则结构、脚本和质量控制参考，不构成法律意见，也不替代具体事项中的专业判断、现行法核验、证据审查和授权审批。

## English overview

Legal OS is an open, modular workflow framework for reliable legal work with AI agents.

It is designed around:

- task routing and minimum-context loading;
- reusable Skills, rule packs and quality gates;
- source-locked factual and legal verification;
- contract, litigation, correspondence, data, file-delivery, reporting and matter-memory workspaces;
- validation and release checks for reviewable legal work products.

## Current public scope

This pre-release repository contains generic, reusable workflow material, including:

- public Legal OS Skills and their workflow references;
- workspace and routing documentation;
- contract redline quality-gate and metrics scripts;
- synthetic-safe test guidance;
- the public/private separation policy.

The public repository does not contain client files, matter facts, private prompts, user-specific preferences, confidential templates, credentials or signed-in service details.

## Quick start

Start with [`OPEN_SOURCE_BOUNDARY.md`](OPEN_SOURCE_BOUNDARY.md), then read [`docs/architecture.md`](docs/architecture.md) and the documentation for the Skill or workspace you want to use. Each module is intended to be reviewed and adapted to its own jurisdiction, evidence sources, permissions and quality requirements.

## Legal and safety notice

This repository provides workflow structures, prompts, scripts and validation guidance. It is not legal advice, does not replace professional judgment, and does not establish that any legal proposition is current or applicable to a particular matter. Verify current law, authority, facts, permissions and output quality before relying on or releasing work produced with these materials.

## Status

Pre-release (`v0.1.0` will be the first public release). Interfaces, module boundaries and repository layout may change before the first stable release.

## License

Unless a file or subdirectory states otherwise, this repository is licensed under the Apache License, Version 2.0. See [`LICENSE`](LICENSE). Third-party materials, if added later, remain subject to their own license and attribution requirements.
