# Query and catalog contract

Canonical JSON is the execution source. Markdown is recall-only and carries stable keys plus `contractRef` pointers.

## Minimum catalog

`catalog.json` contains `dashboards[]`; each dashboard has `key`, `name`, aliases/menu path/routes, and `widgets[]`. Each widget has stable `key`, `kind`, title/aliases/hierarchy, `metrics[]`, parameter and response mappings, operation refs, semantic fingerprint, provenance, and `executionStatus`. Metrics carry stable key/name/aliases, authoritative definition, response field, unit, and provenance.

`contracts.json` contains canonical `contracts[]` (the query runner also accepts legacy `operations` as an object keyed by operation ID or a list). Operations define method/path, parameter schema, success rule, response schema/fingerprint, semantic fingerprint, projection, dimensions/measures, and optional dynamic-option resolvers. A resolver may provide `naturalLanguagePatterns` with a named `value` group; the matched label is still resolved online to a wire ID. Credentials and business rows are forbidden.

## Selection

- Recall text includes menu, dashboard, tabs, widget, metric aliases, and authoritative definition.
- Exact stable key or metric name is strongest; explicit dashboard hints outrank prose overlap.
- Clarify when the best score is below threshold or another dashboard/widget is within the ambiguity margin.
- `definition` may return documented, non-executable metrics without provider calls. Data intents require `executionStatus: executable` and an existing direct operation.

## Provider envelope

```json
{"httpStatus":200,"businessSuccess":true,"data":{},"schemaFingerprint":"sha256:...","semanticFingerprint":"sha256:...","appliedFilters":{},"provenance":{}}
```

Validate expected fingerprints and project only declared fields. A schema-valid empty dataset is allowed.

## QueryResult

Every result contains: `status`, `selection`, `resolvedParameters`, `bindingSource`, `fallbackUsed`, `normalizedData`, `presentation`, `provenance`, and `warnings`. Status is `success`, `partial`, `clarification_required`, `blocked`, `error`, or `dry_run`. Errors must not echo credentials or raw business rows.
