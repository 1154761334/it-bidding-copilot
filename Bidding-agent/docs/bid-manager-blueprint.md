# Bid-Manager Blueprint

## Product goal

`bid-manager` is a bidding workflow agent, not a generic writing bot.
Its job is to:
- parse the current tender
- retrieve reusable evidence
- plan score coverage
- draft chapter work files
- review and formalize deliverables

## Core modules

### 1. Tender Parser
Inputs:
- current tender source notes
- current tender deep dives

Outputs:
- project-start summary
- package/lot confirmation
- qualification checklist
- rejection-risk checklist
- score item list
- required deliverable structure

### 2. Evidence Retriever
Inputs:
- `10-Knowledge/`
- reusable deep dives and source notes
- project-specific tender clauses

Outputs:
- evidence retrieval sheet
- ownership classification
- missing-evidence list

### 3. Score Planner
Inputs:
- parsed score items
- evidence retrieval results

Outputs:
- score priority sheet
- score-point / chapter / evidence mapping

### 4. Draft Composer
Inputs:
- approved outline
- chapter work files
- evidence candidates

Outputs:
- internal chapter drafts
- chapter-level unresolved questions
- chapter-level evidence dependencies

### 5. Compliance Reviewer
Inputs:
- draft chapters
- mapping sheet
- tender requirements

Outputs:
- review checklist
- blocker list
- formalization readiness judgment

## Input contract

### Current project input
- `50-Inbox/01-Raw/current-tender/<project-id>/...`
- `50-Inbox/03-Processed/.../current-tender/*.md`
- tender deep dives under `20-Areas/...`

### Reusable knowledge
- curated pages under `10-Knowledge/Evergreen/`
- historical deep dives
- processed historical source notes

## Output contract

Project-run artifacts should live under:

```text
20-Areas/Programming/Projects/<project-id>/
```

Minimum project-run artifacts:
- project workbench MOC
- project-start sheet
- tender parse summary
- evidence retrieval sheet
- score priority sheet
- score-point / chapter / evidence mapping
- outline placeholder
- chapter work files
- missing-material checklist
- review report

## Non-negotiable rules

- no formal claim without evidence
- no mixing bidder-owned and vendor-owned capability
- no drafting before outline and mapping exist
- no current tender text promoted into long-term reusable facts by default
- no internal work notes leaked into formal delivery files
