---
name: payback-operations
description: Maintain Payback PY promotions, favorites, notifications and admin. Use for this repository's data audits and targeted fixes, not other apps.
---

# Payback PY

Start with `git status --short` and `python scripts/audit_catalog.py`. For one merchant use `--merchant "Punto Farma"` and optionally `--bank "Universitaria"`. Output is bounded; use `--detail` only for the affected records.

## Read only the affected layer
- Source extraction: `scrapers/extract_<bank>.py`, bank CSV under `outputs/`.
- Shared normalization: `promo_backend/normalize.py`; dates, caps and dedup: `promo_backend/quality.py`.
- Rendering, grouping and filters: locate function names in `app-web/app.js` before reading a bounded range.
- Favorites/Google: `app-web/beta-client.js`, `server/beta.js`.
- Push: `server/index.js`, `server/schedule.js`, `scripts/dispatch_notifications.py`, `.github/workflows/favorite-notifications.yml`.
- Admin: `app-web/admin.html` and `admin-client.js`. No app navigation link. Server verifies Supabase identity and BETA_ADMIN_EMAILS; never replace this with a client-side email check.

## Non-obvious invariants
- Stable promotion IDs include source_url. Keep machine provenance stable; user-facing sources use source_page_url.
- Reviewed overrides in `data/reviewed_benefits.json` require exact raw-detail hash. Reverify when the source changes.
- Purchase caps are not refund caps. Preserve card/payment/product qualifiers and 'hasta'. Financing-only cards never enter today's discounts.
- Group PDF campaigns into actual merchants; never label a shopping center as the merchant unless the source explicitly applies center-wide.
- Familiar/GNB `*_extraction_review.json` files are staging, not published coverage. Review conditions and dates before adding catalog sources.
- Push `sent` means provider acceptance, not display on the phone. Never reset uncertain deliveries just to retry. Never log subscription endpoints, tokens or keys.
- Analytics counters require consent; no search text or coordinates.

## Verification and publication
- `npm test`; `python -m unittest discover -s tests -p 'test_*.py'`.
- After source changes: `python promo_backend/normalize.py`, then targeted audit and tests.
- `npm run build` generates ignored auth/admin bundles; Pages builds them in CI.
- Browser check at 390px and desktop: no horizontal overflow, search reset, correct date filters, accessible icon buttons.
- GitHub Pages and the Sites notification backend are separate deployments. Read `.openai/hosting.json` for the exact existing Sites project; use native Sites deployment tools. Never recreate the service.
- Fetch before pushing: daily data workflows update main. Do not overwrite their changes.

Report verified outcomes separately from unverified or blocked items. Keep command output focused on counts, failures and affected records instead of dumping catalogs or minified bundles.
