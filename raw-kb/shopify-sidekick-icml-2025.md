# Shopify Sidekick: Building Agentic Systems in Production (ICML 2025)

> Source: ICML 2025 Talk by Andrew, Ben Laverty & Michael (Shopify)
> Sidekick — merchant-facing AI assistant / "e-commerce expert co-founder"

> Link: [ICML 2025 Talk](https://icml.cc/virtual/2025/46781)
---

## 1. Architecture

### Core Design

- **Standard agentic loop**: LLM + tool set → environment interaction
- **No explicit workflows**: model decides how to handle each task
- **Off the rails**: behavior is not rigidly constrained; model recovers from tool errors on its own
- Key enabler: low-level primitive tools (not task-specific functions)

### Initial Core Skills (V1)

| Skill | Description |
|-------|-------------|
| Segmentation | Text-to-SQL for customer lists (marketing campaigns, discount codes) |
| Analytics | Text-to-SQL for sales/business analytics queries |
| Navigation | Route merchants through 1000+ admin pages |
| Form Filling | Create/update any Shopify resource (products, discounts, SEO) |
| Help | RAG over Shopify Help Center |

### Lessons Learned: Tool Explosion

- Adding tools naturally leads to **20-50+ tools** → unclear boundaries
- **"Death by 1000 instructions"**: system prompt becomes impossible to evaluate, conflicting instructions
- Quality degrades as tool count grows

### Solution: Just-in-Time Instructions

Return instructions **alongside the tool result**, not in the system prompt.

| Benefit | Detail |
|---------|--------|
| Lean system prompt | Core behavior (personality, length, i18n) stays in prompt; edge cases move to tool responses |
| Cache-friendly | Tool instructions sit at bottom of conversation history → only rebuild n-1 cache turns |
| Modular / low blast radius | Changing tool instructions only affects that tool, not the entire system |

### Agentic Handoff (Exploring)

- Main agent delegates to specialized sub-agents (each with own system prompt + tools)
- Sub-agent returns conversation to main agent for final response
- **Warning**: latency concerns in chat systems — use for background tasks only

### Architecture Takeaways

1. **Keep it simple for as long as possible** — a simple agentic loop creates huge value
2. **Don't jump to multi-agent** — unlikely you need it for most cases
3. **Quality over quantity** — core set of high-quality low-level primitives beats 50 random tools
4. **Stay modular** — JIT instructions or similar pattern to reduce blast radius

---

## 2. LLM Evaluations

### From Vibe Testing to Systematic Eval

- Naive approach: vibe test → ship → revert on errors (untenable at scale)
- Hard to know if changes improve things; hard to debug system prompt changes

### Eval Architecture

```
User Simulator (LM-based) → Candidate System → LM Judge
```

- **User Simulator**: LM-based merchant simulator replays real conversation intent
- **Candidate System**: new prompt / tool / component (one change at a time)
- **LM Judge**: reads entire conversation, scores on multiple criteria

### Ground Truth Set

- ~1000+ conversations (continuously growing)
- Follows **production distribution**
- **5-7 evaluation criteria** defined by PMs:
  - Goal fulfillment
  - Safety
  - Merchant sentiment
  - Groundedness
  - etc.
- 3-5 human experts (PMs + team) label & score each conversation
- Statistical agreement measured (Kendall's Tau / Cohen's Kappa, target ~0.7)
- **This IS the spec** — not a static golden set

### Replay-Based Simulation

- Collect real production conversations → extract user intent & goals
- LM replays the conversation with the **candidate system** (instead of production)
- **AA tests**: same system on same conversation → verify LM judge matches production scores
- Once validated, use for AB comparisons with confidence

### LM Judge Iteration

- Version 0 → 0.02 correlation; iterate to 0.11 → continues improving
- Judge is **not a gradually trained discriminator** (unlike GANs) — make it as strong as possible from the start
- Continuous flywheel: new edge cases → add to ground truth set → re-prompt engineer judge

### Key Principle

> The more you can evaluate offline, the more experiments, hyperparameters, and prompt versions you can try before online A/B testing.

---

## 3. GRPO / RL Training (Overview)

- Leverage merchant simulator + LM judges for RLHF loops
- Ground truth set evolves with production distribution → judge prompts continuously readjusted
- Apply reinforcement learning to improve both the model and the evaluation process in tandem

---

## Summary

| Area | Key Insight |
|------|-------------|
| Architecture | Low-level tools + JIT instructions > system prompt bloat |
| Tools | Quality over quantity; avoid "death by 1000 instructions" |
| Eval | LM-based user simulator + LM judge > vibe testing |
| Data | Ground truth set = living spec; continuously grow with production edge cases |
| RL | Strong judge from the start; evolve judge with ground truth drift |