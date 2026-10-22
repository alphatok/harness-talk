# Catalog schema

JSON is authoritative; Markdown is derived. CaptureRun contains metadata plus arrays `dashboards`, `contracts`, `instanceBindings`, `actions`, and `blockers`, with explicit redaction assertions.

Dashboard templates contain stable `key`, name, aliases, menu path, route patterns, tabs, controls, widgets, semantic fingerprint, statuses, and provenance. Every nested node has a stable key, hierarchy path, `captureStatus`, and provenance. Blocked/ignored nodes require `statusReason`.

Widgets contain key, kind, title, aliases, hierarchy path, metrics, `authoritativeDefinitions`, filters, `parameterBindings`, `responseMapping`, operation refs, fingerprint, status, verification, and provenance.

`verifiedOperationRefs` is an optional live-verified execution closure. When present, execution derivation uses it instead of the union of historical generic `directOperationRefs` and `dependencyOperationRefs`. This keeps dashboard-scoped verification from promoting unrelated widgets that share the same endpoint path.

Contracts contain `operationId`, method, normalized relative path, redacted request/response schemas, business success rule, parameter sources, response projection, pagination, fingerprint, verification, status, and provenance. Status is `executable`, `needs_revalidation`, `blocked`, or `not_applicable`.

Bindings contain scope key, dashboard template key, route, release fingerprint, runtime dashboard/widget/dataset IDs, dynamic resolvers, schema fingerprint, timestamps, and provenance. Identity is `scopeKey + dashboardTemplateKey + route + releaseFingerprint`; widget identity additionally includes widget ID. Dynamic labels/IDs remain private.

Status axes: `uiCoverageStatus`, `definitionStatus`, `requestSchemaStatus`, `responseSchemaStatus`, `liveVerificationStatus`, `executionStatus`. Data leaves/remote filters are executable only when all applicable checks pass. UI-only nodes use `not_applicable` rather than fake operations.

Provenance records capture ID, source, observed time, and confidence. Verified live evidence outranks DOM; tooltip text outranks inference, without deleting history.
