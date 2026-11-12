# Staged promotion, not enabled

`npm run build` remains unchanged. It still publishes the existing official UI and the new beta UI separately.

To stage a candidate **after a fresh build**: `node scripts/prepare-official-candidate.mjs`.

The staging step places the beta visual shell at the existing `/app-web/` URL, retaining the official account bundle, API configuration, notification client and push handlers, legal pages, admin files, and exact installed-PWA manifest. A rollback copy of the previous shell is retained in the staging directory. It never touches D1, user records, tokens, or browser storage.

The candidate translates local display keys back to the existing `paybackPy.*` namespace and preserves the `/beta/` application and `paybackPyBeta.*` storage unchanged. Beta-only local favorites are **not synchronized or automatically merged** into the official account. They remain accessible via beta; an explicit, account-bound import UI is still needed if migration of those selections into D1 is desired. Do not promise a unified favorite set yet.

Do not copy the isolated beta account client over production: it intentionally rejects writes and stores favorites locally. Do not change OAuth redirect or storage identity. Do not remove beta or replace it with a redirect while its local selections still need recovery.

## Remaining release gates
- Browser review at desktop and 390px, including filters, date changes, reset, detail close/back, account cancellation and unavailable API.
- Actual OAuth login/cancel/sign-out at `/app-web/`, preservation of one existing account's favorites, and account isolation. Avoid modifying real data just for tests.
- Installed PWA update and push behavior on a real device; preserving manifest identity does not itself prove update success.
- Resolve source health and validation discrepancies reported by the separate catalog audit.
- Make publication wiring an explicit reviewed change only after these gates. This script is deliberately absent from `build.mjs` and the deployment workflow.
