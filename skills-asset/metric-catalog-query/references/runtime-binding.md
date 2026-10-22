# Runtime binding

Templates carry stable meaning; instance bindings carry scope-specific dashboard, release, widget, dataset, and option IDs. Never treat `widgetId` alone as globally unique.

## Modes

`reuse` first tries the current-scope binding, then a reusable template candidate. Validate business success, schema/semantic fingerprints, filters, and projection. Only binding-not-found or schema/semantic drift may trigger targeted progressive discovery and one retry. Never fallback for 401/403, rate limit, network failure, or arbitrary server errors.

`progressive` always discovers only the selected dependency path and ignores reusable IDs. An adapter may update the current instance cache, but must not rewrite public templates or Markdown.

## Adapter protocol

```python
discover(selection, context) -> binding
execute(operation, parameters, binding, context) -> response_envelope
resolve_option(resolver, label, binding, context) -> wire_value  # optional
persist_binding(selection, binding, context) -> None              # optional, instance cache only
```

The CLI supports fixtures and `module:function` factories. Context stays in memory. Public templates store resolver contracts, not merchant labels/IDs. Ambiguous or absent dynamic values stop before the data request.
