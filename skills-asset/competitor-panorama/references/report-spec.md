# 三段式报告结构规范

结构对齐参考报告（曾用实例：《有赞导购经营全景图.html》《Salesforce产品经营全景图.html》）。**复用结构与类名，替换内容与品牌 token。**

## 可移植结构

不依赖作者本机样本。用户提供参考文件时可借鉴结构；否则按以下骨架生成，计数与配色均以本次报告为准。

## 页面骨架

```
<title> + <meta charset> + <style>（全部内联，零外部依赖，本地文件交付）
<div class="wrap" id="top">
  <header class="masthead">…</header>
  <nav class="nav-bar">（可选）
  <section class="sec" id="sec1">01 业务架构</section>
  <section class="sec" id="sec2">02 产品架构</section>
  <section class="sec" id="sec3">03 模块功能地图</section>
  <footer class="footer">数据口径 · SOURCES & NOTES</footer>
</div>
```

## Masthead

- `.eyebrow`：目标公司 · 产品线／结构分析（底本说明）
- `h1` + `.en` 英文副标
- `.lede`：一段话讲清端到端价值链（首尾闭环）与产品面承载
- `.meta-chips`：N 个业务域 / N 个功能模块 / N 个核心模块 ★ / 官方来源 N 条 · 日期

## Section 01 业务架构 SVG（viewBox 1240×600±80）

自上而下分带，margin 24，右界 1216：

1. **角色行**：n 角色（CEO/CMO、销售、服务、CIO、员工顾客等），`box` rect `w=172 gap=22`（4 角色则 `w=252 gap=26`），高 80；标题 `.bt` y=+32，副线 `.bn` y=+58；左上 `.lbl` 「角色 / ROLES」
2. **连接线**：角色底 → 触点顶，dashed `gx`（x 对齐各中心）
3. **触点行**：`w=252 gap=26` 高 62；标题 y=+30 副线 y=+51
4. **价值链**：6 节点 `x=56 起 w=168 gap=19` 高 92；序号「①…⑥」+ 节点名 `.bt` y=+36，副线 `.bn` y=+64；节点间箭头 `g stroke="var(--line-strong)" marker-end`
5. **校准回路**（右上回投）：`path d="M{cx末},top V{top-上浮} H{cx首} V{top}"` class acc marker-end 绿箭头；回路标签 `.sub` 居中在横线之上
6. **收入结构条**（财务事实可视化，可选）：bar 位于链条下方，分段宽 ∝ 分部收入占比×总宽，段间 4px 白分隔；其下一行 chips（`w=203 gap=22`，两行文字：品类名 `.ct` + 「占比 · 金额」`.subl`）；再下一行小注 `.subl` 说明披露口径
7. **生态协同条带**：分隔虚线 + `.lbl`「生态协同 / ECOSYSTEM」+ pills（`chipc` rx=22 高 44 内 `.ct` 单行）+ 底部一句话定位 `.bn`
8. `figcaption`：`<b>一图读懂：</b>` + 闭环一句话 + 关键数字

`aria-label` 完整描述图内容；所有带 `stroke` 的 `<g>` 内文字必须靠全局规则 `svg text,svg tspan{stroke:none}` 防继承描边（见 qa-checklist）。

## Section 02 产品架构 SVG（viewBox 1240×524~636）

- 左侧**层级标签列** x=20：层名（14px 600）+ `.subl` 副注，y 对应各层中线偏上
- 各层 rect：`x=140 w=1040`（右留 spine 位），层高 64~186，层间距 14
- 层内内容两种：
  - 触点层：pill 组（`chipc` rx=20 高 40）
  - 应用云层：`.accbox` 大卡内分组副标题 `.subl` + 小 chip 矩阵（`w=90~140 h=44 gap=12`），chips 行宽按内容定，**先算总宽再定 x**（总宽 = Σw + gaps ≤ 996）
- **双脊柱**（右缘 x≈1198）：数据回流 ↑ / 行动回投 ↓ 两行竖排文字，`transform="rotate(90 cx cy)"`（垂直文字，勿用水平文字硬挤 40px 窄缝）
- 研判层（智能层/数据层）用 `.accbox`（主题色软底）突出
- figcaption 讲「自上而下分发，自下而上回流」

## Section 03 模块能力地图

1. **flowstrip**：三栏 flex —— 左（云族 chips）+ 中（「订单·会话·行为 ↑↓ 洞察·预测·Agent 行动」`.fmid`）+ 右（底座 chips）
2. **GOLDEN PATH 主链路 SVG**：8 节点 `x=52 w=128 gap=16`（viewBox 1240，总宽 ≤1216），节点头部 ★ 标注 + 图内小字路径说明；下方 `.legend`：★ 核心模块（去掉它链路断）/ ● 常规模块 / 虚线 = 细节未官方确认
3. **域×模块矩阵**（核心交付）：
   - `.domain` > `.dhead`（`.did` 域号 + h3 + 一句话 + `.dmeta` 模块计数）
   - `.mrow`（grid 236px/1fr/1.35fr）多次重复：
     - `.cell1`：`.mno`（M 序号）+ `.mname`（模块名+`.star`）+ `.mtag`（定价/版本）
     - `.cell2`：`.chips`（能力 chip；未确认用 `.chip.p` 虚线）
     - `.cell3`：`.caps` 列表（2-4 条能力要点，`<b>` 开头）
4. 域划分逻辑：按端到端链路顺序（数据基石 → 营销 → 销售 → 履约 → 服务 → 门户 → 分析 → 智能 → 协同 → 平台 → 行业 → 底座）
   - 曾用实例：Salesforce 12 域 49 模块 14★（D1 数据基石 D2 营销获客 D3 线索与销售 D4 交易履约 D5 服务留存 D6 体验门户 D7 分析决策 D8 智能与代理 D9 协同集成 D10 平台开发 D11 行业纵切 D12 信任底座）

## Footer 数据口径（`.footer` h4 + ①-⑤ 段）

1. 来源与方法（白名单+访问日期+条数）
2. ★ 判定标准
3. 品牌迁移对照（旧名 → 新名）
4. 财务口径（分部/分段披露、ARR 等口径变化警示、价格列表价声明）
5. 未确认项清单（不编造承诺）

## 设计系统

### Token（双主题；实例=Salesforce 蓝系，需按实际色值验证）

```
:root{ --paper:#f4f7fa; --card:#fbfcfe; --ink:#141f2b; --mut:#526475; --faint:#74828f;
  --line:#dfe7ee; --line-strong:#c8d4df;
  --acc:#0b5cab; --acc-bright:#0176d3; --acc-ink:#eaf4fd; --acc-soft:#e7f1fc; --acc-line:#8fbce8;
  --star:#a06a12; --star-soft:#f5ead0;
  --ui/-mono 字体栈 }
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){ 深色对应 token } }
:root[data-theme="dark"]{ 同上（让手动切换覆盖系统） }
```

换目标公司时：主色 `--acc` 取该公司品牌主色并**用 WCAG 脚本验证**——`--acc` 作文本色对 `--card` 对比度 ≥4.5:1、`--acc-ink` 对 `--acc` 底 ≥4.5:1；`--mut/--faint` 对两色面板 ≥4.5:1。

### 结构类名清单（全部沿用参考报告，勿改语义）

`masthead/eyebrow/lede/meta-chips | sec/figwrap/figure/figcaption | gx/lbl/box/bt/bn/acc/accbox/accink/chipc/ct/ctm/subl/stroke-acc | flowstrip/fside/fmid | domain/dhead/did/dmeta/mrow/cell1-3/mno/mname/star/mtag/chips/chip(.on/.p)/caps/legend | footer`

### 布局公式（1240 viewBox 通用）

- 等距 grid：`总宽 = n×w + (n-1)×gap`，首元素 x=24（或 56），末元素右缘 ≤1216
- 角色行 172/22（4 个则 252/26）；触点行 252/26；价值链 168/19；GOLDEN PATH 128/16
- 校准回路：末节点顶中 → 上浮 36px → 横穿全链 → 首节点顶中
- 两行文字卡：标题 y 中心±16；`.subl` 下行

## 交付物要求

- 单文件 HTML，零外部依赖，全部样式/图内联
- 图上所有事实在页脚可溯源；未确认项以虚线 chip + 脚注双重标注
- 桌面优先（1240 视口），≤920px 降级单列（响应式断点只影响 HTML 网格，SVG 靠 `.figwrap{overflow-x:auto}` 横向滚动承载）