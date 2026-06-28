# Claude Think Tool 最佳实践

> 基于 Anthropic τ-Bench 和 SWE-Bench 验证结果提炼

---

## 一、核心认知

### 1.1 Think vs Extended Thinking

| 维度 | Extended Thinking | Think Tool |
|------|-------------------|------------|
| **时机** | 响应生成前 | 响应生成中（处理工具结果时） |
| **信息源** | 用户查询内 | 外部信息（工具输出） |
| **深度** | 全面规划 | 聚焦新发现 |
| **适用** | 无工具/简单调用 | 长工具链/策略密集 |

### 1.2 Think 工具本质

**一句话**：无副作用的草稿板，让 Claude 在行动前停下来验证规则、检查信息、规划下一步。

---

## 二、工具定义规范

### 2.1 标准模板

```json
{
  "name": "think",
  "description": "Use the tool to think about something. It will not obtain new information or change the database, but just append the thought to the log. Use it when complex reasoning or some cache memory is needed.",
  "input_schema": {
    "type": "object",
    "properties": {
      "thought": {
        "type": "string",
        "description": "A thought to think about."
      }
    },
    "required": ["thought"]
  }
}
```

**关键点**：
- description 明确"不获取新信息、不改数据库"
- 避免 Claude 误认为这是功能性工具
- 输入极简：只有一个 thought 字符串

### 2.2 领域适配（SWE-Bench 版）

```json
{
  "name": "think",
  "description": "Use the tool to think about something. It will not obtain new information or make any changes to the repository, but just log the thought. Use it when complex reasoning or brainstorming is needed. For example, if you discover the source of a bug, call this tool to brainstorm several unique ways of fixing the bug, and assess which change(s) are likely to be simplest and most effective."
}
```

**适配要点**：
- 明确不改仓库
- 给具体使用场景示例（发现 bug → brainstorm 修复方案）

---

## 三、系统提示词设计

### 3.1 结构模板

```
## 使用 think 工具

在收到工具结果后采取任何行动或响应用户之前，使用 think 工具作为草稿板：
- 列出适用于当前请求的具体规则
- 检查是否已收集所有必要信息
- 验证计划行动是否符合所有策略
- 遍历工具结果确保正确性

以下是在 think 工具内遍历的示例：
<think_tool_example_1>
[领域特定场景1，展示决策树]
</think_tool_example_1>

<think_tool_example_2>
[领域特定场景2，展示推理细节]
</think_tool_example_2>
```

### 3.2 设计要点

| 要素 | 说明 |
|------|------|
| **位置** | 复杂指导放系统提示词，而非工具描述 |
| **示例数量** | 2-3个覆盖典型场景 |
| **示例结构** | 需验证项 + 规则检查 + 计划步骤 |

---

## 四、适用场景判断

### 4.1 使用 Think Tool

| 场景 | 原因 |
|------|------|
| **长工具调用链** | 需在每步处理后验证、可能回溯 |
| **策略密集环境** | 详细规则需逐一对照 |
| **顺序决策（错误代价高）** | 每步依赖前序，失误累积 |
| **客服、合规场景** | 一致性优于单次成功 |

### 4.2 不使用 Think Tool

| 场景 | 原因 |
|------|------|
| 单次/并行工具调用 | 无需中间验证 |
| 简单指令跟随 | 默认行为足够 |
| 编码/数学/物理（无工具） | 用 Extended Thinking |
| 信息充足 | 无信息缺口 |

---

## 五、性能基准参考

| 场景 | 配置 | pass^1 | 说明 |
|------|------|--------|------|
| **Airline（策略复杂）** | Think + 优化Prompt | 0.570 | +54% vs Baseline |
| **Airline** | Think alone | 0.404 | 提示词关键 |
| **Retail（策略简单）** | Think alone | 0.812 | 无需额外提示 |
| **SWE-Bench** | Think + 适配描述 | 0.623 | +1.6% |

---

## 六、评估指标选择

### 6.1 pass^k vs pass@k

| 指标 | 定义 | 适用场景 |
|------|------|----------|
| **pass@k** | k次试验至少1次成功 | 单次成功足够 |
| **pass^k** | k次试验全部成功 | **一致性关键**（客服、合规） |

### 6.2 Think 工具的价值

- pass^k 在 k=5 仍保持提升
- 说明不是靠运气，而是**系统性改善**
- 边缘场景和异常情况处理更可靠

---

## 七、落地检查清单

### 设计阶段

- [ ] 判断是否需要 Think（长链/策略密集/顺序决策）
- [ ] 工具定义明确"无副作用"
- [ ] 领域适配示例写入 description

### 提示词阶段

- [ ] 复杂指导放系统提示词
- [ ] 提供2-3个领域特定示例
- [ ] 示例包含：需验证项 + 规则检查 + 计划

### 测试阶段

- [ ] 使用 pass^k 评估一致性
- [ ] 对比 Think alone vs Think + Prompt
- [ ] 简单域验证是否过度工程

### 监控阶段

- [ ] 观察 Claude 何时调用 Think
- [ ] 检查思考内容是否符合预期结构
- [ ] 收集失败案例补充示例