# TLDR: Claude "think" 工具

> 核心：给 Claude 一个专用"草稿板"工具，在长工具调用链中停下来结构化思考

---

## 一、核心定义

**一句话**：通过添加一个无副作用、只记录思考的 `think` 工具，让 Claude 在处理外部信息（工具结果）时能停下来验证规则、检查信息、规划下一步，显著提升策略合规性和顺序决策可靠性。

---

## 二、架构分层

| 层级 | 要素 | 本质 | 核心细节 |
|------|------|------|----------|
| **工具层** | `think` 工具定义 | **无副作用的草稿板** | 1. 不获取新信息、不改数据库、只追加日志；2. 输入只有一个 `thought` 字符串 |
| **触发层** | 使用时机 | **信息缺口感知** | 1. 收到工具结果后、行动前调用；2. 不同于 extended thinking（响应前），think 用于响应过程中处理外部信息 |
| **结构层** | 思考内容 | **四步检查清单** | 1. 列适用规则；2. 检查信息完整性；3. 验证合规；4. 遍历结果正确性 |

---

## 三、性能数据

| 域 | 配置 | pass^1 | 相对提升 |
|-----|------|--------|----------|
| **Airline（难）** | Think + 优化Prompt | 0.570 | **+54%** vs Baseline(0.370) |
| **Retail（简）** | Think alone | 0.812 | +3% vs Baseline(0.783) |
| **SWE-Bench** | Think | 0.623 | +1.6% vs 无Think |

---

## 四、避坑指南

| 陷阱 | 教训 |
|------|------|
| **Extended thinking ≠ Think tool** | 前者是响应前的深度规划；后者是响应中处理外部信息的即时检查 |
| **困难领域提示词关键** | 单纯加工具改善有限，必须配合领域特定示例提示 |
| **简单领域无需过度工程** | Retail 域 Think alone 即最佳，过度提示反而浪费 |
| **不用场景浪费 token** | 非顺序调用、简单指令跟随不需要 Think |

---

## 五、落地参考（Agent 系统设计，3个实操细节）

### 1. 工具定义模板

```json
{
  "name": "think",
  "description": "Use the tool to think about something. It will not obtain new information or change the database, but just append the thought to the log. Use it when complex reasoning or some cache memory is needed.",
  "input_schema": {
    "type": "object",
    "properties": {
      "thought": {"type": "string", "description": "A thought to think about."}
    },
    "required": ["thought"]
  }
}
```

**落地要点**：description 强调"不获取新信息、不改数据库"，避免模型误以为这是个有副作用的功能工具。

### 2. 系统提示词结构

```
## 使用 think 工具

在收到工具结果后采取任何行动或响应用户之前，使用 think 工具作为草稿板：
- 列出适用于当前请求的具体规则
- 检查是否已收集所有必要信息
- 验证计划行动是否符合所有策略
- 遍历工具结果确保正确性

[附2-3个领域特定示例，展示决策树和推理细节]
```

**落地要点**：复杂指导放**系统提示词**而非工具描述，提供更广上下文。

### 3. 适用场景判断

| 使用 Think | 不使用 Think |
|------------|---------------|
| 长工具调用链 | 单次/并行工具调用 |
| 策略密集环境 | 简单指令跟随 |
| 顺序决策、错误代价高 | 信息充足、默认行为足够 |

**落地要点**：用 `pass^k`（一致性指标）而非 `pass@k`（至少成功一次）评估可靠性场景。