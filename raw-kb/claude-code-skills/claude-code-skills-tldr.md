# TLDR: Lessons from building Claude Code — How we use skills

## Core Takeaway
Skills are **folders** (not just markdown) containing instructions, scripts, and resources. Pattern: 9 skill categories; best skills fit cleanly into one.

## 9 Skill Categories

| # | Category | What it does | Example |
|---|----------|-------------|---------|
| 1 | **Library/API Reference** | How to use libs, CLIs, SDKs with gotchas | `billing-lib` |
| 2 | **Product Verification** | Test/verify code (playwright, tmux) — highest impact on quality | `signup-flow-driver` |
| 3 | **Data Fetching & Analysis** | Connect to data/monitoring stacks | `funnel-query`, `grafana` |
| 4 | **Business Process Automation** | Automate repetitive workflows | `standup-post` |
| 5 | **Code Scaffolding & Templates** | Generate boilerplates with NL requirements | `new-migration` |
| 6 | **Code Quality & Review** | Enforce style, adversarial review | `adversarial-review` |
| 7 | **CI/CD & Deployment** | Fetch, push, deploy code | `babysit-pr`, `deploy-<svc>` |
| 8 | **Runbooks** | Symptom→investigation→structured report | `oncall-runner` |
| 9 | **Infrastructure Operations** | Maintenance with guardrails | `<res>-orphans` |

## Best Practices (TLDR)

1. **Don't state the obvious** — Claude already knows basic coding
2. **Build Gotchas section** — highest-signal content; update over time
3. **Progressive disclosure** — SKILL.md → references/ → assets/ (folder hierarchy)
4. **Avoid railroading** — give info, keep flexibility
5. **Config in config.json** — setup through user questions via AskUserQuestion
6. **Descriptions for the model** — not summaries, but *when to trigger*; include trigger words
7. **Use log files for memory** — e.g. `standups.log` for delta detection
8. **Give scripts not boilerplate** — Claude composes; scripts handle the rest
9. **On-demand hooks** — `/careful` (block dangerous ops) / `/freeze` (restrict directory)

## Distribution
- Small teams: check into `./.claude/skills` in repo
- Large orgs: internal plugin marketplace, organic adoption (sandbox → PR)
- Composition: reference other skills by name
- Measurement: PreToolUse hook to log usage & find undertriggering skills