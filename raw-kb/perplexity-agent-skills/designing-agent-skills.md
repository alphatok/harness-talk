# Designing, Refining, and Maintaining Agent Skills at Perplexity

**Source**: https://research.perplexity.ai/articles/designing-refining-and-maintaining-agent-skills-at-perplexity  
**Published**: May 1, 2026

---

Perplexity's frontier agent products rest on a foundation of know-how and domain expertise packaged in modular Agent Skills. We maintain a carefully curated library of Skills across our technical environments. These Skills include many of the general-purpose utilities powering Perplexity Computer; vertical-specific capabilities in areas such as finance, law, and health; and a very long tail of modules for addressing user needs. Some Skills are infrequently invoked but critical when invoked. To ensure a consistently excellent user experience, Perplexity's Agents team prioritizes Skill quality just as much as code quality.

The intuitions and best practices required to develop a high-quality Skill differ significantly from those required to build traditional software. The Agents team reviews many pull requests from excellent engineers who develop Skills in the course of their work. The result is almost always numerous comments and suggestions for revision. This is because many useful patterns for writing code become antipatterns in Skill creation.

For example, if you take some of the aphorisms from PEP20 – The Zen of Python, it quickly becomes clear that writing good Python code is unlike writing good Skills. Of the 20 lines of wisdom, at least half are fully wrong or actively misleading when writing Skills. Here are five of them:

| Zen of Python | Zen of Skills |
|---------------|---------------|
| Simple is better than complex | A Skill is a folder, not a file. Complexity is the feature. |
| Explicit is better than implicit | Activation is implicit pattern matching. Progressive disclosure. |
| Sparse is better than dense | Context is expensive. Maximum signal per token. |
| Special cases aren't special enough to break the rules | Gotchas ARE the special cases (they're the highest-value content). |
| If the implementation is easy to explain, it may be a good idea | If it's easy to explain, the model already knows it. Delete it. |

---

## What is a Skill?

When you write a Skill, you aren't writing plain old software (even though Skills are now part of the main logical engines for agent systems). Rather, you're building context for models and their environments. A Skill has different constraints and different design principles. If you write a Skill like you do code, you will fail.

A Skill is at least four things, especially in the context of how we build them at Perplexity.

### A Skill is a Directory

A Skill is not just a single SKILL.md file. In many cases, a Skill includes several files. Under the directory named after your Skill, you might have:

- **SKILL.md**: frontmatter and instructions
- **scripts/**: code the agent runs, not reinvents
- **references/**: heavy docs, loaded conditionally
- **assets/**: templates, schemas, and data
- **config.json**: first-run user setup

This hub-and-spoke pattern allows you to keep Skills very focused and tight, and one can use the folder structure in a very creative way. Sometimes, particularly intricate Skills benefit from multiple levels of hierarchy to help the model navigate better. Suppose a Skill requires knowledge across 300 topics, groupable into 20 subject matter areas. Reliably choosing the right topic among 300 is an unsolved challenge even for today's best frontier models. It's a much easier choice problem for a model to hone in on one of 20 areas, than among the 15 topics within that area.

As one example of how multilevel hierarchy provides value, our team employed three levels of topical nesting within the Skills powering Computer's U.S. income tax capabilities this past tax season. This hierarchy was absolutely indispensable given the complexity of tax law: in our early tests, presenting the model with a single folder containing all 1,945 sections of the U.S. Internal Revenue Code resulted in worse performance than not loading the Skill at all. Organizing the information into logical subdivisions was indispensable for ensuring high-precision read operations.

Yet this hierarchy did not come free. Increasing levels of hierarchy require increasing levels of curation across the information architecture to manage the resulting indirection. We devised quick reference guides, custom search utilities, and other tools to support the model in locating information with a minimum of indirection.

### A Skill is a Format

A Skill is a format. The core root SKILL.md file must have both a name and a description. Furthermore, the Skill needs to exactly map to the directory name in which the Skill is located. The name must be all lower-case characters, have no spaces, and can use hyphens. The description is the routing trigger. This is a common failure point: the description is not internal documentation for what the Skill does. It amounts to instructions for the model for when to load the Skill. So, you will frequently see "Load when," not "This Skill does." This is important because of the way that most implementations inject the description into the model context.

### A Skill is Invocable

A Skill is invocable. The agent loads a Skill at runtime. Importantly, Skills aren't always bundled into the context. By default, most agent systems unfold Skills progressively upon specific need.

The process:
1. Computer calls `load_skill(name="...")`
2. Computer copies the Skill directory into the isolated execution sandbox
3. Computer recursively auto-loads dependencies in the "depends:" tag
4. Computer then strips the frontmatter and the agent thus only sees the body and the additional files

### A Skill is Progressive

Skills are progressive. In Computer, there are three different tiers of context costs:

| Tier | What loads | Budget | When you pay |
|------|------------|--------|--------------|
| **Index** | name + description for every non-hidden Skill | ~100 tokens per Skill | Every session, every user, always paid |
| **Load** | Full SKILL.md body | ~5,000 tokens | When Skill is loaded |
| **Runtime** | Files in scripts/, references/, assets/, subskills, FORMATTING.md, SPECIAL_CASES.md | Unbounded | Only when the agent reads them |

---

## When do you need a Skill?

The Agents team is often asked to opine on whether a Skill is truly needed for a given domain or use case. Very rarely do we have a definitive answer from first principles alone. The only way to really figure this out is to start with your agent without the Skill, run several hero queries, and then figure out whether the agent is doing a good job.

### When you need a Skill

There are many tasks that are in distribution for trained models. You only need to apply a Skill if you want to change that behavior in some specific way that you can't with say, one sentence in your prompt. So, you need a Skill when the agent will get it wrong without special context, or if there's some inconsistency or non-determinism that you need to be extremely consistent across runs.

It could be that your knowledge is durable but not in the training data. There could be cutoffs or enterprise specific workflows, or it could be a matter of taste. For example, we have several design-related Skills in Computer written by Henry Modisett (our head of design). The reason that every token exists in those Skills is because Henry has very good taste when it comes to designing websites and PDFs.

### When you don't need a Skill

We see many Skills in which engineers have written a series of git commands that need to be executed in order. That's unnecessary because the model already knows how to do that, meaning it makes for great documentation but a poor Skill.

We see examples where Skills recapitulate instructions from the system prompt. You don't need a Skill for that. Knowledge relevant for the majority of requests should be included in global context, not in a conditionally loaded Skill.

If there's something that's changing faster than you can maintain it, you don't need a Skill. For example, if you're hitting some remote MCP endpoint and its tools or the versions of those tools are changing frequently, you shouldn't inject those into a Skill.

### Every Skill is a tax

Here's a useful test you can apply to every sentence in your Skill: "Would the agent get this wrong without this instruction?" If the sentence does not need to be there, it cannot afford to be there because everyone is paying this cost every single time.

> "Je n'ai fait celle-ci plus longue que parce que je n'ai pas eu le loisir de la faire plus courte." — Blaise Pascal

Just like Pascal, you need to invest time in every Skill. It is hard to write a short Skill. If your Skill is easy to write, it is probably too long or shouldn't exist. A good Skill is as short as it can be.

---

## How to build a Skill

### Step 0: Write the Evals

Write some of the evals first. You can source evaluation cases from:
- **Real user queries**: sample from production or your brain trust
- **Known failures**: The agent failed because the Skill didn't exist
- **Neighbor confusion**: Close to your domain boundary but routes to another Skill

At the very least, you should be making sure that you're testing that the Skill loads when needed. Start with similar negative and positive examples. Negative examples are extremely powerful and can matter more than positive examples.

### Step 1: The Description

This is the hardest line in the Skill. It's a routing trigger, not documentation. To get the name and the description right, you don't care about the content of the Skill. You only care about whether the Skill is loaded and injected at the right points and is free of off-target side effects, which is the number one failure mode.

A bad description describes what the Skill does or why it is useful. A good description says when the agent should load the Skill. For example, say you have something for monitoring pull requests. Don't write what the Skill does. Write what engineers say when they're frustrated and they want you to make sure that their PR works, like "babysit" or "watch CI" or "make sure this lands."

**Checklist**:
- Starts with "Load when..."
- Target 50 words or fewer
- Describes the user's intent, ideally from real queries
- Does not summarize the workflow

### Step 2: Write the Body

Next, write the content of the Skill itself. Communicating workflows to an LLM is completely different to communicating workflows to a colleague. When learning a new software tool, an engineer might need to read the documentation, get a walkthrough from someone with experience, and learn how to use the tool. Meanwhile, for almost any software tool that has been around at least a year, you just need to mention its name and the LLM has all the information it needs.

When you are writing the body, **skip the obvious things**. Don't write out a series of commands.

For example, you don't need to write:
```
git log # find the commit
git checkout main
git checkout -b <clean-branch>
git cherry-pick <commit>
```

Instead, write:
> "Cherry-pick the commit onto a clean branch. Resolve conflicts preserving intent. If it can't land cleanly, explain why."

The model will do a much better job with the latter. Don't railroad, or be overly prescriptive. Instead, be flexible where multiple approaches can work.

Next, focus on the **gotchas or negative examples**. These are extremely high-signal content. If you add a line every time the agent trips up, you'll learn by running it and the gotchas will grow organically.

Lastly, if there's any portion that's conditional or extremely heavy in content, take it out of the SKILL.md and put it into one of the spokes (scripts/, references/, assets/).

### Step 3: Use the Hierarchy

| Directory | Purpose | Principle |
|-----------|---------|-----------|
| `scripts/` | Deterministic logic the agent would reinvent every run | Give it code to compose, not reconstruct |
| `references/` | Heavy docs loaded only when a condition is met | "Read api-errors.md if API returns non-200" |
| `assets/` | Output templates the agent copies and fills | report-template.md, output schemas |
| `config.json` | First-run user setup | Ask for the Slack channel, save, and reuse next time |

### Step 4: Iterate

Next, do a bunch of iterations on a branch. Start on the main branch with no Skill, do some iterations, build your hero query set, and run a slew of evals. Anyone reviewing your Skill code will thank you for submitting a single changeset complete with an evaluation set.

### Step 5: Ship

Ship it.

---

## How to Maintain a Skill

### The Gotchas Flywheel

From this point on, your list of gotchas tends to grow or change a lot. We often see engineers who make PRs that are un-evaled, for example, change the description. If you're changing the description after your Skill has been merged, you are off track. If you're making changes to the thing that decides whether to route your Skill, you need to write some evals that support the changes.

Skills are append-mostly. The gotchas section accrues the most value over time:

| Trigger | Action |
|---------|--------|
| Agent fails at something | Add a gotcha |
| Agent loads the Skill off target | Tighten description and add negative evals |
| Agent doesn't load the Skill when it should | Add keywords and positive evals |
| System prompt changes | Check for contention or duplication |

### Eval Suites

At Perplexity, we run many eval suites to check for different things:
- **Skill loading and file reads**: precision, recall, and forbidden checks
- **Progressive loading evals**: does agent read accessory files?
- **End-to-end task completion**: LLM judge grading based on rubric
- **Cross-model validation**: GPT, Claude Opus, Claude Sonnet behave differently

---

## Final thoughts and takeaways

The more Skills you build, the better you will get at building them. If you're not automating tasks using Skills, start immediately.

Key takeaways:
- Write evals before the Skill. Include negative examples and forbidden loads.
- The description is the hard part. "Load when..." (every word costs attention).
- Gotchas are extremely high-value content. Start thin, grow as the agent fails.
- Remember that it is easy to break other pre-existing Skills by adding a new Skill (beware of action at a distance).
- Use all the available tools every time you're writing and maintaining a Skill.