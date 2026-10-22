---
name: metric-catalog-query
description: 问“本月销售额”却总拿到不同口径？基于已建立的指标目录匹配定义、时间和筛选条件，在查询依据与权限均通过核验时读取数据；有歧义先列候选，失败明确说明。帮助减少查错指标、混用单位和误读空值。用法：“按这个指标目录比较本月与上月销售额。”实时查询还需适配器与授权。
---

# 指标问数助手｜先对口径、再查数据

先提供已脱敏的指标目录。没有目录时先整理目录，可搭配 `metric-catalog-capture`，也可使用符合契约的其他目录来源。此包不含企业账号、业务数据、默认看板或即用的生产适配器。

Python工具可做本地匹配与离线验证。实时查询须另行接入用户授权的只读适配器；浏览器CDP适配器还需调试能力与 `websocket` 模块。不要把离线测试通过当成真实平台已连通。

Use the hierarchical Markdown index only for recall. Treat canonical JSON as the sole execution source; never construct AJAX from prose in the index.

## Workflow

1. Locate `index/metrics-index.md`, `catalog/catalog.json`, `catalog/contracts.json`, and the current instance binding if available.
2. Classify `definition`, `data`, `compare`, or `visualize`; extract metric/dashboard hints and filters.
3. Shortlist from Markdown, then rerank canonical JSON. Read [references/query-contract.md](references/query-contract.md) for contracts.
4. Clarify before any request when the leading match is weak or materially tied. Return 2–5 candidates.
5. For data intents, fail closed unless every selected widget is `executable` and its operation exists.
6. Resolve IDs using [references/runtime-binding.md](references/runtime-binding.md). Default to `reuse`; progressive-discover and retry at most once, only for binding or schema drift.
7. Validate HTTP status, business success, fingerprints, applied filters, and projection.
8. Normalize and render using [references/presentation.md](references/presentation.md), disclosing selection, conditions, provenance, fallback, and warnings.

Use `scripts/query_catalog.py` for deterministic retrieval, gating, fixture tests, and dry runs. Live access requires an explicitly injected adapter; the script has no credentials or built-in authenticated client.

## Safety

- Query read-only operations only; never save, publish, configure, export, or mutate business objects.
- Never persist Cookie, Authorization, passwords, raw customer/order rows, adapter context, or live responses.
- HTTP 200 alone is insufficient. Reject business failures, login HTML, schema/semantic drift, missing fields, and filters not proven applied.
- Never progressive-fallback after auth/permission, rate-limit, or network failures.
- Preserve nulls; never silently combine incompatible units, periods, granularities, organizations, dimensions, or definitions.

Complete with a verified result, authoritative definition, bounded clarification list, or explicit blocked/error result. Never label an unverified contract executable.
