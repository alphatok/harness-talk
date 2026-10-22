# Deterministic merge policy

Stable identities are dashboard/component/metric key, contract operation ID, binding scope/dashboard/route/release tuple, and provenance capture/source/time/confidence tuple. Runtime IDs are values, never global identities.

- Equal facts are idempotent. Objects merge recursively; primitive lists are sorted unions; keyed lists merge by identity.
- Renames retain prior names as aliases.
- Scalar/type/schema conflicts remain under `variants` and force `needs_revalidation`; never choose silently.
- Verified live evidence outranks DOM; tooltip text outranks inference; evidence remains append-only.
- Absence never deletes an object. Only a complete same-scope/release traversal may tombstone it.
- Schema, target path, fingerprint, or release drift requires live revalidation.

Outputs: canonical catalog/contracts, private instance bindings, and generated Markdown. Never merge Markdown edits back into JSON.
