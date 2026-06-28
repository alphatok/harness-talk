# TLDR — Claude Tool Use 完全教程（2026）

> 原文：[Claude Tool Use 完全教程:从 Function Calling 到 Agent 循环的实战指南(2026)](https://ofox.ai/zh/blog/claude-tool-use-function-calling-complete-guide-2026/)

---

## 核心流程（4 步）

`定义工具(JSON Schema)` → `Claude 返回 tool_use` → `执行工具 → 返回 tool_result` → `Claude 生成回答`

---

## tool_choice 三种模式

| 模式 | 行为 | 适用场景 |
|------|------|---------|
| `auto` | 模型自主判断是否调工具 | 通用对话 + 工具增强（默认推荐） |
| `any` | 强制至少调一个工具 | 明确需要工具结果的流程步骤 |
| `tool` | 强制调指定工具 | 流程编排里的固定步骤 |

**经验：** 大部分生产系统用 `auto` 就够了。

---

## 工具描述要点

- `description` 比 `name` 重要 — 写清**什么时候用**，而非只写干什么
- 易混淆工具用 **"不用于"** 划清边界
- 参数描述带格式约束（YYYY-MM-DD、范围、enum 列表）
- 工具数量 **≤ 10 个**，超了按意图预筛选

---

## Agent 循环

```
用户提问 → 模型思考 → 调用工具 → 拿到结果
                ↑                        ↓
                └── 还需要更多信息吗？ ←──┘
                        ↓ 不需要了
                    生成最终回答
```

**3 个常见坑：**
1. 必须设最大循环次数（如 10 轮），防死循环
2. 工具执行失败要把错误返回给模型，不要静默吞掉
3. 管理上下文长度，避免无限增长

---

## 并行工具调用

- Claude 单轮可返回多个 `tool_use` — 并行执行，ID 配对即可
- 顺序可乱，`tool_use_id` 对上就行

---

## 流式输出要点

- `content_block_start` → `content_block_delta` → `content_block_stop`
- 工具参数以 JSON 片段流式传输，**必须拼完再解析**
- 技巧：tool_use 开始时先显示"正在查询…"提升体验

---

## Extended Thinking

- 工具多、场景复杂时开，模型会先推理再选工具
- 代价：延迟增加、token 消耗上升
- 适合复杂多步骤流程，简单查询没必要

---

## 四种使用场景

| 场景 | 关键注意 |
|------|---------|
| 查询增强 | 工具返回数据要截断，别全喂给模型 |
| 操作执行 | 不可逆操作必须加确认机制 |
| 多步骤编排 | 每步 tool_result 要包含足够上下文 |
| 结构化数据提取 | 用 `tool` 模式 + JSON Schema 约束输出格式 |

---

## 常见问题排查

| 问题 | 解法 |
|------|------|
| 模型不调工具 | 检查 description 触发条件是否清晰 |
| 调错工具 | 多个工具 description 有重叠，明确边界 |
| 参数格式不对 | Schema 加 enum/pattern/format 约束 |
| 工具调用死循环 | 检查返回值完整性 + 设循环上限 |

---

## 与 OpenAI 差异

- 字段名：Claude 用 `tool_use`，OpenAI 用 `function`
- Claude 对复杂参数 Schema 的理解更准确
- 并行调用默认支持，无需额外参数
- 走 OpenAI 兼容协议可一套代码兼容两者

---

## 入门建议

从 `auto` 模式 + **2-3 个工具**开始，别一上来搞 20 个工具的 Agent 系统。