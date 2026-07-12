# Every Agentic Engineering Hack I Know - TLDR

## 核心思想

Matt Van Horn 分享了 16 个 Agentic Engineering 工作流技巧，核心是：**用 plan.md + voice 替代传统 IDE，让智能体做执行，人类做决策和方向指导。**

---

## 16 个技巧速览

| # | 技巧 | 核心要点 |
|---|------|----------|
| 1 | CE plan.md | 任何想法先 `/ce-plan`，让智能体并行研究并生成结构化计划 |
| 2 | 不读 plan.md | 计划是给智能体的，人类只看标题，用 `/ce-work` 执行 |
| 3 | 计划的计划 | 非代码工作也用 `/ce-plan make a plan for the plan`，防止智能体偷懒 |
| 4 | 语音输入 | Mac 用 Monologue/Wispr Flow，手机用 Apple 听写 |
| 5 | cmux 多标签 | 4-6 个会话并行：写计划、构建、研究、修复 Bug |
| 6 | 终端默认 Claude | 新标签直接打开 Claude Code，减少启动摩擦 |
| 7 | 远程控制 + 邮箱 | 手机远程控制会话，邮件触发会话自动工作 |
| 8 | 跳过权限确认 | YOLO 模式：`skipDangerousModePermissionPrompt: true` |
| 9 | Claude 计划 + Codex 构建 | 双引擎协作，Claude 规划，Codex 并行构建 |
| 10 | last30days 研究 | 规划前先用 last30days 获取最新社区知识 |
| 11 | Granola 原始记录 | 会议记录不总结直接丢给智能体提取 |
| 12 | 人类信号 | 人类做判断和方向，智能体做执行 |
| 13 | HyperFrames 视频 | 用 HTML 构建视频，智能体渲染成 MP4 |
| 14 | 笔记作为知识库 | Bear/Obsidian + gbrain/supermemory，让知识复合增长 |
| 15 | 随时随地工作 | Mosh + Tmux + Agent Cookie |
| 16 | Proof 分享计划 | 给非技术同事分享 plan.md 的工具 |

---

## 关键工具栈

- **核心引擎**: Claude Code + Codex（双引擎）
- **规划**: Compound Engineering (`/ce-plan`, `/ce-work`)
- **研究**: last30days
- **语音**: Monologue / Wispr Flow
- **终端**: cmux / Ghostty
- **记忆**: Granola + Bear + gbrain
- **远程**: AgentMail + Mosh + Tmux
- **协作**: Proof

---

## YOLO TL;DR

> 把整篇文章粘贴给智能体，让它制定计划来设置所有东西，然后一次一个技巧地执行。

---

## 原始来源

https://x.com/mvanhorn/status/2061877533885473181
