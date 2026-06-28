# 设计、优化和维护 Perplexity 的 Agent Skills

**来源**: https://research.perplexity.ai/articles/designing-refining-and-maintaining-agent-skills-at-perplexity  
**发布日期**: 2026年5月1日

---

Perplexity 的前沿智能体产品建立在模块化 Agent Skills 封装的知识和领域专业知识基础上。我们在技术环境中维护一个精心策划的 Skills 库。这些 Skills 包括支持 Perplexity Computer 的通用工具；金融、法律和健康等垂直领域的专业能力；以及满足用户需求的众多模块。有些 Skills 调用频率低但调用时至关重要。为确保一致的用户体验，Perplexity 的 Agents 团队将 Skill 质量与代码质量同等重视。

开发高质量 Skill 所需的直觉和最佳实践与传统软件开发有显著不同。Agents 团队审核了许多优秀工程师在开发 Skills 时的 PR。结果几乎总是有大量修订建议。这是因为许多编写代码的有效模式在 Skill 创建中变成了反模式。

例如，如果引用 PEP20（Python 之禅）的格言，很快就会发现编写好的 Python 代码与编写好的 Skills 完全不同。在20条智慧中，至少有一半在编写 Skills 时是完全错误的或具有误导性。以下是其中五条：

| Python 之禅 | Skills 之禅 |
|---------------|---------------|
| 简单优于复杂 | Skill 是文件夹，不是文件。复杂性是特性。 |
| 明确优于隐式 | 激活是隐式模式匹配。渐进式披露。 |
| 稀疏优于密集 | 上下文成本高。每个 token 都要承载最大信号。 |
| 特殊情况不足以打破规则 | Gotchas 就是特殊情况（最高价值内容）。 |
| 如果实现容易解释，可能是个好主意 | 如果容易解释，模型已经知道了。删掉它。 |

---

## 什么是 Skill？

当你写 Skill 时，你不是在写普通软件（尽管 Skills 现已是智能体系统的主要逻辑引擎）。相反，你是在为模型及其环境构建上下文。Skill 有不同的约束和设计原则。如果你像写代码一样写 Skill，你会失败。

Skill 至少是四件事，特别是在 Perplexity 的构建方式中。

### Skill 是目录

Skill 不仅仅是单个 SKILL.md 文件。很多情况下，Skill 包含多个文件。在以 Skill 名称命名的目录下，可能有：

- **SKILL.md**: frontmatter 和指令
- **scripts/**: 模型运行的代码，而非重写
- **references/**: 重文档，条件加载
- **assets/**: 模板、schema 和数据
- **config.json**: 首次运行用户设置

这种 hub-and-spoke 模式允许保持 Skills 聚焦紧凑，可以创造性使用文件夹结构。有时，特别复杂的 Skills 需要多级层级帮助模型更好导航。假设一个 Skill 需要覆盖300个话题，可分组为20个领域。在300个话题中可靠选择对当今最好的前沿模型也是未解挑战。让模型先定位到20个领域之一，再在其中的15个话题中选择，是更简单的选择问题。

多级层级提供价值的一个例子：我们团队在今年税务季为 Computer 的美国所得税能力采用了三级主题嵌套。考虑到税法的复杂性，这种层级不可或缺：早期测试中，向模型展示包含美国《国内税收法典》全部1,945节的单个文件夹，结果比不加载 Skill 更差。将信息组织成逻辑子分区对确保高精度读取操作至关重要。

但这层级不是免费的。层级增加需要信息架构上更多编排来管理间接性。我们设计了快速参考指南、自定义搜索工具等，帮助模型以最少间接性定位信息。

### Skill 是格式

Skill 是一种格式。核心 SKILL.md 文件必须有名称和描述。此外，Skill 需要精确匹配其所在目录名。名称必须全小写、无空格、可用连字符。描述是路由触发器。这是常见失败点：描述不是 Skill 功能的内部文档，而是模型何时加载 Skill 的指令。所以你常看到 "Load when"，而非 "This Skill does"。这很重要，因为大多数实现将描述注入模型上下文的方式。

### Skill 是可调用的

Skill 是可调用的。智能体在运行时加载 Skill。重要的是，Skills 不是总是打包在上下文中。默认情况下，大多数智能体系统按需渐进式展开 Skills。

过程：
1. Computer 调用 `load_skill(name="...")`
2. Computer 将 Skill 目录复制到隔离执行沙箱
3. Computer 递归自动加载 "depends:" 标签中的依赖
4. Computer 剥离 frontmatter，智能体只看到 body 和附加文件

### Skill 是渐进式的

Skills 是渐进式的。在 Computer 中，有三层上下文成本：

| 层级 | 加载内容 | Token预算 | 支付时机 |
|------|------------|--------|--------------|
| **Index** | 每个 Skill 的 name + description | ~100 tokens per Skill | 每次会话、每个用户，始终支付 |
| **Load** | SKILL.md body | ~5,000 tokens | Skill 加载时 |
| **Runtime** | scripts/、references/、assets/、subskills、FORMATTING.md、SPECIAL_CASES.md | 无上限 | 仅当智能体读取时 |

---

## 何时需要 Skill？

Agents 团队经常被问及某个领域是否真的需要 Skill。很少能从第一原理给出确定答案。真正搞清楚的唯一方法是从没有 Skill 的智能体开始，运行多个 hero 查询，然后判断智能体是否做得好。

### 需要 Skill 的场景

许多任务已在训练模型的分布中。只有当你想以某种特定方式改变行为（无法用一句话在提示词中实现）时才需要 Skill。所以，需要 Skill 的场景是：智能体无特殊上下文会出错，或需要跨运行的一致性/确定性。

可能是知识持久但不在训练数据中（企业工作流、内部工具），或品味问题。例如，我们有多个设计相关 Skills 由 Henry Modisett（设计主管）编写。这些 Skills 中每个 token 存在的原因是 Henry 在网站和 PDF 设计上有非常好的品味。

### 不需要 Skill 的场景

我们看到很多 Skills 中工程师写了一系列按顺序执行的 git 命令。这不必要，因为模型已经知道怎么做——它适合做文档但不适合做 Skill。

我们看到 Skills 重复系统提示词指令。不需要为此做 Skill。大多数请求相关的知识应该放在全局上下文，而非条件加载的 Skill 中。

如果内容变化速度快于你的维护速度，不需要 Skill。例如，如果你调用某个远程 MCP endpoint 且其工具或版本频繁变化，不应注入到 Skill 中。

### 每个 Skill 都是税收

可以对 Skill 中每句话应用的测试："Would the agent get this wrong without this instruction?"（没有这条指令智能体会出错吗？）如果句子不需要在那里，它就不能在那里，因为每个人每次都在支付这个成本。

> "Je n'ai fait celle-ci plus longue que parce que je n'ai pas eu le loisir de la faire plus courte." — Blaise Pascal（我之所以把这封信写得更长，是因为我没有时间把它写得更短）

就像 Pascal，你需要在每个 Skill 上投入时间。写短的 Skill 很难。如果你的 Skill 容易写，它可能太长或不应该存在。好的 Skill 尽可能短。

---

## 如何构建 Skill

### Step 0：先写 Evals

先写一些评估。评估案例来源：
- **真实用户查询**：从生产环境或信任网络采样
- **已知失败**：智能体因为 Skill 不存在而失败
- **邻域混淆**：接近领域边界但路由到另一个 Skill

至少要确保测试 Skill 在需要时加载。从相似的负例和正例开始。负例非常强大，可能比正例更重要。

### Step 1：Description

这是 Skill 中最难的一行。它是路由触发器，不是文档。要正确设置名称和描述，你不在乎 Skill 内容。你只关心 Skill 是否在正确时机加载注入，且无靶向外副作用——这是第一大失败模式。

坏的描述描述 Skill 做什么或为什么有用。好的描述说智能体何时应该加载 Skill。例如，有监控 PR 的东西。不要写 Skill 做什么。写工程师沮丧时说的话，希望确保 PR 工作，如 "babysit"、"watch CI"、"make sure this lands"。

**检查清单**：
- 以 "Load when..." 开头
- 目标 ≤50 words
- 描述用户意图，理想来自真实查询
- 不总结工作流

### Step 2：Body

接下来，写 Skill 内容本身。向 LLM 传达工作流与向同事传达完全不同。学习新软件工具时，工程师可能需要读文档、请有经验的人演示、学习如何使用。而对存在超过一年的软件工具，你只需提名字，LLM 就有所有信息。

写 body 时，**跳过显而易见的内容**。不要写命令序列。

例如，不需要写：
```
git log # find the commit
git checkout main
git checkout -b <clean-branch>
git cherry-pick <commit>
```

而是写：
> "Cherry-pick the commit onto a clean branch. Resolve conflicts preserving intent. If it can't land cleanly, explain why."（将 commit cherry-pick 到干净分支。保留意图解决冲突。如果不能干净落地，解释原因。）

模型用后者会做得更好。不要过度规定（railroad），要灵活允许多种方法可行。

接下来，聚焦 **gotchas 或负例**。这些是极高信号内容。每次智能体出错加一行，通过运行学习，gotchas 会有机增长。

最后，如果有任何条件性或内容极重的部分，从 SKILL.md 移到 spokes（scripts/、references/、assets/）。

### Step 3：使用层级

| 目录 | 用途 | 原则 |
|-----------|---------|-----------|
| `scripts/` | 每次运行智能体会重建的确定性逻辑 | 给它代码复用，不重建 |
| `references/` | 仅当条件满足时加载的重文档 | "如果 API 返回非 200，读 api-errors.md" |
| `assets/` | 智能体复制填充的输出模板 | report-template.md、输出 schema |
| `config.json` | 首次运行用户设置 | 询问 Slack channel，保存，下次复用 |

### Step 4：迭代

在分支上大量迭代。从没有 Skill 的主分支开始，迭代，构建 hero query 集，运行大量 evals。审核 Skill 代码的人会感谢你提交一个带评估集的单一变更集。

### Step 5：发布

发布它。

---

## 如何维护 Skill

### Gotchas Flywheel

从这时起，gotchas 列表会大量增长或变化。我们经常看到工程师提交未经评估的 PR，比如改描述。Skill 合并后改描述，你就偏离轨道了。如果要改决定 Skill 路由的内容，需要写支持变更的 evals。

Skills 是 append-mostly（追加为主）。gotchas 区随时间积累最高价值：

| 触发 | 行动 |
|---------|--------|
| 智能体在某事上失败 | 加 gotcha |
| 智能体错误加载 Skill | 收紧描述 + 加负例 evals |
| 智能体应该加载时未加载 | 加关键词 + 加正例 evals |
| 系统提示词变化 | 检查冲突或重复 |

### Eval Suites

Perplexity 运行多种评估套件检查不同方面：
- **Skill 加载和文件读取**：precision、recall 和禁止检查
- **渐进式加载评估**：智能体是否读取附属文件？
- **端到端任务完成**：LLM judge 基于 rubric 打分
- **跨模型验证**：GPT、Claude Opus、Claude Sonnet 行为差异大

---

## 总结要点

构建越多 Skills，你越擅长构建。如果还没用 Skills 自动化任务，立即开始。

关键要点：
- 先写 evals 再写 Skill。包含负例和禁止加载。
- Description 是难点。"Load when..."（每个词都消耗注意力）。
- Gotchas 是极高价值内容。开始时薄，随智能体失败增长。
- 记住添加新 Skill 可能破坏其他已存在 Skill（警惕远距离作用）。
- 每次编写和维护 Skill 都使用所有可用工具。