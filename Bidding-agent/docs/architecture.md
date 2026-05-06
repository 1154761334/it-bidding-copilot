# Architecture

## Product goal

Deliver a Hermes-native bidding system that feels like one professional bid manager, while internally coordinating specialized execution roles and reading from an Obsidian/OVP knowledge layer.

## External shape

User sees only:
- one skill: `bid-manager`
- one identity: 投标经理 Agent

The user should not have to decide which internal role to invoke.

## Internal roles

### 1. Manager agent
Responsibilities:
- project intake
- role identification
- package/lot confirmation
- clause and scoring gate control
- evidence and outline gate control
- sub-agent dispatch decisions
- final review and release decision

Must not:
- default to writing all chapters itself on complex projects
- allow formal delivery before gates are satisfied

### 2. Evidence agent
Responsibilities:
- organize bidder credentials
- organize vendor/original-manufacturer materials
- structure evidence pages
- classify evidence ownership
- produce missing-evidence checklist

Must not:
- write major technical solution chapters
- claim vendor capability as bidder-owned capability

### 3. Technical agent
Responsibilities:
- demand response
- solution chapters
- deployment, implementation, migration, service, and operation chapters
- use three writing modes:
  - vendor-led capability sections
  - integrator-led implementation sections
  - collaborative sections

Must not:
- alter the approved outline on its own
- over-commit beyond approved risk boundaries

### 4. Review agent
Responsibilities:
- clause coverage review
- score-point coverage review
- evidence linkage review
- bidder-vs-vendor boundary review
- over-commitment review
- formal-delivery hygiene review

Must not:
- replace manager decisions on project strategy

## Knowledge model

The system assumes an Obsidian-style vault:

```text
bid-vault/
├── inbox/
├── raw/
├── wiki/
├── output/
└── logs/
```

Meaning:
- `inbox/` = current project input folders and project-only supplements
- `raw/` = immutable reusable source material bundles
- `wiki/` = compiled knowledge pages and reusable objects
- `output/` = project-specific execution artifacts
- `logs/` = lint, review, and operational traces

Boundary:
- current tender packages are project-run inputs
- reusable bidder/vendor knowledge belongs in `raw/` and promoted `wiki/` pages
- the tender package itself is not the default canonical long-term knowledge object

## Core product objects

Minimum durable objects:
- project input manifest
- project-start sheet
- pack/package parse page
- score-point / chapter / evidence mapping page
- evidence page
- chapter placeholders
- chapter drafts
- review report
- formal-delivery package checklist

## Manager state machine

1. project folder intake
2. startup intake
3. workspace validation
4. current tender parse
5. reusable-knowledge retrieval
6. evidence organization
7. outline generation
8. user confirmation gate
9. drafting
10. independent review
11. formalization
12. export/backflow

## Gate rules

The following gates are non-optional:
- no multi-pack continuation before target pack confirmation
- no drafting before outline confirmation
- no formal qualification statement without evidence
- no fake page numbers for unfinished sections
- no internal process notes in formal delivery
- no mixing bidder capability and vendor capability
- no treating the current tender package as default reusable knowledge

## Why this is not just a writing workflow

This system is designed for real tender production, not only language generation.
It must manage:
- current project input vs long-term knowledge boundaries
- evidence assembly
- evaluation alignment
- rejection-risk control
- role boundary control
- knowledge reuse across projects
