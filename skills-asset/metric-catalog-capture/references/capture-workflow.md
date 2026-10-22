# Capture workflow

Prefer a signed-in in-app browser for AJAX. Scripts consume a redacted JSON export and never receive credentials. If Shadow DOM, iframe, lazy state, or bodies cannot be captured, record a blocker with route, component, action, and error; use fallback browsers only with explicit authorization.

Before traversal, audit browser capabilities as described in [network-capture.md](network-capture.md). Treat DOM traversal and network capture as separate layers: open Shadow roots and iframe bodies solve component discovery, but do not prove that request bodies or responses were captured.

Traverse breadth-first using route, tabs, stable controls, and release fingerprint as state. Enumerate menus, tabs, panels, widgets, controls, iframes, open Shadow roots, safe dropdowns, and bounded lazy scroll until no new keys appear. Revisit only states that expose new components or requests; avoid filter Cartesian products.

Treat labels as hypotheses, not API ownership. A visible parent such as “基本信息” or “访问场景” may be a composite/navigation node whose executable closure is its child Widgets. A parameter found only in configuration is `ignored_with_reason` when a closed traversal proves it is not a rendered user control. Do not invent a parent request or remote option resolver.

Preserve tooltip text verbatim. Enumerate static options; for remote options publish only schema/protocol/search/pagination and counts. If opening a dropdown produces no option request, distinguish a legitimate empty local enum from a blocked remote resolver using DOM state, configuration evidence, and the action's request delta. Scope an empty observation to the current instance/release unless broader evidence exists.

For BI v4 open Shadow DOM, recurse through `div[sandbox-type="shadow"]`; map runtime components from `[layout-item-panel="true"].bicore-card-config` using `type` and `slot`, and cross-check charts with `[chart-panel][data-id]`. For Legacy BI v3, enter the business frame rather than help/chat frames; a robust first candidate is `iframe:not(#wpm-iframe):not(#udesk_iframe)`. A missing `src` is not a blocker because BIStudio may dynamically populate the frame.

Create an `actionId` before each safe UI action and map the new request IDs to that action and component. Prefer text plus container scope over coordinates; use occurrence only to disambiguate repeated labels. Capture method, normalized path, redacted schemas/runtime sources, projections, business rule, pagination, fingerprint, and evidence ref. Never persist auth/session headers, full business responses, customer/order rows, or real option values.

Live validation requires HTTP 200, business success, schema match, and target projection. Valid empty rows pass with a valid envelope. Composite widgets require all dependencies. UI-only nodes use DOM evidence. Login HTML, business errors, wrong fingerprints, missing fields, and drift fail.

```bash
python3 scripts/capture_catalog.py init --entry-url URL --scope menu --scope-key HASH --out capture-run.json
python3 scripts/capture_catalog.py validate capture-run.json
```

Keep validated runs immutable; incomplete closure remains `incomplete` with blockers.
