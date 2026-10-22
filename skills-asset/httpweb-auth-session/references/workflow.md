# Capture and verification workflow

## Capture

1. Confirm the user is signed in and the selected request succeeded.
2. Record its exact URL, Cookie request header, and request headers through Chrome DevTools/CDP.
3. Do not print the raw request or header values. Pass one compact JSON object directly to the importer stdin.
4. Declare the exact origin independently with `--origin`; the importer rejects a request URL from another origin.
5. Keep one profile per person/account when a device has multiple signed-in identities.

The importer deliberately keeps site-defined context headers and `Authorization`, because some applications require both cookies and contextual routing. It removes connection-specific headers, `Cookie`, `Host`, `Content-Length`, `Sec-*`, and `Proxy-*`.

## Verify

Run structural validation first. Then probe the smallest known authenticated read-only endpoint:

- Prefer identity, permission, metadata, or list endpoints.
- Default to GET/HEAD.
- If a read endpoint uses POST, explicitly acknowledge it with `--read-only-post` and supply a bounded body file.
- Supply expected status codes and, when useful, a small response marker. The response body is scanned in memory but never printed.
- A redirect is treated as failure because it commonly means the session was sent to login.

## Refresh and revoke

New captures use a 7-day local TTL by default; pass `--ttl-days N` with `N >= 7` when a longer local cache is needed. Re-run capture to atomically replace an expired or server-rejected bundle. To revoke local reuse, delete the exact profile directory. To revoke the browser session itself, sign out or invalidate it on the target system; deleting the local copy alone does not revoke the upstream session.

## Non-goals

- Capturing passwords, form values, TLS keys, or browser profile databases.
- Bypassing MFA, SSO, authorization, CAPTCHA, or device policy.
- Sharing one person's session bundle with another person.
- Treating a user Cookie as a permanent service token.
- Automating native PC apps that expose no DevTools/CDP or HTTP request record.
