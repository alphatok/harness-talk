# 理解阶梯：ASD-STE100 与 3B1B —— 同类 Agent Skill 全景

> 缘起：Andrej Karpathy [关于"输出格式阶梯"的帖子](https://x.com/karpathy/status/2105819303471976479)（2026-10）
> 同类项目：GitHub topic 下的 agent skill 生态（调研时间：2026-10，星标数为 GitHub Search 截面值）

---

## 0. TL;DR

**`asd-ste100` 和 `3b1b` 不是同类的两个竞品，而是同一条"理解阶梯"的上下两级。**

它们都属于同一批 **agent skill**（Claude Code / Codex / Cursor / OpenCode 通用）：

| | `asd-ste100` | `3b1b` |
|---|---|---|
| 阶梯档位 | 第 1 档：受控语言文本 | 第 4 档：讲解视频 |
| 输出形态 | 短句、一词一义的英语文本 | Manim 动画 + TTS 旁白视频 |
| 解决的问题 | **歧义**（读者没人可追问） | **随时间展开的过程**（文字讲不清） |
| 成本 | 零依赖，秒级 | ffmpeg + Manim + TTS，数十分钟渲染 |
| 真实定位 | 让下游 agent 一次读对 | 让人类一次看懂 |

两者共同的上游是 Karpathy 的观点：**LLM 产出文本几乎免费，"读懂它"才是瓶颈**——所以要让 agent 换一种更好理解的形式交付，而不是继续堆字。

---

## 1. 背景：Karpathy 的"理解阶梯"

Karpathy 的原话大意：既然生成成本已经趋近于零，就不该继续接受一堵又一堵的文字墙，而应主动要求更容易理解的形式。他排了四档，逐档"更好"：

| 档 | 形式 | 为什么更好 | 解决什么问题 |
|---|---|---|---|
| 1 | **ASD-STE100 受控英语文本** | 一句一个意思，一词一个含义 | 歧义、长句、一词多义 |
| 2 | **图**（Mermaid / ASCII / SVG） | 结构一次性铺开，而不是逐行读 | 线性文本读不出结构关系 |
| 3 | **可交互 HTML 页** | 参数一动，结果立刻变 | "如果改了会怎样"讲不清 |
| 4 | **3Blue1Brown 式讲解视频** | 动画 + 旁白，表达时间维度上的过程 | 推导/过程无法用文字即时呈现 |

**难点不在知道这个阶梯，而在于每次都不用被要求就选对档位，且不爬得比问题需要的高。** 这句话正是下面那一大票"路由器技能"的卖点。

---

## 2. 第 1 档：ASD-STE100 是什么

### 2.1 起源：为"不能被误读"而生

ASD-STE100（Simplified Technical English）是**受控自然语言**与国际标准，由 ASD（Aerospace, Security and Defence Industries Association of Europe，欧洲航空航天与国防工业协会）持有。1980 年代由 AECMA 应欧洲航空业要求开发，用于飞机维修文档。

它存在的理由很硬：**维修手册被误读会死人，而读者常常是非英语母语者，且没有作者可以打电话追问。**

标准含两部分：

- **Part 1 — 写作规则**：语法与文风（主动语态、简单时态、一句一条指令、不省略成分、限制句长）
- **Part 2 — 受控词典**：约 900 个核准词 + 少量技术名词，**一词一义**（one word = one meaning）

### 2.2 为什么搬到 agent 上

这是这批 skill 最关键的洞察。**一个 LLM agent 读另一个 agent 的输出时，处境和读维修手册的技工一模一样：没有 back-channel，不能反问"你说的 X 是哪个意思"。**

于是同一套纪律：工具描述、错误信息、跨 agent 指令、系统提示词，都值得用 STE 写。

| Before（易误读） | After（STE） |
|---|---|
| "This tool will attempt to synchronize state across the various backends that have been configured, and if a conflict is detected it may resolve it automatically depending on the strategy that has been set, or otherwise it will surface the conflict for manual review." | "The tool tries to synchronize state across the configured backends. If it finds a conflict, it reads the configured strategy. If the strategy allows automatic resolution, the tool may resolve the conflict without a user. If the tool does not resolve the conflict, it reports the conflict for manual review." |
| "An error may have occurred while processing your request due to a possible mismatch in the expected data format." | "Your request may have failed. The cause may be a data format that does not match what the server expects." |

### 2.3 "80% STE" 是个高明默认值

多数实现默认只做到 STE 的 **80%**：保留核心纪律（短句、主动语态、不省略、一词一义），但不强求通过完整词典合规检查。原因是完整合规会牺牲可读性和速度，收益递减。这个取舍来自 Karpathy 的建议。

---

## 3. 第 4 档：3B1B 是什么

**3Blue1Brown** 是 Grant Sanderson 的数学可视化频道。它的价值不在"把数学动画化"，而在它的**教学哲学**——这些原则被 skill 化之后才是可复用的：

| 教学原则 | 含义 |
|---|---|
| 直觉先于形式 | 先建立视觉理解，再给公式 |
| 先问为什么，再问是什么 | 先给动机，再给定义 |
| 具体先于抽象 | 从例子出发，再一般化 |
| Show, don't tell | 让画面自己解释 |

技术栈是 **Manim**（Sanderson 自研的数学动画引擎）。这里有个容易踩的坑——**Manim 有两个不兼容的分支**：

- **Manim Community Edition（Manim CE）**：社区维护，生态与文档主流 → 绝大多数 skill 用它
- **ManimGL**：Sanderson 本人那套，特性更前沿但不通用 → 少数 skill 明确只支持它

另有不走 Manim 的路线（如 Remotion / React），用音频驱动架构做视频，适合已有前端能力栈的团队。

---

## 4. 同类清单（按档位分组）

### 4.1 第 1 档：STE 写作类（赛道最卷，几十个仓库）

| 技能 | ★ | 区别点 |
|---|---|---|
| `danyuchn/asd-ste100-skill` | 5.1k | **标杆**。明确面向 agent-to-agent：工具描述、报错、跨 agent 指令；纯写作规则，零依赖 |
| `AminBlg/SimpleEnglish` | 3.9k | 偏"让 LLM 写文档"，不是改写存量文本 |
| `0xpili/simplified-technical-english` | 1k | 带**核准词表 + check 工具**，可判定，不靠模型自觉 |
| `dualface/ste-zh` | 316 | **中文汇报版**（简体），把 STE 原则映射到中文，不是翻译 STE |
| `dualface/ste-zht` | 17 | 同上，繁体 |
| `jsath/simplified-technical-english` | 86 | 卖点是 "kill AI slop"，反模型腔 |
| `lemonhall/asd-ste100-skill-zh` | 54 | 受控中文 + stdlib-only 确定性 linter |
| `mzopedia/simplified-technical-chinese` | 32 | 40 条规则 + 一词一义词表 + 零依赖 checker |
| `TheAngryByrd/simplified-technical-english-skill` | 33 | 目标单一：减少输出冗余 |
| `tornikegomareli/agent-rules` | 12 | 一套规则通吃所有 coding agent，并禁掉 hype 形容词 |
| `JuanMarchetto/doc-standards-skill` | 19 | 五层标准叠加：STE + Google/Microsoft style + ISO 24495 + AI 可读性 |
| `abryfs/agent-ste` | 5 | 唯一强调**跨 12 个模型跑 benchmark**（宣称违规率降 95.5%） |
| `Syntaf/vale-llm-slop` | 27 | 不是 skill，是 **Vale 风格 linter**，进 CI 守门 |
| `jyooi/agent-simple-english` | 11 | TypeScript + Effect 实现的确定性 linter |
| `NikolaRHristov/STE-Code` | 17 | 9-agent 流水线 + 59 条测试基准（96.6%） |
| `jlelia/CompleXEnglish` | 1 | 反派彩蛋：故意写成"看不懂的受控英语"（讽刺作品） |

### 4.2 第 4 档：3B1B / Manim 视频类

关键分岔是**引擎**（Manim CE / ManimGL / Remotion）与**是否覆盖全流程**（分镜？旁白？合成？）：

| 技能 | ★ | 区别点 |
|---|---|---|
| `Yusuke710/manim-skill` | 174 | 最主流，纯 Manim 动画产出，不含 TTS |
| `subinium/3b1b-style-animation-skill` | 7 | 只沉淀**教学哲学**（不绑定具体工作流） |
| `devamsheth21/3b1b-video-skill` | — | 端到端：Manim CE + TTS 旁白，且**与 agent 无关**（任何编码 agent 可用） |
| `do-gongil/manimgl-skill` | — | 用 **ManimGL**（3b1b 本人那套）而非社区版 |
| `24kchengYe/note2video-skill` | 1 | 窄场景：算法可视化 / 题解讲解 |
| `KhalilOthmanEng/3b1b-scientific-explanation` | — | 输入是**论文**，输出结构化教学视频 |
| `Rica320/3b1b-Skill`、`sushanthj/3B1B_animation_skills` | — | 更早的复刻，功能重叠 |
| `youxiangdev/turn-anything-into-3b1b` | — | 输入是论文/链接/仓库/主题，通吃 |
| `RealHacker/3b1b-explainer-kit` | 1 | 重点在**旁白脚本**，画面是附带 |
| `Brmbobo/remotion-video-skill` | 2 | 换引擎：**Remotion**（React），音频驱动架构 |

### 4.3 四档全包（"该用哪一档"的路由器）—— 真正该选的一层

| 技能 | ★ | 区别点 |
|---|---|---|
| `ChangWenC/understanding-ladder` | 108 | **最完整**。自动选"最低够用的档"，且强调 **Nothing cut**（不删内容，只换形式）；中英双语；有 live demo |
| `Yaxin9Luo/explainer-skill` | — | 会**自检输出**：重算每个数字、核对图表、卡住时先定位卡点 |
| `Alon-W/explain-skill` | — | 最轻量，单文件 SKILL.md，一条 curl 装完 |
| `ashryaagr/karpathy-output-style` | 32 | 拆成 4 个独立 skill（clear-writing / diagram / webpage / video），走 Codex plugin marketplace |
| `Sumit189/explain-claude-mod` | 21 | 做成 `/explain` 命令，四档可选 |
| `FutureAtoms/karpathy-ladder` | 9 | 含"工程图纸规格表"这一额外形态 |
| `prithivrajmu/asd-ste100` | 13 | 默认 "80% STE 模式" |

### 4.4 相邻但不同类（容易混进来）

| 类型 | 代表 | 与 STE 的区别 |
|---|---|---|
| 去 AI 味 | `humanizer`、`human-writing` | STE 管"不产生歧义"，humanizer 管"不像模型写的"，方向相反 |
| 省 token | `caveman` | 压的是**长度**，STE 压的是**歧义** |
| 第 2 档图表 | `excalidraw-diagram`、`karpathy-output-style/explain-diagram` | 输出图，不是文本 |
| 第 3 档交互页 | `canvas-design`、`explain-webpage`、`artifacts-builder` | 输出可交互页面 |
| 本地化变体 | `german-technical-writing-skill`、`portugues-tecnico-controlado`、`asd-ste100-ru-skill`（俄，对标 GOST Р 58049） | 把 STE 原则移植到其他语言 |

---

## 5. 关键区别：四个真实分岔点

1. **要"写"还是要"选"**
   需求单一 → 直接装单档技能（`manim-skill` 或 `danyuchn/asd-ste100-skill`）。
   不确定输出形态 → 装路由器（`understanding-ladder`）。否则你会把它当两件事分别维护。

2. **要不要确定性守门**
   只有"自觉遵守的规则"必然漂移。要稳定 → 选带 linter 的（`0xpili`、`lemonhall`、`vale-llm-slop`、`agent-simple-english`）。
   这类工具是 **skill（软约束）** 与 **linter（硬约束）** 的分水岭。

3. **中文场景**
   直接套英文 STE 会得到翻译腔。对外**汇报**用 `dualface/ste-zh`；产出**中文文档**用 `mzopedia` 或 `lemonhall` 的受控中文。

4. **成本梯度**
   STE 零依赖、秒级；视频档要 ffmpeg + Manim + TTS（ElevenLabs 或本地 Piper/Kokoro/espeak-ng），几分钟视频 = 数十分钟渲染。
   **别爬得比问题需要的高**——这是 Karpathy 那条帖子的核心精神，也是 `understanding-ladder` 的第一卖点。

---

## 6. 场景决策表

| 你的场景 | 选哪档 | 具体推荐 |
|---|---|---|
| agent 工具描述、报错信息、跨 agent 指令 | 1 | `danyuchn/asd-ste100-skill` |
| 运维/维修/合规类文档，一次读对 | 1 | `JuanMarchetto/doc-standards-skill` 或 STE + linter |
| 中文向用户/老板汇报结论 | 1 | `dualface/ste-zh` |
| 架构、数据流、状态机、因果链 | 2 | `excalidraw-diagram` |
| "噪声系数调大点会怎样" | 3 | `explain-webpage`、`canvas-design` |
| 培训物料、对外科普、算推导演示 | 4 | `devamsheth21/3b1b-video-skill`（全流程）/ `Yusuke710/manim-skill`（只要动画） |
| 论文 → 教学视频 | 4 | `KhalilOthmanEng/3b1b-scientific-explanation` |
| 不知道用哪种，想让 agent 自己决定 | 全 | `ChangWenC/understanding-ladder` |

---

## 7. 安装速查

```bash
# 第 1 档：STE 写作（最轻）
mkdir -p ~/.claude/skills/ste100
curl -fsSL https://raw.githubusercontent.com/danyuchn/asd-ste100-skill/main/SKILL.md \
  -o ~/.claude/skills/ste100/SKILL.md

# 第 4 档：单文件 explain（四档全包，最轻）
mkdir -p ~/.claude/skills/explain
curl -fsSL https://raw.githubusercontent.com/Alon-W/explain-skill/main/skills/explain/SKILL.md \
  -o ~/.claude/skills/explain/SKILL.md

# 路由器：理解阶梯（一行装，支持 npx skills）
npx skills add ChangWenC/understanding-ladder

# 视频档依赖
uv tool install manim          # Manim Community
brew install ffmpeg
# 旁白：ELEVENLABS_API_KEY，或本地 Piper / Kokoro / espeak-ng
```

---

## 8. 容易踩的坑

- **别把上下级当竞品**：`asd-ste100` 与 `3b1b` 不是二选一，是同一个决策函数的不同分支。
- **过度爬档**：一句定义配一段视频，是成本黑洞。默认从能回答问题的**最低档**起步。
- **英文 STE 直接套中文**：规则可迁移，词表不可迁移。中文要用受控中文项目。
- **Manim CE ≠ ManimGL**：装错分支会到处报错，先确认 skill 支持哪个。
- **星标不等于质量**：第 1 档有大量复刻，差异在"是否带确定性 linter"和"是否覆盖本地语言"。
- **规则类 skill 会漂移**：没有 linter 的 STE skill，长会话里会逐渐退回原样。

---

## 9. 参考来源

- Andrej Karpathy，理解阶梯原帖：<https://x.com/karpathy/status/2105819303471976479>
- ASD-STE100 官方站：<https://www.asd-ste100.org/>
- ASD-STE100 Issue 9（PDF）：<https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf>
- Wikipedia：Simplified Technical English — <https://en.wikipedia.org/wiki/Simplified_Technical_English>
- 3Blue1Brown：<https://www.3blue1brown.com/> ／ Manim Community：<https://www.manim.community/>
- 标杆实现：`danyuchn/asd-ste100-skill`、`ChangWenC/understanding-ladder`、`Yusuke710/manim-skill`
