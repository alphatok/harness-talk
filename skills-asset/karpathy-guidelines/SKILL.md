---
name: karpathy-guidelines
description: AI改代码越改越多，小需求变成大重构？把需求、报错或待审代码交给助手，按Karpathy四项准则先澄清关键假设、选择简单方案、只改相关代码，再用可观察结果验证。帮助减少过度设计、无关改动和“看着完成却没验证”的返工。适合修Bug、加功能、代码审查与按需重构。安装后直接说：“按Karpathy准则修这个问题，先说明假设、最小改动范围和验证方法。”
license: MIT
metadata:
  version: "1.0.1"
---

# Karpathy 编程准则｜少改代码、做对需求

把需求、报错或待审代码交给助手，按下列四项准则控制改动范围并验证结果。适合修复问题、增加功能、代码审查和按需重构；不会保证自动消除所有缺陷。

用法：“按Karpathy准则修这个问题，先说明关键假设、最小改动范围和验证方法。”已有信息不重复询问；只有关键歧义影响实现时才澄清。简单任务按实际情况处理。

原始四项准则如下，保留来源与MIT许可。

Behavioral guidelines to reduce common LLM coding mistakes, derived from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876) on LLM coding pitfalls.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.
