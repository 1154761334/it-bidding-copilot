# Company Knowledge Vault

This is the recommended permanent knowledge store for the bidding entity.
All project workspaces may read from this vault; project-specific tender inputs and generated artifacts do not belong here.

## Structure

- `raw/` — immutable source materials (historical bids, credentials, vendor docs)
- `wiki/` — curated, promoted knowledge pages
- `.env` — OVP API configuration

## Boundary

- Put reusable company credentials, historical bid patterns, vendor capability notes, and approved evergreen knowledge here.
- Keep current project tender packages under `workspaces/<project>/50-Inbox/01-Raw/current-tender/` or the `/bid` upload flow.
- Do not commit this vault when it contains customer materials, certificates, screenshots, contracts, prices, signatures, or private vendor files.
- Promote project facts into this vault only after human review confirms they are reusable and not project-confidential.
