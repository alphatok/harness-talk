# Directory layout

## Contents

- Workspace
- Client
- Opportunity
- Project
- Placement rules

## Workspace

```text
workspace/
├── workspace.json
├── schemas/
├── policies/
├── registry/clients.json
└── clients/<client-id>/
```

Run `scripts/init_workspace.py`, then `scripts/init_client.py`. Keep reusable policies and schemas at workspace scope; keep client facts only below the client directory.

## Client

```text
clients/<client-id>/
├── client.json
├── profile/current.json
├── claims/*.jsonl
├── stakeholders/
├── interactions/
├── research/
├── sources/index.jsonl
├── opportunities/
├── projects/
├── reviews/
├── views/
├── changes/
└── archive/
```

## Opportunity

```text
opportunities/<opportunity-id>/
├── opportunity.json
├── profile.json
├── claims.jsonl
├── interactions/
├── deliverables/
├── views/
└── changes/
```

Create it with `scripts/init_scope.py --type opportunity`. Close it by updating status to `won`, `lost`, `suspended`, or `abandoned`; do not delete it.

## Project

```text
projects/<project-id>/
├── project.json
├── profile.json
├── claims.jsonl
├── requirements/
├── decisions/
├── meetings/
├── deliverables/
├── acceptance/
├── sources/
├── views/
├── changes/
└── closure/
```

Create it with `scripts/init_scope.py --type project --origin-opportunity <id>`. Do not rename a won opportunity into a project.

## Placement rules

Store originals once. Scope every Claim. Never copy long-lived company facts into each opportunity. Never promote a one-project constraint to the whole client without review.
