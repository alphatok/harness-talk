# 官方源白名单与采集协议

## 白名单模式（每个目标公司一套）

```
vendor.com                      # 官网产品/新闻
help.vendor.com                 # 帮助中心（功能细节主源）
developer.vendor.com            # 开发者文档、API/对象版本
investor.vendor.com             # 财报、电话会、披露
trust.vendor.com                # SLA/安全合规/可用性
trailhead.vendor.com            # 产品学习路径（教育源）
exchange/marketplace.vendor.com # 生态市场
sec.gov                         # 美股上市公司 10-K/10-Q
生态子公司域（如某公司的 MuleSoft/Slack/Tableau 对应域）
```

国内非上市 SaaS：官网 + 帮助中心 + 官方公告/发布会实录（无财报则注明「本次未查到公开财报」，财务域降级为「商业模式」推断并标注是推断）。

## Salesforce 实例白名单（已验证使用）

salesforce.com / help.salesforce.com / developer.salesforce.com / investor.salesforce.com / trust.salesforce.com / trailhead.salesforce.com / appexchange.salesforce.com / sec.gov / mulesoft.com / slack.com / tableau.com

## 证据优先级

10-K/年报 > 财季新闻稿/电话会 > 官网产品页 > 帮助中心 > Trailhead/Trust/生态市场 > 开发者文档

冲突时取高优先级，冲突本身记入存疑清单。

## 采集协议

- 每条事实：`事实 | 来源URL(s) | 访问日期`，报告页脚注明「官方来源 N 条 · 日期」
- 按业务、产品、数据与 AI 主题采集，默认串行；URL 汇总去重后统计条数
- 每路末尾必须带「存疑清单」（口径冲突 / 缺失 / 无法确认项）

## 口径警戒清单（采集时必查）

1. **品牌迁移**：产品改名（如 Sales Cloud→Agentforce Sales、Data Cloud→Data 360、AppExchange→AgentExchange）——正文用新名，括注旧名；引用旧财报数字时说明旧口径对应关系
2. **分段披露变化**：分部口径从 A 改 B（如 FY27 起五分部改两段式）——不能把新旧口径数字混排对比
3. **ARR/指标扩容**：某季度起 ARR 或 AWU 覆盖范围扩大（含新产品线）→ 同比增长不可作同口径对比，必须加警示
4. **定价口径**：官网列表价 ≠ 成交价（未含折扣/税费）；订阅分层（org 月/用户月/会话/credit）写清单位
5. **GA 状态**：pilot/GA/区域限制写明确；逐项 GA 状态无法确认时进未确认项，不写「已全面 GA」
6. **客户数口径**：总客户数 vs 高价值分层客户数（如 ≥$1m ARR），不能混用

## 反面清单（不采用）

- 二手媒体/分析师报告的数字（如第三方市场份额）
- 论坛、社区问答里的能力猜测
- AI 幻觉产生的「官方不存在」产品名（每次引用新名称前先在白名单域内验证存在）
- 竞对材料中的互黑表述
证据按问题选用：财务以监管披露为准，功能边界优先帮助中心和开发文档。示例域名需在本次研究中核实，示例产品改名与披露变化不作为当前事实直接引用。
