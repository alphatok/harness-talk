---
name: metric-catalog-capture
description: 看板多、指标同名，查数前总要先问口径？在授权范围内整理页面、指标说明、筛选条件和只读查询证据，生成可检索的指标目录与覆盖清单，帮助减少重复摸索。用法：“为这个看板建立指标目录，缺失口径明确标记。”需可用浏览器导出或网络观察能力，不携带任何真实业务目录。
---

# 指标目录整理｜口径、看板、查询依据

先给看板范围与可用的脱敏导出。此包不含已登录浏览器、真实接口契约或指标目录。页面观察能力由当前宿主提供；具体平台URL、读接口匹配规则和网络能力必须按现场证据配置。无网络证据时可整理定义，但不得把契约标记为可执行。

配套Python工具只处理本次输入。网络采集脚本另需当前环境提供的 `websocket` 模块与受支持的浏览器调试能力；不得为完成任务绕过宿主工具限制。

Build an evidence-backed catalog without credentials or raw business rows. JSON is the execution source of truth; Markdown is generated only for semantic retrieval.

## Goal-driven workflow

1. Read [references/capture-workflow.md](references/capture-workflow.md), discover the smallest page-state graph that closes the requested URL or menu scope, and keep every discovered node explicit.
2. Read [references/network-capture.md](references/network-capture.md) only when AJAX evidence is needed. Prefer the signed-in in-app browser; use authorized system Chrome CDP when request bodies, iframe, Shadow DOM, or manual interaction capture requires it.
3. Read [references/catalog-schema.md](references/catalog-schema.md), build a redacted CaptureRun, and validate it with `scripts/capture_catalog.py`.
4. Revisit only unresolved coverage. Classify real data leaves, composite/navigation parents, UI controls, configuration-only parameters, and legitimate empty states instead of forcing every label to own an AJAX call.
5. Read [references/merge-policy.md](references/merge-policy.md), dry-run when classification or schema changed, then merge with `scripts/merge_catalog.py`; never hand-edit canonical JSON.
6. Regenerate the Markdown index and run `scripts/validate_catalog.py`. Stop with machine-readable blockers when evidence cannot close the scope.

## Invariants

- Every discovered node is `captured`, `ignored_with_reason`, or `blocked`.
- Preserve question-mark/tooltip definitions verbatim; flag inconsistencies instead of repairing them.
- Component kinds are `data_leaf`, `composite`, `filter`, `layout`, and `navigation`.
- Executable data requires a real read-only request passing HTTP 200, business success, response schema, and target projection checks.
- Store stable semantics in templates and runtime IDs in private instance bindings. Raw widget IDs are never global keys.
- Never persist Cookie, Authorization, passwords, tokens, customer/order rows, or merchant-specific dynamic option values in public artifacts.
- Capture only read operations. Writes and exports are outside this skill.

Default data home is `~/.metric_catalog`: immutable runs in `captures/`, canonical JSON in `catalog/`, generated Markdown in `index/`, private bindings in `instances/<scope-key>/`, and coverage in `coverage/`.

Complete only when traversal is closed, all nodes have status, help is captured or blocked, live checks pass, references resolve, and privacy validation passes.
