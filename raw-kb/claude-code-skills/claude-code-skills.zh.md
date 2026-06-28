# 构建 Claude Code 的经验教训：我们如何使用 Skills

在 Anthropic 内部构建和扩展数百个 skills 后学到的经验。

- **分类：** Claude Code
- **产品：** Claude Code
- **日期：** 2026年6月3日
- **阅读时间：** 5 分钟

---

Skills 已成为 Claude Code 中最常用的扩展点。它们灵活、易于创建、易于分发。

但这种灵活性也让人难以判断什么做法最好。什么样的 skills 值得创建？如何结构化的 skill？何时与他人分享？

我们在 Anthropic 内部广泛使用 Claude Code 的 skills，目前有数百个在活跃使用。以下是我们使用 skills 加速开发方面学到的经验教训。

## 什么是 Skills？

Skills 是指令、脚本和资源的文件夹，代理可以发现并使用它们来更准确、更高效地完成任务。本文假设读者熟悉 skills 的基础知识；如果您是新手，请先在 Skilljar 上查看我们的代理 skills 入门课程。

一个常见的误解是 skills"只是 markdown 文件"。实际上，它们是可以包含脚本、资产、数据等的文件夹，代理可以发现、探索和操作这些内容。

在 Claude Code 中，skills 还具有多种配置选项，包括注册动态钩子（hooks）。

我们发现，Claude Code 中一些最有效的 skills 充分利用了这些配置选项和文件夹结构。

## Skill 的类型

在对 Anthropic 内部所有 skills 进行分类后，我们发现它们可分为九类。最好的 skills 清晰归入一类；那些试图做太多事情的 skills 会跨越多个类别，让代理困惑。

![Anthropic 内部 skills 的九大分类](images/skills-categories-chart.png)

### 1. 库和 API 参考

解释如何正确使用库、CLI 或 SDK 的 skills。可以是内部库或 Claude Code 有时难以处理的常见库。通常包含参考代码片段文件夹和 Claude 应避免的陷阱列表。

示例：
- **billing-lib** — 内部计费库：边缘情况、陷阱等。
- **internal-platform-cli** — 内部 CLI 包装器的每个子命令及其使用时机。
- **sandbox-proxy** — 配置出口网关：哪些主机可达、如何调试"连接拒绝"错误、如何添加白名单条目。

### 2. 产品验证

描述如何测试或验证代码是否正常工作的 skills。通常与 playwright、tmux 或其他外部工具配合使用。

验证 skills 对 Claude 输出质量的影响最大。让工程师花一周时间完善验证 skills 是值得的。

考虑让 Claude 录制输出视频以便看到它测试了什么，或在每一步强制状态断言。这些通常通过在 skill 中包含各种脚本来完成。

示例：
- **signup-flow-driver** — 在无头浏览器中运行注册→邮箱验证→入职流程，每步有状态断言钩子
- **checkout-verifier** — 使用 Stripe 测试卡驱动结账 UI，验证发票正确到达
- **tmux-cli-driver** — 交互式 CLI 测试，需要 TTY 环境

### 3. 数据获取和分析

连接到数据和监控堆栈的 skills。可能包括使用凭据获取数据的库、特定仪表板 ID 等，以及常见工作流程说明。

示例：
- **funnel-query** — "哪些事件用于查看注册→激活→付费"及包含标准 user_id 的表
- **cohort-compare** — 比较两个队列的留存率或转化率，标记统计显著差异
- **grafana** — 数据源 UID、集群名称、问题→仪表板查找表
- **datadog** — 字段参考、服务列表、指标前缀约定

### 4. 业务流程和团队自动化

将重复工作流自动化为一条命令的 skills。通常指令简单，但可能对其他 skills 或 MCP 有复杂依赖。将先前结果保存在日志文件中可帮助模型保持一致性。

示例：
- **standup-post** — 聚合工单、GitHub 活动和 Slack → 格式化站会报告（仅增量）
- **create-<ticket-system>-ticket** — 强制 schema（有效枚举、必填字段）及创建后工作流
- **weekly-recap** — 合并的 PR + 关闭的工单 + 部署 → 格式化周报

### 5. 代码脚手架和模板

为特定功能生成框架样板的 skills。当脚手架有自然语言要求时特别有用。

示例：
- **new-<framework>-workflow** — 用注解搭建新服务/工作流/处理器
- **new-migration** — 迁移文件模板及常见陷阱
- **create-app** — 新内部应用，预配认证、日志和部署配置

### 6. 代码质量和审查

在组织内强制代码质量并帮助审查代码的 skills。可包含确定性脚本或工具以实现最大健壮性。

示例：
- **adversarial-review** — 生成全新视角的子代理进行批评，迭代改进
- **code-style** — 强制代码风格（特别是 Claude 默认做不好的部分）
- **testing-practices** — 如何编写测试及测试内容的说明

### 7. CI/CD 和部署

帮助在代码库内获取、推送和部署代码的 skills。可能引用其他 skills 来收集数据。

示例：
- **babysit-pr** — 监控 PR→重试不稳定 CI→解决合并冲突→启用自动合并
- **deploy-<service>** — 构建→冒烟测试→逐步流量发布（错误率比较）→回归自动回滚
- **cherry-pick-prod** — 隔离工作树→cherry-pick→冲突解决→带模板的 PR

### 8. 运行手册（Runbooks）

接受症状（如 Slack 线程、警报、错误签名），通过多工具调查并生成结构化报告的 skills。

示例：
- **<service>-debugging** — 将症状映射到工具和查询模式
- **oncall-runner** — 获取警报→检查常见问题→格式化发现
- **log-correlator** — 给定请求 ID，从所有相关系统提取匹配日志

### 9. 基础设施运维

执行日常维护和操作程序的 skills，其中一些涉及破坏性操作需有防护措施。

示例：
- **<resource>-orphans** — 查找孤立资源→发布到 Slack→浸泡期→用户确认→级联清理
- **dependency-management** — 依赖项批准工作流
- **cost-investigation** — "为什么存储/出站账单飙升"排查

## 创建 Skills 的技巧

### 不要陈述显而易见的事

Claude 已经知道如何编码并可以读取代码库。重复 Claude 默认会做的事情只会增加上下文噪音。专注于推动 Claude 跳出正常思维方式的信息。

前端设计 skill 是个好例子：工程师通过迭代改进 Claude 的设计品味，避免 Inter 字体和紫色渐变等经典模式。

### 构建陷阱（Gotchas）部分

任何 skill 中信号价值最高的内容是 Gotchas 部分。应从 Claude 使用 skill 时遇到的常见失败点构建，并随时间持续更新。

示例：
- "订阅表是只追加的。你要找的是版本最高的行，不是最新创建的行。"
- "此字段在 API 网关中叫 @request_id，在计费服务中叫 trace_id。它们是同一个值。"
- "Staging 即使 Stripe webhook 没处理也返回 200。检查 payment_events 获取真实状态。"

### 使用文件系统和渐进式披露

Skill 是一个文件夹，而不仅仅是 markdown 文件。应将整个文件系统视为上下文工程和渐进式披露的形式。告诉 Claude skill 中有哪些文件，它会在适当时读取。

最简单的形式是指向其他 markdown 文件。例如，将详细函数签名和用法示例拆分到 `references/api.md`。

### 避免过度约束 Claude

Claude 通常会严格执行指令。由于 skills 高度可重用，需注意不要过于具体。给 Claude 必要信息，但保留灵活性。

### 仔细考虑设置

某些 skills 需要用户提供上下文。好的模式是将设置信息存储在 skill 目录的 `config.json` 中。配置未设置时，代理可询问用户。

如需呈现结构化选择题，可使用 AskUserQuestion 工具。

### 为模型（而非人类）编写描述

Claude Code 启动时会构建每个可用 skill 及其描述的列表。Claude 扫描此列表决定"是否有适合此请求的 skill？"因此描述字段不是摘要，而是触发条件。在描述中包含触发词（如"babysit"）很有帮助。

### 帮助 Claude 记忆

Skills 可通过存储数据实现记忆。数据可简单到追加文本日志文件，或复杂到 SQLite 数据库。

例如，standup-post skill 可保留 `standups.log` 记录每次帖子。下次运行时，Claude 读取自身历史，判断自昨天起的变化。

使用环境变量 `${CLAUDE_PLUGIN_DATA}` 获取稳定数据存储目录。

### 存储脚本并生成代码

给 Claude 脚本和库，让它专注于组合决策，而非重新构建样板代码。

### 使用按需钩子

Skills 可包含仅在调用 skill 时激活的钩子，仅在会话期间有效。

示例：
- **/careful** — 阻止 `rm -rf`、`DROP TABLE`、`force-push`、`kubectl delete`
- **/freeze** — 限制编辑/写入仅在特定目录内

## 分发 Skills

两种方式共享 skills：
1. 检入仓库（`./.claude/skills`）
2. 制作插件并拥有 Claude Code 插件市场

小团队检入仓库即可。但每个检入的 skill 都会增加模型上下文。规模扩大后，内部插件市场让团队自行决定安装哪些。

### 管理 Skills 市场

Anthropic 没有集中决策团队，而是有机地发现最有用的 skills。有人可将 skill 上传到 GitHub 沙箱文件夹，在 Slack 中分享。获得关注后提交 PR 移入市场。

### 组合 Skills

依赖管理尚未原生支持，但可通过名称引用其他 skills，模型会在安装后调用。

### 衡量 Skills

使用 PreToolUse 钩子记录公司内部 skill 使用情况，发现热门或触发不足的 skills。

## 开始使用

Skills 最佳实践仍在演进。我们最好的 skills 大多始于几行代码和一个陷阱，随着 Claude 遇到新的边缘情况而不断完善。

理解 skills 的最佳方式是开始尝试，看看什么适合你。

---

*本文由 Anthropic 技术人员 Thariq Shihipar 撰写，他在 Claude Code 团队工作。*