# Bid-Manager Benchmark

## Benchmark workspace

Primary benchmark workspace:

```text
/root/it-bidding-copilot/workspaces/my-bid-project
```

Primary benchmark project:

```text
CTZB-2023110453
```

## Canonical input sources

### Current tender
- `50-Inbox/01-Raw/current-tender/招标文件.docx`
- `50-Inbox/03-Processed/2023-12/current-tender/2023-12-06_招标文件_e5214c64.md`
- `20-Areas/Programming/Topics/2026-04/2023-12-06_浙江省财务开发有限责任公司私有云建设项目_深度解读.md`

### Historical bid
- `50-Inbox/01-Raw/historical-bid/商务技术文件.docx`
- `50-Inbox/03-Processed/2023-12/historical-bid/2023-12-08_商务技术文件_5585f28e.md`
- `20-Areas/Programming/Topics/2026-04/2023-12-08_浙江省财务开发有限责任公司私有云建设项目_深度解读.md`

### Curated knowledge
- `10-Knowledge/Evergreen/bid-qualification-and-certification-requirements.md`
- `10-Knowledge/Evergreen/case-zhejiang-finance-private-cloud-2023.md`
- `10-Knowledge/Evergreen/bid-project-experience-scoring-rules.md`
- `10-Knowledge/Evergreen/delivery-team-and-service-requirements.md`
- `10-Knowledge/Evergreen/solution-private-cloud-and-state-cloud-integration.md`

## Expected project-run artifacts

Under:

```text
20-Areas/Programming/Projects/ctzb-2023110453/
```

Expected artifacts:
- project workbench MOC
- project-start sheet
- tender parse summary
- evidence retrieval sheet
- score priority sheet
- mapping sheet
- outline placeholder
- missing-material checklist
- material assembly checklist
- chapter work files
- template material drafts

## Facts that must remain unresolved unless explicitly evidenced

Do not let `bid-manager` invent any of these unless they are explicitly found in the benchmark sources:
- final bidder entity
- current vendor/original-manufacturer selection
- current authorization file names
- current proof file names under `10-Knowledge/company-credentials/`
- certificate numbers not visible in the benchmark materials
- current capital amount or other company profile numbers
- tender packaging counts, copy counts, media submission counts
- current quote values
- current team names and staffing assignments

If any of the above are missing, the expected output is:
- `待补`
- `待核验`
- `未确认`

## Hard failure examples

These are treated as benchmark failures:
- writing file paths that do not exist in the workspace
- filling a template draft with specific values that are not evidenced
- asserting a vendor/platform choice that is not confirmed
- asserting “已核验/已完成/已拿到” when the source material does not prove it
- writing temporary project objects into `10-Knowledge/`
