# Card eligibility corrections and release verification

Base: `7044c7242ed2e077bef63393cfad232767f9aa84`. Initial PR: `d0d0dc1f7aea79e8f5e6a8b83bf9d720f1b49000`.

## Final behavior
- Familiar: 242 campaigns become 416 scoped offers, retaining all legacy favorite keys. Percentages 20/25/30, card eligibility, shared limits, QR conditions and 12/24 installment alternatives remain separate. Paraná has 30% Wednesday cashback, a Gs. 10m purchase cap and Gs. 3m refund cap; daily financing remains distinct.
- Continental Moet Hennesy: 20% ordinary / 25% Privilege, both with the official Gs. 2m monthly purchase cap. A Gs. 3m spend estimates Gs. 400k / 500k.
- Sudameris Concepts and Tatano: 20% ordinary / 25% Black and Infinite. Financing is independently classified, preserving Tatano's accommodation-only condition.
- Itaú Fuschia Palma: 20% base + 5% only with Visa through Google Pay or Apple Pay; 6 installments. DERMAGE: 30% base + 10% through those wallets; 10 installments. The calculator uses only the base rate and the official October schedule.
- Exact source-detail hashes gate the five reviewed corrections. Changed source text produces a warning and requires renewed review. Original text, source URL, review time and campaign identity remain available.
- Fixed two additional regressions found by full validation: dedup collision IDs retain their legacy hash; ordinal weekday order is deterministic. All 1,991 unrelated records, including timestamps and IDs, are byte-equivalent as JSON objects to the original published catalog. All nine source files and unrelated source metadata are preserved.

## Evidence
The existing same-day Familiar snapshot was retained. Nineteen official fetches, including all seven discrepancy PDFs, are recorded in [source verification](promotion-source-verification-2026-10-07.json). Rechecked PDFs match their captured SHA-256 hashes. No partial-source regeneration was used.

The full regenerated catalog has 2,417 rows. Seven Familiar campaigns retain listing/PDF rate discrepancies: Coloso, Las Hortensias Hotel, Óptica Santa Lucía, Denoir-Shopping Mariscal, Farmatitu, Farmacia Zulmi and Essen. The UI shows explicit warnings and the PDF clauses; disputed rows do not produce numeric estimates or automated benefit notifications. Óptica Santa Lucía remains unsplit with a review reason. Other previously withheld Familiar records remain in the source review queue; no unsupported coverage was invented.

## Validation
- `npm ci` completed with the repository lockfile.
- `npm test`: 54 passed, 0 failed. Includes actual Web Push encryption/provider-response simulation, duplicate prevention, revoked subscriptions, atomic account-scoped favorite updates, rapid clicks, rollback and campaign notification grouping.
- `python -m unittest discover -s tests -p 'test_*.py'`: 48 passed, 0 failed.
- `npm run build`: passed for frontend and backend.
- Full source regeneration: `python scrapers/build_familiar_table.py`, then `python promo_backend/normalize.py`.
- Playwright Chromium UI at 390px and 1440px: Paraná rate/caps/12-24 installments, Familiar tiers and QR, Moet calculator, Sudameris discounts/financing, Itaú wallet conditions, favorite campaign writes, search reset/day filters and notification profile. No JavaScript errors or horizontal overflow.
- UI authentication and account API were simulated locally; no real account or push subscription was modified. Live Google OAuth completion and display of a push on a physical phone are not claimed.
- Profile tests now load the production favorite-key helper. Universitaria's saved-output test compares the current refresh audit (72 offers) rather than a different historical fixture (89 offers); its independent fixed-source tests remain intact.

## Publication
Publication was explicitly authorized after the initial draft. GitHub Pages and the existing Sites backend must use the validated changes together. This document records validation; deployment completion and the final commit are reported separately after the official workflows succeed.
