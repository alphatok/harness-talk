# TLDR: Perplexity Agent Skills 设计要点

> 核心：写 Skill ≠ 写代码，传统代码思维模式是反模式

---

## 一、Skill 本质

| 属性 | 要点 |
|------|------|
| **目录** | Skill = 文件夹，含 SKILL.md + scripts/ + references/ + assets/ |
| **格式** | name 全小写无空格，description 写 "Load when..." 而非 "This does..." |
| **可调用** | 运行时按需加载，非预装 |
| **渐进式** | Index(~100t) → Load(~5000t) → Runtime(无上限) |

---

## 二、何时需要 Skill

| 需要 | 不需要 |
|------|--------|
| 模型无上下文会出错 | 模型已知的命令序列 |
| 需跨运行一致性 | 重复系统提示词内容 |
| 企业流程/内部工具 | 变化频率 > 维护频率 |
| 品味领域（设计偏好） | - |

**原则**：每句话必须通过 "Would the agent get this wrong without this instruction?" 测试

---

## 三、构建五步法

| Step | 核心要点 |
|------|----------|
| **0: Evals** | 正例 + 负例 + 禁止加载例，负例比正例更重要 |
| **1: Description** | ≤50 words，以 "Load when..." 开头，描述用户意图而非工作流 |
| **2: Body** | 跳过显而易见，聚焦 gotchas，写意图不写命令序列 |
| **3: Hierarchy** | scripts/代码复用、references/条件加载、assets/模板填充 |
| **4: Iterate** | 大量迭代后再合并，description 微调有巨大路由影响 |

---

## 四、维护 Flywheel

| 触发 | 行动 |
|------|------|
| Agent 失败 | 加 gotcha（不改 description） |
| Skill 被错误加载 | 收紧 description + 加负例 eval |
| Skill 未加载 | 加关键词 + 加正例 eval |
| 系统提示词变化 | 检查冲突/重复 |

**原则**：Skills 是 append-mostly，gotchas 是最高价值积累区

---

## 五、关键原则

1. **Token Tax**: 不必要 = 不能存在
2. **短文更难写**: 5分钟 PR 的 Skill 几乎不合格
3. **远距离作用**: 新 Skill 可能破坏其他 Skill（即使未修改）
4. **跨模型验证**: Sonnet/GPT/Claude 行为差异大