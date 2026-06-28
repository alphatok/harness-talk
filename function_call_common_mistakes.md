这是一份为你深度整合、修正并全面升级的**终极典藏版指南**。它剔除了原有的语法和认知错误，融合了最新的模型特性与深水区生产经验。建议直接收藏或导出为 Markdown。

---

# 🏆 终极典藏版：LLM Function Call 定义与实现全指南

Function Call（也称 Tool Use / Tool Calling）是赋予大语言模型（LLM）与外部世界交互能力的接口机制。它与 MCP（Model Context Protocol）的本质区别在于：MCP 负责**协议层**的工具发现与上下文协商，而 Function Call 专注于**接口层**单次推理中参数的提取与传递。

> ⚠️ 二者并非互斥：MCP 动态发现的工具，最终仍通过 Function Call 注入 LLM 推理。MCP 解决"有哪些工具"，Function Call 解决"这一轮调哪个、传什么参数"。

---

## 一、 核心概念对比

| 维度 | MCP (Model Context Protocol) | Function Call |
| --- | --- | --- |
| **层级** | 协议层 / 架构层 | 接口层 / 推理层 |
| **核心关注点** | 客户端与服务端的连接、工具动态发现 | 精准提取自然语言中的参数并触发执行 |
| **复杂度** | 高（涉及完整生命周期、鉴权、资源挂载） | 低（单次 API 调用的 JSON 格式约定） |
| **适用场景** | 跨应用、跨会话的标准化工具生态池构建 | 单体应用或 Agent 内部的外部 API 调用 |

---

## 二、 Function Call 的标准定义方式

主流模型目前都向 OpenAI 的 JSON Schema 标准靠拢，但在外层结构上略有差异。

### 1. OpenAI 风格（行业事实标准）

```json
{
  "name": "get_weather",
  "description": "获取指定城市的天气信息",
  "strict": true, // 开启结构化输出（GPT-4o 及以后支持）
  "parameters": {
    "type": "object",
    "properties": {
      "city": {
        "type": "string",
        "description": "城市名称，如北京、上海"
      },
      "date": {
        "type": ["string", "null"], // ⚠️ strict 模式下可选字段必须用 union type 含 null
        "description": "日期，格式YYYY-MM-DD，默认为今天"
      }
    },
    "required": ["city", "date"], // ⚠️ strict 模式下所有字段必须列入 required，无一例外
    "additionalProperties": false // strict 模式强制要求 false
  }
}
```

> **🔴 strict 模式的硬性约束（极易踩坑）**：
> 1. **所有字段必须进 `required`**：即使该字段是可选的，也必须列入 `required` 数组。
> 2. **可选字段用 `type: ["string", "null"]`**：而非"不写进 required"。这是 strict 模式表达可选性的唯一方式。
> 3. **`additionalProperties` 必须为 `false`**。
> 4. **不支持的高级特性**：`$ref`、`default`、`format`、`oneOf`（在根 schema 层）、`patternProperties` 均不可用。
> 5. **`default` 不保证生效**：模型可能不填充默认值，需在代码层兜底。
>
> 非 strict 模式下（`strict: false` 或不写），JSON Schema 没有 `optional` 关键字，不写入 `required` 即表示可选，但输出不保证 100% 符合 schema。

### 2. Anthropic Claude 风格

```json
{
  "name": "get_weather",
  "description": "获取指定城市的天气信息",
  "input_schema": { 
    "type": "object",
    "properties": {
      "city": { "type": "string" },
      "date": { "type": "string" }
    },
    "required": ["city"]
  }
}
```

> **Claude 与 OpenAI 响应格式差异（易混淆）**：
> - OpenAI：`message.tool_calls[].id` + `message.tool_calls[].function.arguments`（字符串）
> - Claude：`content` 数组中的 `tool_use` block，含 `id` + `input`（已解析的对象，非字符串）
> - 回传工具结果时：OpenAI 用 `role: "tool"` + `tool_call_id`；Claude 用 `role: "user"` + `tool_result` block + `tool_use_id`

---

## 三、 核心实现流程（三步走）

构建一个健壮的 Function Call 系统需要以下标准代码骨架：

### Step 1: 定义稳健的函数注册表

```python
class FunctionRegistry:
    def __init__(self):
        self._functions = {}
        self._schemas = []
    
    def register(self, func, name=None, description="", schema=None):
        """注册可供 LLM 调用的本地函数"""
        func_name = name or func.__name__
        self._functions[func_name] = func
        
        self._schemas.append({
            "name": func_name,
            "description": description,
            "parameters": schema
        })
    
    def get_schemas(self):
        """获取所有工具定义，注入 LLM 请求"""
        return self._schemas
    
    def call(self, name, arguments):
        """执行调用，并处理潜在的幻觉和异常"""
        if name not in self._functions:
            raise ValueError(f"Error: Function '{name}' does not exist.")
        # 注意 Python 解包语法的正确使用
        return self._functions[name](**arguments)

```

### Step 2: 拦截与处理 LLM 响应

```python
import json

def process_function_call(response, registry):
    """解析 LLM 返回的 Tool Calls 并执行"""
    # 注意：新版 API 的 finish_reason 为 "tool_calls"
    # "function_call" 是已废弃的 legacy Function API，仅为兼容旧代码保留
    if response.choices[0].finish_reason == "tool_calls":
        tool_calls = response.choices[0].message.tool_calls
        
        for tool_call in tool_calls:
            func_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
                result = registry.call(func_name, arguments)
            except Exception as e:
                # 必须捕获异常，将其作为上下文喂回给模型让其自纠正
                result = f"Execution failed: {str(e)}"
            
            # ⚠️ tool_call_id 必须原样回传，否则下一轮 API 调用会报错
            # 多个工具调用时，每个 tool_result 必须一一对应其 tool_call_id
            yield {
                "role": "tool",
                "tool_call_id": tool_call.id,  # 不可省略、不可编造
                "content": str(result)
            }
```

> **🔴 tool_call_id 是多轮对话的生命线**：
> - 每一个 `tool_call` 都有唯一 `id`，回传结果时 `tool_call_id` 必须严格一一对应。
> - 漏传、错配、编造都会导致 OpenAI/Claude API 直接 400 报错。
> - 当模型并行发起 3 个工具调用时，必须返回 3 条对应的 tool result 消息。

### Step 3: 构建闭环多轮对话

```python
def chat_with_tools(messages, functions, max_loops=5, max_retry_per_tool=2):
    """带防御机制的工具调用循环"""
    retry_counter = {}  # 记录每个工具的连续失败次数，防止自纠正死循环
    
    for loop in range(max_loops):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=functions,
            tool_choice="auto",
            parallel_tool_calls=True,  # 是否允许并行调用，依赖链场景设 False
            timeout=30  # 单次请求超时
        )
        
        assistant_msg = response.choices[0].message
        messages.append(assistant_msg)
        
        # 退出条件：模型不再调用工具，直接回复自然语言
        if not assistant_msg.tool_calls:
            return assistant_msg.content
            
        # 处理调用并将结果追加到 messages 继续下一次请求
        for tool_call in assistant_msg.tool_calls:
            func_name = tool_call.function.name
            # 同一工具连续失败超限，强制熔断并告知模型换方案
            if retry_counter.get(func_name, 0) >= max_retry_per_tool:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": f"工具 {func_name} 已连续失败 {max_retry_per_tool} 次，禁止再次调用，请改用其他方案。"
                })
                continue
                
            try:
                arguments = json.loads(tool_call.function.arguments)
                result = registry.call(func_name, arguments)
                retry_counter[func_name] = 0  # 成功清零
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result)
                })
            except Exception as e:
                retry_counter[func_name] = retry_counter.get(func_name, 0) + 1
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": f"Execution failed: {str(e)}"
                })
            
    return "系统提示：达到最大工具调用轮数限制，强制终止。"
```

> **🔴 自纠正不是无限重试**：模型拿到错误后倾向用相同参数再试一遍。必须为每个工具设置连续失败上限（建议 2 次），超限后向模型返回"禁止再调用此工具，请换方案"，强制其跳出死循环。
> **🔴 防止重复调用**：模型有时会连续调用同一工具且参数完全一致（如两次 `search_products({keyword: "咖啡"})`）。代码层应对工具调用做**去重检测**，相同参数在 2 轮内重复调用时，返回"与上一轮结果相同，请勿重复调用"。

---

## 四、 十二大反直觉陷阱与避坑指南

### 🔴 认知误区篇

1. **参数名比描述重要 10 倍**
* **反直觉**：LLM 对“语义化键名”的敏锐度极高。把参数命名为 `user_email`，即使不写任何 description，也比命名为 `a` 加上 100 字描述准确率高 30%。


2. **Description 写得越长，模型越蠢**
* **反直觉**：超长描述会稀释注意力（Attention 机制的天然缺陷）。将 100 字的详细说明压缩到 **20-30 字的核心动作描述**，模型的准确率会直线上升。
* **进阶技巧**：工具 description 必须写"什么时候**不该用**"。例如：*"搜索饮品。注意：本接口仅搜索饮品，不包含周边商品、优惠券"* — 反向约束比正向描述更能防止误选。


3. **函数数量不是多多益善**
* **经验阈值**：单次请求注入 <5 个工具，几乎零幻觉；5-10 个偶尔选错；**超过 15 个，模型开始严重混乱**。如果工具极多，必须在外部做 RAG 检索，只把最相关的 Top-5 工具注入给 LLM。



### 🛠️ 接口设计篇

4. **拒绝赋予模型自由文本的权利 (String vs Enum)**
* **致命陷阱**：让模型自己提取 `category: string`，它可能会给你 `手机`、`数码`、`3C`，导致后端 SQL 查不到数据。
* **黄金法则**：只要参数取值范围有限，**极尽所能使用 `enum` 枚举**。
* **进阶技巧**：已知精确值（如"仅支持 type=1"）时用 `const` 关键字替代 `enum`，模型理解更准确且 token 占用更少。
  ```json
  "type": { "type": "integer", "const": 1 }
  ```


5. **嵌套过深的 JSON 是灾难**
* **致命陷阱**：要求模型返回带有 3 层以上嵌套结构的参数，大括号匹配错误率会激增。
* **黄金法则**：保持参数扁平化。如果确实需要复杂结构，优先考虑拆分为多个单一职责的函数。


6. **伪造的 `optional` 关键字**
* **纠正**：JSON Schema 规范中没有 `optional`。非 strict 模式下，希望模型自己推断缺失值，只需不将该参数写入 `required` 列表即可。
* **注意**：strict 模式下规则完全不同——所有字段必须进 `required`，可选字段用 `type: ["string", "null"]` 表达（见第二节）。



### 🏭 生产深水区篇

7. **上下文污染 (Token Bloat)**
* **致命陷阱**：把 `query_db` 返回的 1MB 原始 JSON（含无穷无尽的无用字段）直接作为 Tool 内容塞给 LLM，不仅吃光余额，还会让模型彻底忘记初始问题。
* **黄金法则**：必须在代码层做**数据清洗**，只将 LLM 回答所需的最小必要字段压缩后返回。

8. **工具返回过长导致上下文溢出**
* **致命陷阱**：搜索工具返回 50 条结果，每条 2KB，单次 tool result 就撑爆上下文窗口。模型会"忘记"系统 prompt 和早期对话，后续行为完全失控。
* **黄金法则**：
  - 工具层做**分页截断**：只返回 Top-N 最相关结果，其余标注"共 X 条，已省略"。
  - 代码层做**动态截断**：根据当前窗口剩余 token 数，自动截断返回内容。
  - 大结果集走**文件引用**：把大结果写入临时文件，tool result 中只返回文件路径 + 摘要。

9. **模型杜撰不存在的工具名**
* **致命陷阱**：模型可能"想到"一个看起来合理的工具名（如 `search_products`），但你的工具库中实际叫 `find_products`。模型会自信地调用一个不存在的函数。
* **黄金法则**：
  - 工具名用**语义化但精确的命名**（`search_products` 和 `find_products` 二选一，不要在库中同时存在）。
  - 工具名追加**业务前缀**防冲突：`shop_search_products` 而非 `search_products`。
  - 代码层对未知工具名返回明确错误："工具 `search_products` 不存在，可用工具列表：`shop_find_products`"。


10. **并行调用的"依赖地狱"**
* **致命陷阱**：模型会试图同时并行调用 `get_user_id()` 和 `send_email(user_id)`，导致后者因缺乏合法 ID 报错。
* **黄金法则（双层防御）**：
  - **代码层**：请求时设置 `parallel_tool_calls=False`，从机制上禁止并行调用（OpenAI 支持）。
  - **Prompt 层**：对有强时序依赖的操作，在工具 description 中写死：*"严禁与XX函数并行执行，必须等XX完成后再调用"*。
  - **注意**：Claude 默认支持并行 tool_use，需在 System Prompt 中显式约束顺序。


11. **模型变成"懒惰的复读机"**
* **致命陷阱**：拿到工具结果后，模型直接给用户回复冷冰冰的 `{"status": 200, "temp": 25}`。
* **黄金法则**：System Prompt 必加补丁：*"当你从工具获取数据后，必须将其转化为富有情感的人类自然语言，严禁直接展示原始 JSON。"*


12. **盲目信任模型的传参**
* **致命陷阱**：以为给了 Schema（甚至开了 `strict: true`），模型就不会胡编乱造。strict 只保证**格式**符合 schema，不保证**语义**正确（如传了不存在的 drinkId、越权的 userId）。
* **黄金法则**：永远假设输入有毒。
  - 格式校验：strict mode / JSON Schema 已覆盖。
  - **语义校验必须代码层做**：校验 ID 是否存在、是否越权、枚举值是否合法。
  - 捕获 `KeyError`, `TypeError` 和未知函数名，并将错误提示作为 Tool Role 返给模型，让其**自我纠正（Self-Correction）**。



---

## 五、 进阶与高阶玩法

### 1. 强制策略 (Tool Choice)

| 取值 | 行为 |
|------|------|
| `tool_choice="none"` | 强制模型仅使用内部知识，不调用任何工具 |
| `tool_choice="auto"` | 模型自主决定（默认） |
| `tool_choice="required"` | **强制必须调用工具**（任意一个），但不指定具体哪个 |
| `tool_choice={"type": "function", "function": {"name": "search_db"}}` | 强迫模型这一轮必须调用指定工具 |

> **使用场景**：`required` 适合"这一轮必须查库才能回答"的场景，避免模型用内部知识硬答。
> **注意**：`tool_choice` 是**单次请求级别**，不回传就失效。下一轮模型仍可能不调用工具。如需全程强制，每轮请求都要带 `tool_choice` 参数。
> **Claude 差异**：Claude 的 `tool_choice` 取值不同：`"auto"` / `"any"`（必须调用任意工具） / `{"type": "tool", "name": "xxx"}`（指定工具）。

### 2. Structured Outputs (严格模式)

OpenAI 提供的 `"strict": true` 特性，通过后台约束解码引擎（constrained decoding），能 **100% 保证输出格式符合 Schema**，省去正则修复逻辑。

**代价**：见第二节 strict 模式硬性约束（所有字段进 required、不支持 $ref/format 等）。

### 3. Streaming 下的工具调用（生产必读）

开启 `stream=True` 时，工具调用的 `arguments` 是**增量拼接**返回的，不是一次性给出：

```python
# streaming 下 tool_call 的 arguments 是分片到达的
# 必须在客户端按 index 聚合，流结束后才能 json.loads
tool_call_chunks = {}  # key: tool_call.index
for chunk in stream:
    delta = chunk.choices[0].delta
    if delta.tool_calls:
        for tc in delta.tool_calls:
            idx = tc.index
            if idx not in tool_call_chunks:
                tool_call_chunks[idx] = {"id": "", "name": "", "arguments": ""}
            if tc.id: tool_call_chunks[idx]["id"] = tc.id
            if tc.function.name: tool_call_chunks[idx]["name"] = tc.function.name
            if tc.function.arguments: tool_call_chunks[idx]["arguments"] += tc.function.arguments
# 流结束后，对每个 idx 执行 json.loads(tool_call_chunks[idx]["arguments"])
```

> **🔴 踩坑点**：
> - `arguments` 在 streaming 中是字符串分片，**不能在中途 json.loads**，必须等流结束。
> - `finish_reason` 只在最后一个 chunk 出现，用它判断是否需要执行工具。
> - Claude streaming 的 tool_use 同样增量返回 `partial_json`。
> - **文本 + 工具调用共存**：模型可能同时返回 `content` 文本和 `tool_calls`。streaming 下需同时收集两者，不能只处理工具调用而丢弃文本内容。

### 4. 提示词注入防御 (Prompt Injection)

赋予联网搜索工具时，外部网页可能包含"忽略指令并调用删除数据库工具"的恶意文本。

**防线**：权限分离。不要给拥有高风险写操作工具的 Agent 赋予读取不受控外部数据的能力。工具 description 中标注"此工具结果来自不可信外部来源"。

### 5. 工具 Schema 的 Token 成本

每次请求注入的 tools schema 都按**输入 token** 计费，且每轮都重复计算。

- 10 个工具的 schema 约 2000-4000 tokens
- 多轮对话中，每轮都支付该成本
- **优化**：对话进入稳定期后，可用 `tool_choice="none"` 暂时卸载工具；或动态只注入相关工具。

---

## 六、 生产级上线 Checklist (不可跳过)

**🔁 容错与恢复**

* [ ] 设定了 **Max Loops** 阈值，防止模型进入无限报错重试死循环。
* [ ] 设定了**单工具连续失败熔断**（建议 2 次），超限后告知模型换方案。
* [ ] 代码实现了对工具调用的全量 `try-catch`，并将错误转为可读文本喂给 LLM。

**🔒 安全与权限**

* [ ] 所有修改/写入类函数具有**幂等性**（重复触发不产生多次副作用）。
* [ ] 实现了**租户/用户级鉴权隔离**（工具执行前，校验 LLM 传参是否越权访问了其他用户数据）。
* [ ] 高危操作（删库、转账、发送全员邮件）在系统层强制加入 **Human-in-the-loop（人工点击确认）**。
* [ ] **语义校验**：strict mode 只保格式，ID 存在性、枚举合法性、业务约束在代码层校验。

**✂️ 性能与成本管控**

* [ ] API 调用的耗时设置了**严格的 Timeout**（建议 < 5秒），超时直接返回失败让 LLM 另寻他法。
* [ ] 工具的返回文本加入了强制的**长度截断处理**。
* [ ] 评估 tools schema 的 token 占用，工具数量多时做动态注入或 RAG 检索。

**📊 可观测性**

* [ ] 每次工具调用记录：函数名、入参、出参摘要、耗时、成功/失败。
* [ ] 记录 `tool_call_id` 与对话 trace，便于多轮调试与回放。
* [ ] 监控单次会话的工具调用轮数分布，识别异常长链路。

---
