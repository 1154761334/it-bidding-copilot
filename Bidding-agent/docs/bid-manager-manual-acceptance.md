# Bid-Manager Manual Acceptance

## Goal

Use this checklist to validate that `bid-manager` is producing stable project-run artifacts, not just chat replies.

## Recommended command

```bash
cd /root/it-bidding-copilot/workspaces/my-bid-project
hermes chat -s /root/it-bidding-copilot/Bidding-agent/skills/bid-manager/SKILL.md
```

Recommended post-run check:

```bash
cd /root/it-bidding-copilot/Bidding-agent
bash scripts/check-bid-manager-output.sh /root/it-bidding-copilot/workspaces/my-bid-project ctzb-2023110453
```

Recommended full benchmark run:

```bash
cd /root/it-bidding-copilot/Bidding-agent
bash scripts/run-bid-manager-benchmark.sh /root/it-bidding-copilot/workspaces/my-bid-project ctzb-2023110453
```

## Required project-run artifacts

After a meaningful run, confirm these project files exist or are updated under:

```text
20-Areas/Programming/Projects/<project-id>/
```

Required files:
- project workbench MOC
- project-start sheet
- tender parse summary
- evidence retrieval sheet
- score priority sheet
- score-point / chapter / evidence mapping
- outline placeholder
- missing-material checklist
- material assembly checklist
- at least one template-type material work draft

## Template-type materials to verify

At least one of these must be updated during a run:
- legal-form draft
- deviation response sheet
- quote explanation draft
- presentation outline draft

## Manual review focus

### 1. Template compliance
- Does the output follow the tender's required material shape?
- Are required fields preserved?
- Are unresolved placeholders explicit?

### 2. Ownership boundary
- Are bidder-owned and vendor-owned capabilities separated?
- Is vendor/platform evidence kept out of bidder self-owned claims?

### 3. Historical-vs-current boundary
- Does the output clearly distinguish:
  - historical evidence
  - current tender requirements
  - current project missing materials

### 4. Evidence discipline
- Are claims tied to evidence sources?
- Are missing or stale materials marked explicitly?
- Does the output avoid pretending missing evidence exists?
- Do all referenced file paths actually exist in the workspace?

### 5. Benchmark discipline
- Does the output keep unresolved facts as `待补 / 待核验 / 未确认`?
- Does it avoid fabricating vendor names, company profile numbers, and packaging counts?

## Fail conditions

Treat the run as failed if any of these happen:
- no project-run files are updated
- it outputs only chat text and no artifacts
- it writes temporary project objects into `10-Knowledge/`
- it presents historical facts as current confirmed facts
- it mixes bidder and vendor capability ownership
- it skips mapping and goes directly to polished prose
- it references file paths that do not exist
- it fills benchmark-unresolved facts with fabricated concrete values
