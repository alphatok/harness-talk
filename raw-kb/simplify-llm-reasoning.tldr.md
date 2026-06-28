# TLDR — Simplify LLM Reasoning

> 原文：[Clarity Beats "Thinking Harder": Simplify LLM Reasoning](https://codewithcaptain.com/simplify-llm-reasoning/)

---

## 核心论点

**清晰度胜过复杂性。** 在 prompt 中堆砌"逐步推理""自我反思"等步骤，反而让模型准确率下降。Anthropic 的研究也证实了这一点：增加反思步骤 ≠ 更好的输出。

---

## LLM 的本质

LLM 不是推理引擎，而是**模式重混器**（next-word prediction）。给它模糊的 prompt，它重混出模糊的结果。给它清晰的 prompt，它给出清晰的输出。

---

## 三大实践原则

| 原则 | 要点 |
|------|------|
| **意图明确** | 像写合同一样写 prompt：目标、边界、约束、成功标准 |
| **步骤精简** | 只保留任务真正需要的推理步骤，把关每个步骤 |
| **外部校验** | 用检索、工具调用、人工反馈来锚定输出，别让模型自己"反思" |

---

## 常见陷阱

| 陷阱 | 说明 |
|------|------|
| prompt 臃肿 | 堆砌越多上下文，模型越容易走偏 |
| 中间信息丢失 | prompt 中间的内容模型最容易忽略（[Lost in the Middle](https://direct.mit.edu/tacl/article/doi/10.1162/tacl_a_00638/119630/Lost-in-the-Middle-How-Language-Models-Use-Long)） |
| 自我纠错幻觉 | 让模型"与自己争论"只会强化错误，变成回音室 |
| 跨模型不通用 | 同一 prompt 在不同模型上表现可能天差地别 |

---

## 何时增加推理步骤

**需要时**：多约束规划、工具链修补、严格数据模式

**不需要时**：标准摘要、问答、事实检索类任务 → 堆步骤只会固化错误

---

## 验证方法

1. 单次基线 → 2. 叠加步骤门控版 → 3. 加外部校验变体
离线用保留数据评估，再上线。回归测试比头脑风暴更能发现漂移。

---

## 一句话

> **少即是多。** 精简 prompt + 外部锚定 = 可靠输出。从 `auto` 和 2-3 个原则开始，别上来就堆 20 个推理步骤。