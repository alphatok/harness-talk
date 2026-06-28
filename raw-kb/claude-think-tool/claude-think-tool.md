# The "think" tool: Enabling Claude to stop and think in complex tool use situations

**Source**: https://www.anthropic.com/engineering/claude-think-tool  
**Published**: Mar 20, 2025  
**Updated**: Dec 15, 2025 (Extended thinking update)

---

> **Extended Thinking Update (Dec 15, 2025)**: Extended thinking capabilities have improved since its initial release, such that we recommend using that feature instead of a dedicated think tool in most cases. Extended thinking provides similar benefits—giving Claude space to reason through complex problems—with better integration and performance. See our extended thinking documentation for implementation details.

---

As we continue to enhance Claude's complex problem-solving abilities, we've discovered a particularly effective approach: a **"think" tool** that creates dedicated space for structured thinking during complex tasks.

This simple yet powerful technique—which is different from Claude's new "extended thinking" capability—has resulted in remarkable improvements in Claude's agentic tool use ability. This includes following policies, making consistent decisions, and handling multi-step problems, all with minimal implementation overhead.

---

## What is the "think" tool?

With the "think" tool, we're giving Claude the ability to include an additional thinking step—complete with its own designated space—as part of getting to its final answer.

### Difference from Extended Thinking

| Feature | Extended Thinking | "think" Tool |
|---------|-------------------|--------------|
| **When** | Before generating response | During response generation |
| **Purpose** | Deeply consider and iterate on plan before action | Stop and think about whether it has all information needed to move forward |
| **Use case** | All information from user query alone | Need to process external information (tool call results) |
| **Depth** | Comprehensive reasoning | Focused on new information discovered |

### When to Use Each

| Scenario | Recommended |
|----------|-------------|
| Non-sequential tool calls | Extended thinking |
| Straightforward instruction following | Extended thinking |
| Coding, math, physics (no tools) | Extended thinking |
| **Complex tool calls** | "think" tool |
| **Long chains of tool calls** | "think" tool |
| **Policy-heavy environments** | "think" tool |
| **Sequential decisions where mistakes are costly** | "think" tool |

---

## Tool Definition

Here's a sample implementation using the standard tool specification format from τ-Bench:

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

---

## Performance on τ-Bench

![Airline Domain Performance](tau_bench_airline.jpg)

τ-bench (tau-bench) is a comprehensive benchmark designed to test a model's ability to use tools in realistic customer service scenarios.

**Evaluation metric**: `pass^k` measures the probability that all k independent task trials are successful. Unlike `pass@k` (at least one succeeds), `pass^k` evaluates **consistency and reliability**—critical for customer service where consistent policy adherence is essential.

### Configurations Tested

1. Baseline (no "think" tool, no extended thinking)
2. Extended thinking mode alone
3. "Think" tool alone
4. "Think" tool with optimized prompt

### Results - Airline Domain

| Configuration | k=1 | k=2 | k=3 | k=4 | k=5 |
|---------------|-----|-----|-----|-----|-----|
| **"Think" + Prompt** | 0.584 | 0.444 | 0.384 | 0.356 | 0.340 |
| "Think" | 0.404 | 0.254 | 0.186 | 0.140 | 0.100 |
| Extended thinking | 0.412 | 0.290 | 0.232 | 0.192 | 0.160 |
| Baseline | 0.332 | 0.206 | 0.148 | 0.116 | 0.100 |

**Key findings**:
- "Think" + optimized prompt: **54% relative improvement** over baseline (0.570 vs 0.370 on pass^1)
- Extended thinking showed similar performance to unprompted "think" tool

![Retail Domain Performance](tau_bench_retail.jpg)

### Results - Retail Domain

| Configuration | k=1 | k=2 | k=3 | k=4 | k=5 |
|---------------|-----|-----|-----|-----|-----|
| **"Think" + no prompt** | 0.812 | 0.735 | 0.685 | 0.650 | 0.626 |
| Extended thinking | 0.770 | 0.681 | 0.623 | 0.581 | 0.548 |
| Baseline | 0.783 | 0.695 | 0.643 | 0.607 | 0.583 |

**Key findings**:
- Retail policy is easier → "Think" tool alone achieved highest pass^1 (0.812)
- No additional prompting needed for simpler domains

---

## Optimized Prompt Example

The best performance in the airline domain was achieved by pairing the "think" tool with an optimized prompt:

```
## Using the think tool

Before taking any action or responding to the user after receiving tool results, use the think tool as a scratchpad to:
- List the specific rules that apply to the current request
- Check if all required information is collected
- Verify that the planned action complies with all policies
- Iterate over tool results for correctness 

Here are some examples of what to iterate over inside the think tool:
<think_tool_example_1>
User wants to cancel flight ABC123
- Need to verify: user ID, reservation ID, reason
- Check cancellation rules:
  * Is it within 24h of booking?
  * If not, check ticket class and insurance
- Verify no segments flown or are in the past
- Plan: collect missing info, verify rules, get confirmation
</think_tool_example_1>

<think_tool_example_2>
User wants to book 3 tickets to NYC with 2 checked bags each
- Need user ID to check:
  * Membership tier for baggage allowance
  * Which payments methods exist in profile
- Baggage calculation:
  * Economy class × 3 passengers
  * If regular member: 1 free bag each → 3 extra bags = $150
  * If silver member: 2 free bags each → 0 extra bags = $0
  * If gold member: 3 free bags each → 0 extra bags = $0
- Payment rules to verify:
  * Max 1 travel certificate, 1 credit card, 3 gift cards
  * All payment methods must be in profile
  * Travel certificate remainder goes to waste
- Plan:
1. Get user ID
2. Verify membership level for bag fees
3. Check which payment methods in profile and if their combination is allowed
4. Calculate total: ticket price + any bag fees
5. Get explicit confirmation for booking
</think_tool_example_2>
```

---

## Performance on SWE-Bench

A similar "think" tool was added to our SWE-bench setup when evaluating Claude 3.7 Sonnet, contributing to the state-of-the-art score of **0.623**.

**Adapted tool definition**:

```json
{
  "name": "think",
  "description": "Use the tool to think about something. It will not obtain new information or make any changes to the repository, but just log the thought. Use it when complex reasoning or brainstorming is needed. For example, if you explore the repo and discover the source of a bug, call this tool to brainstorm several unique ways of fixing the bug, and assess which change(s) are likely to be simplest and most effective. Alternatively, if you receive some test results, call this tool to brainstorm ways to fix the failing tests.",
  "input_schema": {
    "type": "object",
    "properties": {
      "thought": {
        "type": "string",
        "description": "Your thoughts."
      }
    },
    "required": ["thought"]
  }
}
```

**Results**: n=30 samples with "think" tool vs n=144 samples without → **+1.6% improvement** (Welch's t-test: t(38.89) = 6.71, p < .001, d = 1.47)

---

## When to Use the "think" Tool

| Scenario | Benefit |
|----------|---------|
| **Tool output analysis** | Process previous tool call outputs before acting; may need to backtrack |
| **Policy-heavy environments** | Follow detailed guidelines and verify compliance |
| **Sequential decision making** | Each action builds on previous ones; mistakes are costly |

---

## Implementation Best Practices

### 1. Strategic prompting with domain-specific examples

Provide clear instructions on when and how to use the "think" tool:
- Level of detail expected in reasoning
- How to break down complex instructions into actionable steps
- Decision trees for handling common scenarios
- How to check if all necessary information has been collected

### 2. Place complex guidance in the system prompt

When instructions are long/complex, include them in the **system prompt** rather than tool description. This provides broader context and helps the model better integrate the thinking process.

---

## When NOT to Use the "think" Tool

| Scenario | Reason |
|----------|--------|
| Non-sequential tool calls | Single or parallel calls don't benefit from "think" |
| Simple instruction following | Default behavior is good enough |
| Cost consideration | Increases prompt length and output tokens |

---

## Getting Started

1. **Test with agentic tool use scenarios** — Start with challenging use cases where Claude struggles with policy compliance or complex reasoning
2. **Add the tool definition** — Customize to your domain; consider including instructions with examples in system prompt
3. **Monitor and refine** — Watch how Claude uses the tool; adjust prompts to encourage effective thinking patterns

**Minimal downside**: Doesn't change external behavior unless Claude decides to use it; doesn't interfere with existing tools or workflows.

---

## Key Insights

| Insight | Detail |
|---------|--------|
| **Prompting matters on difficult domains** | "Think" alone improves somewhat; + optimized prompt = dramatically better |
| **Easier domains need less prompting** | Retail: "Think" alone achieved best results |
| **Improved consistency** | Improvements maintained for pass^k up to k=5 |
| **Generalizes across models** | Claude 3.5 Sonnet (New) also achieves gains with same configuration |