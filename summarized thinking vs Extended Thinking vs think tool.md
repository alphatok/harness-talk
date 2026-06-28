# Summarized Thinking vs Extended Thinking vs Think Tool

---

### 1. 核心定义

解决的核心痛点在于**如何平衡大模型的"直觉速度"、"深度逻辑"与"多工具调用中的复杂决策"**。它提出了在不同业务场景下，如何有机协同模型的"快思考（总结式）"、"模型层慢思考（扩展式）"与"架构层慢思考（思考工具）"的下一代 Agent 计算范式。

---

### 2. 架构/方法分解（三者关系与运行层级）

#### 【Summarized Thinking】（直觉层 - 零延迟输出）

模型直接生成最终响应或 Action，思考被压缩。

- **本质**：单次 Forward（前向传播）直接出答案，将多步思考压缩为单一概率预测，追求低延迟与即时响应。
- **核心细节**：
  1. 零推理 Token 消耗
  2. 适合分类、情感分析、结构化数据提取及标准 SQL 执行等确定性原子任务

#### 【Extended Thinking】（模型层 - 隐式黑盒慢思考）

模型在输出最终答案前，在底层吐出大量隐藏的推理 Token（如 OpenAI o系列、DeepSeek-R1、Claude Extended Mode）。

- **本质**：牺牲时间与 Token 成本，通过模型内固化的强化学习（RL）本能进行生成前（Before Action）的全局规划。
- **核心细节**：
  1. 在产生最终答案前生成隐藏的推理 Token
  2. 具备极强的通用逻辑、涌现推理和自主纠错能力

#### 【Think Tool】（Agent 架构层 - 显式草稿纸机制）

AI 厂商/架构显式注入的一个虚无工具（一个输入为 `thought: string` 的自定义空操作 Tool）。

- **本质**：属于生成中（During/Between Actions）的局部刹车，让模型在收到工具返回的复杂数据后，强行停下来在专用的 Log/Scratchpad 中盘点业务规则。
- **核心细节**：
  1. 完全兼容流式传输并可作为标准 Tool Call 被日志审计
  2. 专门用来在多步复杂工具链（Long-horizon chains）中检测策略合规、校验前置条件

---

### 3. 避坑指南/反直觉教训

| 教训 | 说明 |
|------|------|
| **Extended Thinking 在长路径多工具调用中存在智商退化** | 纯粹依靠模型的 Extended Thinking 面对连续 5 次以上的工具调用时，模型容易在深层推理中遗忘早期的业务 Policy（之前的思考 Token 在上下文里不断累积产生噪声）。**Think Tool** 正是为了解决这个问题——迫使模型在每次拿到 Tool Output 后，像写便利贴一样只做局部推演。 |
| **Extended Thinking 并非包治百病的万灵药** | 在简单的业务表单校验或确定性路由中，强行引入扩展思维会带来 3-5 秒的致命延迟（Latency），还会因为大模型"过度思考（Overthinking）"导致原本简单的规则被幻觉推翻。 |
| **不要同时开启三者 + 塞满复杂 System Prompt** | 如果同时对一个模型压上 Extended Thinking、复杂的 System Prompt 规则，以及自定义的 `think` 机制，会导致严重的"过度反思综合征（Overthinking Loop）"，Agent 会自己和自己打架，不断调用 `think tool` 却不敢执行实际的写操作工具。 |

---

### 4. 针对 [Agent 系统设计与实现] 落地参考细节

#### 细节 1：数据流向设计——构建三级火箭流

**架构**：`Extended（全局总纲）→ Think Tool（单步纠偏）→ Summarized（快速反应）`

**实操方法**（复杂企业级 Agent 请求，如多账户金融清算）：

```
1. 接收请求 → Extended Thinking 开启全局慢思考 → 构思整体资金清算路径 → 生成 Goal Graph

2. Extended 给出第一步指令调用 get_balance → 拿到返回值 → 触发 Think Tool 节点 → 调用 think → 检查余额是否触发合规红线

3. 确认合规 → 路由到 Summarized 模式/轻量模型 → 快速、高并发执行 execute_transfer
```

#### 细节 2：利用 Think Tool 实现低成本、可控的策略对齐

**实操方法**：

1. 在 Agent 框架工具库中显式注册空工具：
   ```json
   {
     "name": "think",
     "description": "用于在复杂逻辑判断、检查前置条件、以及多工具输出分析时进行头脑风暴和规则校验"
   }
   ```

2. 在系统提示词中增加 Domain Examples：
   ```
   当你连续收到 3 次接口报错，或者需要做出高危删除动作前，必须首选调用 think 工具，列出至少 2 种替代方案
   ```

**收益**：将思考外置为工具，比 Extended Thinking 黑盒推理成本更低、可控性更高。

#### 细节 3：Agent Observer 中差异化流式解析与动态限额

**实操方法**：在 Parser 层将三者数据和逻辑彻底解耦：

| 组件 | 处理方式 |
|------|----------|
| **Extended Thinking** | 通过双通道流式传输将 `reasoning_content` 隔离，实时渲染给前端（缓解用户焦虑），对 Agent 状态机隐蔽。API Wrapper 封装时显式注入 `max_completion_tokens` 参数设置熔断阈值，防止费用雪崩。 |
| **Think Tool** | 作为标准 `tool_calls` 拦截。Agent 执行引擎拦截到此 `call_id` 时无需访问真实后端，只需将 `thought` 记录到 Memory/Trace 中作为可审计日志，立即返回 `{"result": "Thought logged successfully."}`，让模型无缝继续。 |

---

### 5. 三者对比速查表

| 维度 | Summarized Thinking | Extended Thinking | Think Tool |
|------|---------------------|-------------------|------------|
| **层级** | 直觉层（零延迟） | 模型层（黑盒慢思考） | 架构层（显式草稿纸） |
| **时机** | 生成时（单次 Forward） | 生成前（Before Action） | 生成中（Between Actions） |
| **Token成本** | 零推理消耗 | 高（隐藏推理Token） | 低（显式thought） |
| **可控性** | 低（直觉输出） | 低（黑盒） | 高（可审计日志） |
| **适用场景** | 确定性原子任务 | 全局规划、涌现推理 | 长工具链策略合规 |

---

### 6. 落地检查清单

- [ ] 判断任务复杂度：确定性原子 → Summarized；全局规划 → Extended；长工具链 → Think Tool
- [ ] 避免 Overthinking Loop：不同时开启三者 + 复杂 System Prompt
- [ ] 数据流设计：Extended（总纲）→ Think（单步）→ Summarized（执行）
- [ ] Think Tool 注册：description 明确用途 + System Prompt 附 Domain Examples
- [ ] Parser 解耦：Extended 双通道隔离；Think Tool 记录 Trace 不访问后端
- [ ] 费用熔断：Extended 注入 `max_completion_tokens` 限额