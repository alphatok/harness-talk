# Perplexity Agent Skills 设计最佳实践

> 基于 Perplexity 生产经验提炼的核心落地要点

---

## 一、核心认知转变

### 1.1 写 Skill ≠ 写代码

| Python Zen | Skill Zen |
|------------|-----------|
| Simple is better than complex | **Skill is a folder. Complexity is the feature.** |
| Explicit is better than implicit | **Activation is implicit pattern matching. Progressive disclosure.** |
| Sparse is better than dense | **Context is expensive. Maximum signal per token.** |
| Special cases aren't special enough | **Gotchas ARE the special cases (highest-value content).** |
| If easy to explain, may be a good idea | **If easy to explain, model already knows it. Delete it.** |

**关键**：写好代码的思维模式在写 Skill 时是反模式。

---

## 二、Skill 的四个本质

### 2.1 Skill 是目录

```
skill-name/
├── SKILL.md          # 核心指令（≤5000 tokens）
├── scripts/          # 代码：给模型复用而非重写
├── references/       # 重文档：条件加载
├── assets/           # 模板、schema、数据
└── config.json       # 用户初始化配置
```

**层级策略**：
- 300个话题 → 分组20个领域 → 每领域15个话题
- 多级层级需要配套快速索引工具
- 信息架构的精心编排是必要成本

### 2.2 Skill 是格式

**Frontmatter 必备**：
- `name`: 全小写、无空格、可用连字符，必须匹配目录名
- `description`: 路由触发器，写"Load when..."而非"This Skill does..."
- `depends`: 层级依赖
- `metadata`: 评审和评估用

### 2.3 Skill 是可调用的

**渐进式加载**：
1. `load_skill(name="...")` 调用
2. 目录复制到沙箱
3. 递归加载 `depends:` 依赖
4. 剥离 frontmatter，模型只看到 body

### 2.4 Skill 是渐进式的

| 层级 | 加载内容 | Token预算 | 支付时机 |
|------|----------|-----------|----------|
| **Index** | name + description | ~100 tokens | 每次会话必付 |
| **Load** | SKILL.md body | ~5000 tokens | Skill加载时 |
| **Runtime** | scripts/、references/、assets/ | 无上限 | 模型读取时 |

---

## 三、何时需要 Skill

### 3.1 需要 Skill 的场景

- 模型无特殊上下文会出错
- 需要跨运行的一致性/确定性
- 知识持久但不在训练数据中（企业流程、内部工具）
- **品味领域**（设计偏好、风格指导）

### 3.2 不需要 Skill 的场景

- 模型已知的命令序列（git 命令）
- 重复系统提示词的内容
- 变化频率高于维护频率的内容
- 频繁变化的 MCP endpoint

---

## 四、Skill 构建五步法

### Step 0：先写 Evals

**评估来源**：
- 生产环境真实查询
- 已知失败案例
- 边界混淆（邻域但路由错误）

**必须验证**：
- Skill 正确加载时机
- 包含负例 + 禁止加载例

### Step 1：Description（最难）

**Checklist**：
- ✅ 以 "Load when..." 开头
- ✅ ≤50 words
- ✅ 描述用户意图（来自真实查询）
- ❌ 不总结工作流

**失败模式**：写 "This Skill does..." 而非 "Load when..."

### Step 2：Body

**原则**：
- 跳过显而易见的内容
- 不写命令序列，写意图："Cherry-pick onto clean branch. Resolve conflicts preserving intent."
- 聚焦 **gotchas**（负例是最高价值内容）
- 条件/重内容 → 移到 spokes 文件

### Step 3：层级利用

| 目录 | 用途 | 原则 |
|------|------|------|
| `scripts/` | 确定性逻辑 | 给代码复用，不重建 |
| `references/` | 重文档 | 条件加载（如API错误码） |
| `assets/` | 输出模板 | 模型复制填充 |
| `config.json` | 用户初始化 | 首次配置、后续复用 |

### Step 4：迭代

- 在分支上大量迭代
- 建立 hero query 集 + evals
- Description 的微小改动有巨大路由影响
- **先完成所有迭代再合并**

### Step 5：Ship

---

## 五、Skill 维护

### 5.1 Gotchas Flywheel

**核心增长模式**：
| 触发 | 行动 |
|------|------|
| Agent 失败 | 加 gotcha |
| Skill 被错误加载 | 收紧 description + 加负例 eval |
| Skill 未加载 | 加关键词 + 加正例 eval |
| 系统提示词变化 | 检查冲突/重复 |

**原则**：Skills 是 append-mostly，gotchas 是最高价值积累区。

### 5.2 Eval Suites 类型

| Eval类型 | 检查内容 |
|----------|----------|
| **加载评估** | precision/recall/禁止加载检查 |
| **渐进加载评估** | 是否读取 accessory 文件 |
| **端到端评估** | LLM judge 基于 rubric 打分 |

**跨模型验证**：Sonnet、GPT、Claude Opus 行为差异大，必须分别测试。

---

## 六、关键原则

### Token Tax

> "Would the agent get this wrong without this instruction?"

每句话都必须通过此测试。不必要 = 不能存在。

### 短文更难写

> Pascal: "I have only made this letter longer because I have not had the time to make it shorter."

- 好 Skill 写起来难
- 5分钟 PR 的 Skill 几乎不合格
- LLM 写的 Skill 对 LLM 自己无益

### 远距离作用

- 添加新 Skill 可能破坏其他 Skill（即使未修改）
- Description 改动需 evals 支持
- 维护期改 description = 越轨

---

## 七、落地检查清单

### 发布前

- [ ] Evals 包含正例 + 负例 + 禁止加载例
- [ ] Description ≤50 words，以 "Load when..." 开头
- [ ] Body ≤5000 tokens，无命令序列
- [ ] Gotchas 区已初始化
- [ ] 跨模型（GPT/Claude）测试通过

### 维护期

- [ ] 新增失败 → 加 gotcha（不改 description）
- [ ] 加 gotcha → 同步更新 evals
- [ ] 系统提示词变更 → 检查 Skill 冲突