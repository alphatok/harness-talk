# Operations

## Contents

- Initialize
- Register a source
- Propose and apply Claims
- Materialize and render
- Validate
- Manual correction

## Initialize

```bash
python scripts/init_workspace.py --workspace /absolute/path/to/workspace --owner "Owner"
python scripts/init_client.py --workspace /absolute/path/to/workspace --client-id acme --display-name "Acme" --owner "Owner"
python scripts/init_scope.py --workspace /absolute/path/to/workspace --client-id acme --type opportunity --id knowledge-base-2026 --name "Knowledge Base 2026"
```

## Register a source

```bash
python scripts/register_source.py --workspace /absolute/path/to/workspace --client-id acme --type meeting_minutes --title "Discovery meeting" --path /absolute/path/to/notes.md --provider "Sales" --authority customer_business --sensitivity confidential --copy-original
```

Use the returned `source_id` in candidate Claims.

## Propose and apply Claims

Write a JSON array or JSONL candidate file. First run without `--apply`:

```bash
python scripts/merge_claims.py --workspace /absolute/path/to/workspace --client-id acme --candidates /absolute/path/to/candidates.json
```

Review the proposed append/reject result. Apply only when the user authorized the update:

```bash
python scripts/merge_claims.py --workspace /absolute/path/to/workspace --client-id acme --candidates /absolute/path/to/candidates.json --apply
```

## Materialize and render

```bash
python scripts/materialize_profile.py --workspace /absolute/path/to/workspace --client-id acme
python scripts/freshness_check.py --workspace /absolute/path/to/workspace --client-id acme --apply
python scripts/render_views.py --workspace /absolute/path/to/workspace --client-id acme
```

## Validate

```bash
python scripts/validate_workspace.py --workspace /absolute/path/to/workspace --client-id acme
python /path/to/skill-creator/scripts/quick_validate.py /path/to/maintain-client-profile
```

## Manual correction

Register the correction text as a source. Create a `correction` Claim, set `supersedes` to the old Claim IDs, and use the same subject and predicate where appropriate. Apply, rematerialize, run freshness, render, and validate. Never edit the old JSONL line in place.
