# BNF / GNB source repair — 2026-10-30

## Root causes and bounded verification

- BNF `extract_bnf` rejected an explicitly expired October pharmacy PDF, aborting the entire bank. It now preserves historical rows with their exact end dates, while unknown validity still fails. No dates are renewed. Actual complete scraper run 15:52:42Z fetched the public catalog and all five linked PDFs; 77 rows, byte-identical to the previous CSV. Metadata records document SHA256, end date, expiry and branch counts.
- GNB `build_gnb_reviewed` aborted the whole bank on card 688 (Casa Rica prize draw), because it was not a quantified discount. Official API fetched HTTP200 on 30/10 (~15:48Z): 254 cards versus 252 previously. Added 688, 689 Ulix, 74 Geox; removed 683 Theoni Experience. Three exact semantic reviews are now in `data/gnb_source_reviews.json`. Decisions are bound to card content; each builder run also re-fetches and validates their official PDF hashes. Changed terms fail closed, not silently reused.
- Casa Rica 688 is an extra prize-draw coupon for purchases from Gs.250,000, plus insurance for the winner only. Excluded from guaranteed discount offers, not presented as free insurance for every customer.
- Geox 74 API start date says 2025-10-10, but both current description and PDF V1 28/10/2026 specify 29 October–1 November 2026. The narrower explicit campaign window is used. 20% discount and up to six interest-free installments remain separate. No cap or branch is invented.
- Tonina 52: current API explicitly says Gs.50,000 monthly refund cap, linked PDF says Gs.100,000. Removed old unconditional hard-coded cap. Discount is `unconfirmed`, with no selected refund cap and an explicit warning; installments are separate. Do not report GNB as fully fetched/confirmed: runner must mark partial (one unconfirmed discount row).

## BNF evidence coverage

All five official linked October PDFs were retrieved and parsed. Branch counts are PDF source rows, **not newly verified geographic coordinates**:

| Category | End date | Rows | Branches |
|---|---|---:|---:|
| Mayoristas | 2026-10-31 | 10 | 17 |
| Farmacias | 2026-10-26 | 12 | 429 |
| Estaciones de Servicio | 2026-10-28 | 5 | 388 |
| Supermercados | 2026-10-29 | 46 | 110 |
| Frigorificos | 2026-10-30 | 4 | 47 |

Expired rows remain history and must not become today's deals. Original card variants, purchase-versus-refund caps and branch provenance remain unchanged (CSV exact byte comparison passed). No November campaign is inferred.

## GNB coverage limits

Real official catalog API retrieval, 254/254 cards and terms links. Three PDFs rechecked (Casa Rica prize draw, Geox, Tonina), not 254 PDFs. Remaining existing reviewed campaigns were not newly audited exhaustively. Result 484 source rows versus482, of which one discount is unconfirmed. The build must retain this distinction in source health. Metadata and actual source artifacts remain available in the isolated worktree for integration; no public source_status was certified by this repair alone.

## Verification

`test_bnf*.py`: 6 passed. `test_gnb*.py`: 19 passed (includes deliberate failure/rollback fixture). Exact-source regression fixtures cover expiry without renewal, unknown-date rejection, semantic review invalidation, changed-PDF rejection, sweepstakes exclusion, Geox window, and Tonina conflicting-cap quarantine.

This is a targeted source repair, not a full test-suite, full-bank-PDF, or deployment certification.
