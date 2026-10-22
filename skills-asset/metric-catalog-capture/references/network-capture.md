# Network capture for Shadow DOM and iframe dashboards

## Capability ladder

Use the first available read-only mechanism and record which tier produced each fact:

1. Browser-native network events with request body and response body access.
2. Browser asset observations for method, URL, status, timing, and request counts.
3. Production vendor bundle inspection for deterministic request builders and response projections.
4. DOM rendering evidence only.

Tiers 2–4 may enrich a contract but cannot make it `executable`. Only a real request passing all four verification checks can do that.

## CDP capture when the browser exposes it

Enable the network domain before reload. Auto-attach to child targets so out-of-process iframes are included. Shadow DOM requests remain on the parent target.

```js
const cdp = await tab.capabilities.get("cdp");
await cdp.send("Target.setAutoAttach", {
  autoAttach: true,
  waitForDebuggerOnStart: false,
  flatten: true,
});
await cdp.send("Network.enable");
const start = await cdp.readEvents({methods: ["Network.requestWillBeSent"]});
await tab.reload();
const events = await cdp.readEvents({
  afterSequence: start.cursor,
  methods: [
    "Target.attachedToTarget",
    "Network.requestWillBeSent",
    "Network.responseReceived",
    "Network.loadingFinished",
  ],
  limit: 1000,
  timeoutMs: 15000,
});
```

For every `Target.attachedToTarget`, run `Network.enable` on its `sessionId`. Filter only the read-only analytics paths in scope. Parse `request.postData`, then call `Network.getResponseBody` only after `loadingFinished`, using the correct target session.

Keep request/response content in memory. Persist only:

- method and normalized relative path;
- redacted request JSON Schema and runtime source bindings;
- response JSON Schema, business-code rule, target projection, counts, and hashes;
- request ID to action/widget correlation;
- HTTP status, elapsed time, and verification result.

Drop all headers, cookies, tokens, raw customer/order rows, and merchant-specific option values before creating the CaptureRun.

## Authorized system Chrome workflow

When the user explicitly authorizes system Chrome, launch a separate temporary profile with a narrowly scoped debugging port, let the user sign in interactively, and never copy cookies from another profile. Conceptual example; adapt to the OS and supported browser tooling:

```text
<supported-browser-launch-command> --remote-debugging-address=127.0.0.1 --remote-debugging-port=<local-port> --user-data-dir=<new-temporary-profile>
```

After login, run `scripts/capture_cdp_network.py` against the visible target:

```text
python3 scripts/capture_cdp_network.py \
  --port 9222 \
  --page-url-contains analytics.example.com \
  --navigate <dashboard-url> \
  --match /api/analytics/ \
  --settle-seconds 12 \
  --out <redacted-capture.json>
```

For a user-triggered state, attach without reloading and keep a bounded listener open:

```text
python3 scripts/capture_cdp_network.py \
  --port 9222 --page-url-contains analytics.example.com \
  --no-reload --settle-seconds 120 \
  --out <redacted-capture.json>
```

For repeated labels, Shadow DOM controls, dropdowns, inputs, or Tooltip hover, use repeatable goal-level actions rather than page-specific code:

```text
--action '{"kind":"click","text":"市","withinText":"客户收货区域分布"}'
--action '{"kind":"hover","text":"业绩金额"}'
--action '{"kind":"open","text":"全部","withinText":"会员等级"}'
--action '{"kind":"input","withinText":"会员等级","value":"测"}'
```

Each action records whether it matched, visible option counts, newly displayed Tooltip texts, and only the matching request IDs observed after the action. Use `--extra-match` for an additional known read-only option endpoint; do not broaden capture to unrelated page traffic.

The script reloads, navigates, or attaches to the selected page, captures parent-target and attached-frame network events, reads response bodies only long enough to derive schemas, and persists no headers, credentials, raw response bodies, or raw business rows. Use a dashboard-scoped operation ID for live verification when a generic endpoint is shared by unverified widgets.

For child OOPIF targets, `Target.setAutoAttach` alone is insufficient: enable `Network` and `Runtime` on every attached `sessionId`. For lazy dashboards, use bounded recursive scroll passes that enter same-origin iframes and open Shadow Roots. Known read-only view labels can be triggered with repeatable exact `--click-text` arguments; this is the preferred way to activate tab-specific Widget requests without exploring a filter Cartesian product. A remote dropdown may be opened and its first visible option selected with `--click-first-option`, but the option value must remain in memory or private instance cache and must never enter public catalog artifacts.

Recommended incremental sequence:

1. Initial reload captures `repoQuery` and default Widget requests.
2. Recursive scroll closes lazy Widget coverage.
3. Scoped actions capture alternate Tabs, repeated labels, dynamic options, and Tooltip states.
4. Merge runtime titles/IDs to semantic Widget keys; retain unmapped runtime components explicitly and model parent containers through child dependencies.
5. Re-run coverage and target only remaining blockers.

## Vendor-specific static evidence

Use only request builders and projections actually observed for the authorized platform. Do not ship an internal vendor contract as a universal default. Static observations stay `needs_revalidation` until a real scoped read-only request passes all checks. Never guess runtime IDs, field types, business success rules, or supported endpoints from another deployment.

## Explicit blocker

If the selected browser exposes DOM but not native network events, do not attempt script-URL, raw-CDP, cookie-copying, or other policy workarounds. Record `network_debug_capability_unavailable`, keep the contract non-executable, and request authorization for a supported signed-in browser that exposes network capture.
