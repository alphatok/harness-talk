# Extraction and field mapping

## Contents

- Extraction contract
- Presales questionnaire mapping
- Multimodal guidance
- Required update outputs

## Extraction contract

For every source, produce candidate Claims before running `merge_claims.py`. Preserve exact facts but paraphrase long copyrighted text. Include source references and location details in `notes` when available.

Never fill gaps for completeness. Represent unknowns as open questions, not invented values. Separate customer statements, verified public facts, supplier evidence, observations, inferences, and hypotheses.

## Presales questionnaire mapping

Map the 22-item questionnaire to predicates:

| Questionnaire area | Predicate prefix | Default scope |
|---|---|---|
| Main business, scale, position | `organization.*` | client |
| Prior AI initiatives and current systems | `current_state.*` | client |
| Current need and pain | `needs_and_value.*` | opportunity when tied to one pursuit |
| Trigger and success criteria | `needs_and_value.trigger_events`, `needs_and_value.success_criteria` | opportunity |
| Data, users, workflow, error impact | `delivery_readiness.*` | opportunity/project |
| Customer execution resources | `delivery_readiness.customer_resources` | opportunity |
| Deployment, network, compliance, compute | `delivery_readiness.*_constraints` | opportunity/project |
| Integration systems and vendor support | `delivery_readiness.integration_readiness` | opportunity/project |
| Budget, procurement, payment | `opportunity.budget`, `opportunity.procurement` | opportunity |
| Timeline and competition | `opportunity.timeline`, `opportunity.competition` | opportunity |
| Attachments received/requested | `sales_strategy.attachments` | opportunity |

## Multimodal guidance

- Images and whiteboards: inspect visually, capture uncertain OCR text as `unverified`, and retain the image source reference.
- Meeting transcripts: distinguish speaker statements; do not attribute a statement when speaker identity is uncertain.
- Email and chat: preserve sender, sent time, and thread context.
- Public research: record page publication/update date separately from capture date; supplier claims do not prove current use.
- Manual correction: use `correction`, include the reviewer, reason, and `supersedes` IDs.

## Required update outputs

Every update must state:

1. Sources registered.
2. Claims proposed, accepted, rejected, or conflicted.
3. Current conclusions changed and why.
4. Stale or missing critical information.
5. Suggested validation questions and next actions.
