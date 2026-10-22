---
name: maintain-client-profile
description: 客户跟了很久，资料还散在纪要、邮件和文件里？提供已有材料，把客户、商机与项目整理成可追溯档案，记录来源、需求变化、历史修正和待确认项，生成客户概览与证据视图。减少重复问询、交接遗漏和沿用过期信息。用法：“根据这份纪要更新客户档案，保留旧记录，标出变化和下次要问的问题。”档案保存在指定工作区，分享时按资料权限处理。
metadata:
  version: "1.0.0"
---

# 客户档案管家｜资料归档、变化追踪

先提供客户名称、资料和本次工作目录。此包只含空白模板和工具，不含客户名录、联系人或历史会议数据。新档案放到用户指定工作区，不写回安装目录。

Python 3.10+，工具使用标准库。脚本示例从当前技能目录执行，或把 `scripts/` 替换为实际技能路径。内部协作视图与对外视图分别处理；对外视图仍需核对公开范围。

Maintain a durable client-intelligence workspace. Preserve sources and append-only Claims, materialize current snapshots, and generate replaceable human views. Never treat a generated report as the fact store.

## Core rules

1. Store one client per directory.
2. Separate `client`, `opportunity`, and `project` scopes.
3. Register a source before accepting Claims from it.
4. Separate verified facts, customer statements, supplier evidence, internal observations, inferences, hypotheses, and corrections.
5. Never infer a negation from silence or fill unknowns for completeness.
6. Preserve history. Replace conclusions with `supersedes`; do not edit old JSONL lines.
7. Treat the current profile as a derived snapshot that can be rebuilt.
8. Default to `propose` before applying extracted Claims. Apply only when the user asked to create/update/maintain the profile or approved the proposal.
9. Surface authoritative conflicts for human review instead of guessing.
10. Keep internal strategy, personal data, budgets, and meeting records out of external views unless explicitly authorized.

## Read references progressively

- Read [data-model.md](references/data-model.md) before creating Claims, resolving conflicts, or changing the profile structure.
- Read [directory-layout.md](references/directory-layout.md) before initializing a workspace, client, opportunity, or project.
- Read [extraction-mapping.md](references/extraction-mapping.md) when processing source materials or mapping the 22-item presales questionnaire.
- Read [operations.md](references/operations.md) before running the bundled scripts.
- Consult `*.schema.json` and policy JSON files only when validating fields or changing governance rules.

## Workflow

### 1. Establish scope

Identify:

- workspace path;
- client name and stable lowercase `client_id`;
- information scope: client, opportunity, or project;
- source context and event date;
- requested mode: analysis-only, propose, or apply;
- sensitivity and intended audience.

Do not mix opportunity facts into the client-wide profile. If scope is unclear but the material refers to a specific pursuit, keep it at opportunity scope and flag the assumption.

### 2. Initialize only what is missing

Use the scripts documented in [operations.md](references/operations.md). Initialize the workspace, then one client directory. Create opportunity or project directories only when the business object exists.

Use JSON/JSONL as canonical machine storage. Keep Markdown and HTML as derived views.

### 3. Register each source

Register local files, URLs, meeting records, images, corrections, or exports with `register_source.py`. Preserve event time separately from capture time. Use content hashes to prevent duplicate local material.

For images, screenshots, or whiteboards, inspect the image before extracting Claims. For PDFs, spreadsheets, documents, audio transcripts, or web pages, use the appropriate available capability to read the material, then register the source. Do not claim OCR certainty when text is unclear.

### 4. Extract minimal candidate Claims

Create one independently reviewable statement per Claim. Use a JSON array or JSONL file. Example:

```json
[
  {
    "client_id": "acme",
    "domain": "needs-and-value",
    "scope": {"type": "opportunity", "id": "knowledge-base-2026"},
    "subject": "opportunity.knowledge-base-2026",
    "predicate": "needs_and_value.pain_points",
    "value": ["Product answers vary across channels"],
    "claim_type": "customer_statement",
    "status": "probable",
    "confidence": 0.85,
    "source_refs": ["src-abc123"],
    "observed_at": "2026-08-08",
    "sensitivity": "confidential",
    "notes": "Customer business owner; meeting paragraph 12"
  }
]
```

For every inference or hypothesis, include supporting Claim IDs or source refs in `notes` and add a validation question. Do not label supplier marketing as verified current use.

### 5. Propose, inspect, then apply

Run `merge_claims.py` without `--apply`. Review rejections, duplicate detection, missing sources, scope, type, confidence, and sensitivity.

When authorized, rerun with `--apply`. A successful append is not completion: materialize, check freshness, render, and validate.

### 6. Materialize and reconcile

Run `materialize_profile.py`. Let explicit corrections and `supersedes` links replace older conclusions. When equally ranked active Claims disagree, retain alternatives and add a conflict review item.

Run `freshness_check.py --apply`. Stale means “reconfirm,” not “delete.” Use field-level TTL rules.

### 7. Render views

Run `render_views.py` to produce:

- `views/client-overview.html` for the current profile and active opportunities;
- `views/evidence-audit.html` for Claim/source traceability.

Generate an external/shareable view only when asked. Exclude internal observations, inferences, hypotheses, restricted data, relationship ratings, and win strategy by default.

### 8. Validate and report

Run `validate_workspace.py`. Report:

- sources registered;
- Claims proposed, appended, rejected, superseded, or conflicted;
- current conclusions changed and why;
- stale and missing decision-critical information;
- next validation questions and actions;
- exact paths to canonical profile and rendered views.

Do not call the profile current if validation fails or unresolved high-impact conflicts are hidden.

## Human corrections

Treat direct human correction as a new `manual_correction` source plus a `correction` Claim. Include reviewer, reason, and `supersedes` IDs. Preserve the old Claim. If the user corrects a role but not the person's identity, update the known role and leave identity unknown.

## Public research

When current public research is requested, browse and cite authoritative sources. Distinguish confirmed company facts, supplier-side evidence, historical or possibly stale evidence, and open questions. Use a research source record per page or coherent source artifact. Reverify people, vendors, metrics, and current-use claims before applying them.

## Relationship to client-intel

Use `client-intel` for a full first-contact company investigation and collaboration strategy when that skill is available and the user requests it. Import its outputs here as registered sources and typed Claims; do not copy its narrative conclusions into the profile without evidence mapping.

## Deterministic scripts

The scripts use the Python standard library only:

- `init_workspace.py`: create shared schemas, policies, templates, and registry.
- `init_client.py`: create one durable client directory.
- `init_scope.py`: create one opportunity or delivery project.
- `register_source.py`: register and optionally preserve an original source.
- `merge_claims.py`: validate and propose/apply candidate Claims.
- `materialize_profile.py`: rebuild current snapshots and conflict records.
- `freshness_check.py`: evaluate and optionally write field freshness.
- `render_views.py`: generate self-contained HTML views.
- `validate_workspace.py`: check records, IDs, source references, and directory integrity.

Read [operations.md](references/operations.md) for exact commands.
