---
name: httpweb-auth-session
description: 浏览器里已经登录，脚本查接口还要重新接入？在明确授权的网站范围内，复用登录状态和必要请求信息，让脚本继续执行只读查询，减少重复配置与登录。凭据只保存在本机，不跨网站复用。用法：“复用这个网站的登录状态，先验证查询接口。”需宿主支持读取授权请求。
metadata:
  version: "1.0.1"
---

# 浏览器登录复用｜免重复登录查接口

技术向工具，先明确站点、请求、用途和保存位置，再导入用户授权的成功请求。凭据不得放进对话、日志、源码或分享包。安装本包不会抓取或保存任何会话。脚本用Python 3.10+标准库；权限检查依赖POSIX权限语义，Windows环境需先验证或改用受支持的凭据机制。

提供本地合成会话自测，不代表任何真实网站已接入。会话失效、无权限或不同源时停止，不能复制其他浏览器配置或扩大用户访问范围。

Create and reuse authenticated HTTP sessions without placing secrets in prompts, logs, source control, or environment variables.

## Security boundary

- Capture only a request the signed-in user successfully made and explicitly placed in scope.
- Bind each bundle to one exact origin: scheme, host, and port. Never replay it cross-origin.
- Store runtime secrets only under `${HTTPWEB_AUTH_HOME:-~/httpweb_auth}`.
- Keep directories `0700` and credential files `0600`; reject symlinks, foreign ownership, and group/world-readable files.
- Never print Cookie values, authorization values, response bodies, or complete request headers.
- Use `GET` or `HEAD` for probes. Permit `POST` only with `--read-only-post` when the known read-only API requires it.
- Do not submit forms, mutate data, follow redirects, export bulk business data, or broaden the logged-in user's permissions.
- A native PC app is supported only when it exposes DevTools/CDP or an exportable HTTP request record.

Read [references/bundle-contract.md](references/bundle-contract.md) before integrating a Provider. Read [references/workflow.md](references/workflow.md) when capturing or refreshing a session.

## Workflow

1. In Chrome DevTools/CDP, identify one successful request to the target origin.
2. Obtain only its URL and request headers. Keep the raw result suppressed from user-visible logs.
3. Feed one JSON object to `scripts/import_devtools_request.py` on stdin:

```json
{"requestUrl":"https://example.com/api/me","cookie":"name=value","headers":{"x-context":"value"}}
```

4. Validate the bundle with `scripts/validate_bundle.py`.
5. Probe a known read-only endpoint with `scripts/probe_session.py`.
6. Point the consuming Provider at the bundle directory or use `SessionBundle` from `scripts/session_bundle.py`.

The importer uses a denylist for connection-specific browser headers, so site-specific context and authorization headers remain reusable. It removes `Cookie` from `headers.json` and stores it only in the Netscape cookie jar.
New bundles remain locally reusable for 7 days by default. Use `--ttl-days N` for a longer lifetime; values below 7 are rejected. This local lifetime cannot extend an upstream login: a server-side expiry or 401 still requires a fresh capture.

## Commands

Use Python 3.10+ and no third-party packages.

```bash
python3 scripts/import_devtools_request.py --origin https://example.com --profile default --ttl-days 7
python3 scripts/validate_bundle.py --origin https://example.com --profile default
python3 scripts/probe_session.py --origin https://example.com --profile default --url https://example.com/api/me --expect-status 200
python3 scripts/self_test.py
```

To migrate a previously captured Netscape jar and context-header file without exposing values:

```bash
python3 scripts/migrate_legacy_bundle.py --origin https://example.com \
  --cookie-file /absolute/path/cookies.txt --headers-file /absolute/path/headers.json
```

For a read-only JSON API that uses POST:

```bash
python3 scripts/probe_session.py \
  --origin https://example.com \
  --url https://example.com/api/read \
  --method POST \
  --read-only-post \
  --body-file /absolute/path/request.json \
  --content-type application/json \
  --expect-status 200
```

## Provider integration

Import `SessionBundle` and call `SessionBundle.load(...)`. Use `headers_for(url)` for a same-origin URL, or `open(...)` for a bounded request. Treat returned headers as secrets in memory. Do not log them.

If the target system already has a supported service token or delegated identity contract, prefer that contract for stable automation. This Skill is for user-session workflows and does not turn a browser session into a service credential.

## Acceptance

- `scripts/self_test.py` passes.
- `scripts/validate_bundle.py` reports `valid: true` without exposing secret values.
- A known read-only endpoint returns the expected status or marker.
- Credential directories and files have the required modes.
- The Provider rejects a different origin, redirects, write methods, unsafe permissions, and tampered manifests.
