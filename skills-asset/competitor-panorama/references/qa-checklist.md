# 确定性 QA 清单

结构、模型与视觉分别检查。脚本辅助定位，不能替代真实浏览器呈现检查。

## 1. 结构校验（无依赖，全部命令化）

```bash
# 标签平衡（grep 计数近似即可，浏览器容错会掩盖问题）
grep -o "<div"  报告.html | wc -l   # vs grep -o "</div>"
grep -o "<g "   报告.html | wc -l   # vs grep -o "</g>"
grep -o "<section" 报告.html | wc -l # vs </section>
# 占位符必须清零
grep -n "placeholder\|__SEC\|__TODO__\|TODO" 报告.html → 期望 0 命中
# 计数一致性（与 masthead meta-chips 核对）
grep -o 'class="domain"' 报告.html | wc -l          # = 域数
grep -o 'class="mrow"'   报告.html | wc -l          # = 模块数
grep -c '★'              报告.html                    # 与「N 个核心模块 ★」一致
```

## 2. SVG 文字越界检测（skill 内置脚本）

```bash
node scripts/svg-overflow-qa.js 报告.html 浏览器可执行路径
# 输出所有越界 text 的坐标与所属 viewBox；0 越界 → exit 0
```

脚本是 **transform 感知**的（用 getBoundingClientRect 映射回 viewBox 坐标）。注意：Chrome 的 `getBBox()` 对带 `rotate()` 的 text 会报未旋转的 bbox（误报越界）——所以不要用 getBBox 方案，本脚本已内置正确实现。

## 3. 渲染巡检（最后一道）

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --screenshot=/tmp/final.png \
  --window-size=1240,3400 --hide-scrollbars "file:///绝对/路径/报告.html"
sips -s format jpeg -s formatOptions 85 /tmp/final.png --out /tmp/final.jpg
```

看整页 JPEG：图带间是否重叠、chips 行是否碰撞、文字是否溢出卡片边界。

## 4. 陷阱库（本 skill 实际踩过的坑，逐条防范）

| # | 陷阱 | 症状 | 对策 |
|---|---|---|---|
| 1 | **SVG stroke 继承**：带 `stroke` 的 `<g>`（如 `.chipc`、节点箭头组）内的 `<text>` 会沿字形描 1px 边 | 小字（尤其 11px mono）发糊、发虚、「颜色看不清楚」 | 全局规则 `svg text,svg tspan{stroke:none}`，所有 SVG 图必带 |
| 2 | 双脊柱竖排标签误用水平文字 | 右侧 40px 窄缝放不下 120px+ 的文字，被 viewBox 裁掉 | `transform="rotate(90 cx cy)"` 竖排 |
| 3 | band 截图 Read 不显示（会话内图像回显偶发失败） | 局部 PNG/JPEG 裁剪读不到 | 整页 JPEG 可显示；裁剪失败时退回确定性结构检查 |
| 4 | sips cropOffset 是**中心点**语义不是左上角 | 裁出来的全黑/空 | center = 顶部偏移 + 高/2 |
| 5 | Edit 多处匹配 | 改错位置 | old_string 带足上下文（前后邻行） |
| 6 | 分段写入时漏掉容器开/闭标签（如 footer） | 标签不平衡、渲染错乱 | 每次 Section 写入后跑结构校验 |
| 7 | 遗留占位标记 | `__SEC__` 等残留 | 交付前 grep 清零 |
| 8 | 同 y 带多行内容坐标冲突（如生态标签 vs 收入 chips） | 文字重叠 | 写入前规划每带 y 区间，宁留白不挤压 |
| 9 | 多语言串入笔误（法语/日文 IME 混入） | 错别字 | 全文校对关键词（产品名、模块名） |

## 5. 完成标准对照表

- [ ] 3 处 SVG bbox 检测 0 越界
- [ ] 域/模块/★ 计数与 masthead 一致
- [ ] 无占位标记、标签平衡
- [ ] 整页渲染巡检无碰撞
- [ ] `svg text,svg tspan{stroke:none}` 规则存在
- [ ] 页脚口径逐条可溯源；未确认项全部列入
- [ ] 深色模式 token 完整（`:root` + prefers-color-scheme + data-theme 三处）
命令均从本技能目录执行，按当前操作系统选择工具。星号计数按实际核心模块节点统计，不能用包含图例与说明的字符总数代替。标签计数只是辅助，不能证明 HTML 语法或布局正确。
