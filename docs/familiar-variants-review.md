# Familiar eligibility variants: review and release gate

Base: `7044c7242ed2e077bef63393cfad232767f9aa84`.
Official-source snapshot: `outputs/familiar_extraction_review.json`, checked 2026-10-07 14:25:05 UTC. The live Familiar listing and Paraná terms landing page were checked again; individual PDF text comes from the repository's same-day official-source capture.

## Change
- Split explicitly evidenced card clauses instead of displaying a 20–25% range. Support two or three tiers and keep each tier's cards and purchase limits.
- Keep conditional QR bonus in its eligibility row, explicitly requiring Banco Familiar's app. Display estimated base savings, not unconditional QR-enhanced savings.
- Separate shared cashback from 12/24-installment alternatives and preserve each clause's schedule. Paraná retains 30% Wednesday cashback, purchase cap Gs.10m and refund cap Gs.3m, plus separate daily financing rows. The old UI failed to read `30% (Treinta) de reintegro`.
- Never show cash savings on a financing-only row. For legacy unstructured card variants whose cap cannot be scoped, show an explicit unconfirmed-cap message instead of an uncapped estimate.
- Preserve the legacy promotion ID as `campaign_id`; favorites and notifications use campaign identity. Account consolidation is atomic and account-scoped; notifications group only eligible variants for the requested day.
- Keep unresolved previously verified offers visible and report the segmentation issue. Óptica Santa Lucía remains unchanged, flagged for review because it combines product-specific checkout discounts and cashback.

## Source coverage checked in a disposable copy
242 Familiar campaigns remain covered, with no campaign lost. 159 expand into variants, producing 416 total offers. All 242 old favorite identities resolve. Full local normalization produced 2,412 rows across banks; it was a verification artifact, not committed production data.

The listing and PDF are not always identical. Coloso advertises 30/20 on the listing while its captured PDF says25/20; Las Hortensias has three PDF tiers20/25/30 despite a simpler listing. This patch uses the PDF clauses, as the existing pipeline does. These discrepancies need source-owner review before release. Other listing/PDF percentage differences were observed for Óptica Santa Lucía, Denoir-Shopping Mariscal, Farmatitu, Farmacia Zulmi and Essen.

## Tests verified
36 focused Node tests and17 Python tests passed:

```
node --test tests/favorite-campaigns.test.cjs tests/navigation-favorites.test.cjs tests/beta.test.cjs tests/push-client.test.cjs tests/familiar-presentation.test.cjs tests/classification.test.cjs tests/additive-benefit.test.cjs tests/benefits.test.cjs tests/today-sections.test.cjs
python -m unittest discover -s tests -p 'test_familiar_offers.py'
python -m unittest discover -s tests -p 'test_favorite_campaigns.py'
```

`node --check` passed for app.js, beta-client.js and all three changed server files. Regression coverage includes rate/eligibility/cap separation, QR, mixed financing, shared limits, single/multiple/range weekday expressions, stable IDs, legacy favorites, account isolation, click rollback and notification grouping.

Presentation regressions use a small fixture generated from the same official-source snapshot. They do not require already-regenerated production data. Python tests derive the source offers from the existing extraction snapshot.

Full `npm test` was attempted: the schedule and push-dispatch test files could not load because esbuild is absent in the verification environment. The broader Python quality test could not load because requests is absent. Full build, browser QA and actual push delivery have not been verified. Do not interpret focused green tests as a full release pass.

## Required before merge/release
Generated CSV and public catalogs are intentionally not committed: the verification copy does not have all original metadata for the other banks, so publishing its complete catalog would overwrite unrelated provenance.

1. In the authoritative checkout, fetch latest main and preserve its source-status/metadata. Reverify the affected Familiar PDF/listing discrepancies and the existing pending-source queue.
2. Regenerate only Familiar's table from the reviewed current official snapshot, then normalize with all authoritative source files and metadata present:

```
python scrapers/build_familiar_table.py
python promo_backend/normalize.py
python scripts/audit_catalog.py --bank Familiar
```

3. Inspect the generated diff: preserve all existing bank metadata, 242 Familiar campaign identities for this snapshot, and unchanged unresolved offers. Add those generated artifacts to the branch after verification.
4. Install the repository's locked Node dependencies and Python requirements in the normal environment; run `npm test`, `python -m unittest discover -s tests -p 'test_*.py'`, and `npm run build` against final code/data.
5. Verify mobile390px and desktop UI, ordinary/premium sections, day filters, cards, favorites across sign-in and repeated clicks, cap messages and QR explanations. Verify notification payloads and delivery in the normal test setup.
6. Frontend, notification backend and catalog must be released together under explicit release approval. This draft PR does not merge or deploy anything.

## Other-bank findings not blanket-fixed
- Continental Moet Hennesy: legacy variant calculation discarded the2m purchase cap and returned600k/750k for a3m spend instead of400k/500k. The new safety guard suppresses this unverified estimate; full numeric restoration requires scoped eligibility/cap extraction.
- Sudameris Concepts La Cuadrita, Tatano and Le Bistro lose Black/Infinite25% under the legacy percentage heuristic; mixed financing can be misclassified. Their source mappings require a separate verified correction.
- Itaú Fuschia Palma shows25% unconditional despite20%base+5%Visa wallet; another Fuschia offer shows40% instead of30%base+10%wallet. Verify current source terms and model the conditional channel before changing those figures.

These were reproduced from repository data/code; current external pages for those banks were not refreshed. GNB's20/25 base/QR rows are already structured and must not be split again blindly.
