# Data model

## Contents

- Canonical files
- Source
- Claim
- Current profile packet
- Client, opportunity, and project boundaries
- Conflict behavior

## Canonical files

Use UTF-8 JSON for snapshots and JSONL for append-only ledgers. Do not treat HTML or Markdown views as writable facts.

- `client.json`: durable client identity and owner.
- `sources/index.jsonl`: registered source ledger.
- `claims/*.jsonl`: client-level claim ledgers.
- `opportunities/<id>/claims.jsonl`: opportunity-only claims.
- `projects/<id>/claims.jsonl`: delivery-project-only claims.
- `profile/current.json`: materialized current client snapshot.
- `views/*.html`: derived, replaceable views.

JSON is the executable default because the bundled scripts have no third-party dependency. If users prefer YAML, convert only at the presentation/editing boundary and keep JSON/JSONL canonical unless a reliable YAML validator is available.

## Source

Register every material before accepting claims from it. Include source ID, client ID, type, title, URI, content hash when local, captured time, event time, provider, authority, and sensitivity. Preserve originals when authorized; otherwise keep a stable URI and hash.

Do not treat a source as universally authoritative. Judge authority against the predicate: procurement can confirm budget process; business owners can confirm pain; IT can confirm interfaces; vendor marketing can only establish a supplier-side claim.

## Claim

Make each Claim one minimal, independently reviewable statement. Required fields are defined in `claim.schema.json`.

Use these types exactly:

- `verified_fact`: official or strongly corroborated fact.
- `customer_statement`: explicit customer statement; preserve speaker context.
- `supplier_evidence`: vendor or partner-side evidence.
- `internal_observation`: named internal observer's record.
- `inference`: reasoned conclusion from other claims.
- `hypothesis`: proposition to validate; attach a validation question in notes.
- `correction`: explicit human correction; reference superseded claim IDs.

Use dotted business predicates. Prefer stable names such as:

- `organization.main_business`
- `relationships.decision_chain`
- `current_state.systems`
- `needs_and_value.pain_points`
- `delivery_readiness.deployment_constraints`
- `sales_strategy.open_questions`
- `opportunity.budget`
- `opportunity.competition`
- `project.scope`

## Current profile packet

Materialized fields are not naked values. Keep `value`, `status`, `confidence`, `claim_type`, `claim_refs`, `source_refs`, `as_of`, `expires_at`, `owner`, and freshness information together.

## Client, opportunity, and project boundaries

- Put durable company facts and cross-opportunity relationships at client scope.
- Put budget, buying stage, competitors, POC requirements, and opportunity-specific decision roles at opportunity scope.
- Put contracted scope, requirement changes, delivery decisions, milestones, risks, and acceptance at project scope.
- Store an interaction once under the client and reference its ID from scopes.
- Promote project learning to client scope only through a reviewed new Claim.

## Conflict behavior

Never delete history. Use `supersedes` for explicit replacement. If equally authoritative active Claims disagree without a supersedes link, materialize a conflict with alternatives and write it to `reviews/conflicts.json`. Do not guess a winner.
