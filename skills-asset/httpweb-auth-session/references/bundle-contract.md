# Session bundle contract

Default root: `~/httpweb_auth`. Override only with `HTTPWEB_AUTH_HOME` or the explicit `--auth-home` option.

```text
~/httpweb_auth/
  example.com/
    default/
      cookies.txt
      headers.json
      manifest.json
```

Ports are encoded in the host directory as `example.com__8443`. Profiles must match `[A-Za-z0-9._-]{1,64}` and may not be `.` or `..`.

## Files

- `cookies.txt`: Netscape cookie jar. Cookies reconstructed from a request are host-only, path `/`, and receive the bundle's local expiry because the Cookie request header does not expose their original expiry or path metadata.
- `headers.json`: reusable request headers after removing Cookie and connection/browser transport headers. Values are credentials and must not be displayed.
- `manifest.json`: non-secret binding metadata: format version, exact origin, host key, profile, capture and expiry times, local TTL days, source, cookie count, header names, and filenames.

The default and minimum local TTL is 7 days. A larger value may be selected at import time. The loader rejects an expired bundle; legacy manifests without `expiresAt` are treated as expiring 7 days after `capturedAt`. This local TTL is only an upper bound and does not override server-side session expiry.

All directories are `0700`; all files are `0600`. The loader rejects symlinks, foreign ownership, broad permissions, malformed JSON, unknown bundle versions, and origin/profile mismatch.

## Provider contract

`SessionBundle.load(origin, profile="default", auth_home=None)` returns a bundle after all checks pass.

- `headers_for(url)` returns reusable headers plus an in-memory Cookie header only for the exact origin.
- `open(url, method="GET", ...)` refuses methods other than GET/HEAD unless `allow_read_only_post=True` and method is POST.
- Redirects are not followed.
- Callers must bound timeout and response size and must not log returned headers or response bodies.

This format is intentionally plain text and stdlib-only so it can be consumed by any Agent or coding tool. Copy the entire Skill directory; keep runtime bundles outside it.
