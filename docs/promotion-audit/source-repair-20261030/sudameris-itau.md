# Sudameris / Itaú source repair — 2026-10-30

Public sources only. No email content or account information included.

## Verified changes

- Sudameris fetch itself succeeded (46 campaigns). The builder aborted globally because the exact document hash for Concepción changed. Fresh bounded retrieval checked all nine scoped documents: four unchanged; four changed; old Curuguaty URL returned 404. This was not evidence that the bank was unavailable.
- Concepción, Katueté and Santa Rosa del Aguaray: current PDF text reviewed against every existing scoped merchant/date/cap. Existing financial scopes unchanged; PDF footer now uses `/personas/beneficios`. Exact hashes renewed only after review. Original source text updated. Elite +5% eligibility remains explicitly unresolved, not assigned to card tiers by inference.
- San Alberto current PDF V3 (26/08/2026), page 2 visually checked: only MAX SUPERMERCADO, 20% reintegro, last Saturday each month, purchase cap Gs.600,000 per account/brand/month, 29/08–31/12/2026. Removed obsolete CHAI/Petrobras/financing reviews from active override manifest; previous historical rows remain unconfirmed rather than silently renewed. Replacement of MAX's old row requires its exact previous fingerprint.
- Official Zona Norte page now links Curuguaty to `/descargas/documentos/zona-norte-curuguaty`. PDF V5 (28/10/2026), page 2 visually checked: Farmacia Amaia remains first Monday, 20% reintegro plus up to 12 interest-free installments, Gs.500,000 monthly purchase cap, 01/10–07/12/2026. New GREFRAN SUPERMERCADO: last Saturday, 20% reintegro, Gs.500,000 purchase cap, **31/10–31/12/2026**, not active on 30/10. Both require credit Visa/Mastercard Sudameris and Bancard POS; exclusions preserved. Historical Amaia machine identity retained; current source link updated.
- Itaú: fresh GET of all three `b=16359` detail URLs (`c=30226`, `30369`, `1040`) reproduced exact prior source hash `60bb9d0bc58f78b3bcb863a692555ba93793cde0b5cdd79e9fcfb280b9e280a5`. Official prose still says 10% reintegro while benefit field says 5%. These remain unconfirmed, with original text and no guessed card variants. Their review date is updated, not their financial trust.
- Itaú day extraction previously truncated `Aplica MIERCOLES, JUEVES Y VIERNES` to Wednesday. Parser now preserves explicit lists and ranges without inferring daily availability.

## Failure isolation

Strict scoped-review API still fails on changed documents. Builder explicitly opts into isolated partial mode: document errors are recorded; affected existing rows are unconfirmed and their new overrides are not applied; missing additions are not manufactured. Unaffected hash-bound reviews continue. Unknown changed row fingerprints remain unconfirmed. No failures are discarded to obtain a green source status.

## Remaining coverage

Sudameris Zona Sur and Zona Este now link multiple city PDFs; existing one-PDF expansion refuses them rather than guess or merge city caps. Zona Norte scoped manifest covers the reviewed cities but the general expansion also records multiple-PDF coverage. Many campaigns lack newly reviewed document scopes; retained historical rows are not fresh verification. Do not label the whole bank fully verified or all current offers covered.

## Biggie Express public-source check

Current official page `https://www.sudameris.com.py/personas/beneficios/biggie-express` links `https://www.sudameris.com.py/descargas/documentos/6ae398c8d53c5838839357/B%26C-BIGGIEEXPRESS-1RODECADAMES-5.10.26.pdf`. SHA256 `c7a110aa9cc202b3d9ce0c8743be7366c2b5bda8ff871e9e0a9586eacac70cd3`. Full rendered single page verified: 30% reintegro; first calendar day of month; **01 July–31 December 2026** according to PDF (not an inferred start); monthly purchase cap per credit account Gs.700,000; minimum transaction Gs.50,000; Mastercard/Visa credit; all physical Biggie Express locations via Infonet/Bancard. No web/delivery/third-party platforms, prepaid/debit/excluded card products, other processors or stacking. Existing review pointed to an obsolete PDF path; rebound to current exact document after comparison, preserving financial conditions. No private email evidence used in dataset.

## Bounded fresh-run results

- Sudameris final build at 15:59:17 UTC: 46 fetched campaigns; 346 exported scoped/retained rows vs 329 before; 17 added identities, zero removed identities, zero duplicate (URL, merchant, variant) keys. 68 current hash-verified document rows; 278 unconfirmed retained/generic rows. Four migration coverage failures remain (Distrito Perseverancia lacks quantified page benefit; Zona Sur/Este/Norte multi-document expansion requires scoped review). This is partial, **not** complete coverage.
- Fixed independent preservation bug: old card/payment variants were discarded when the current page yielded a generic banner with the same URL+merchant. Retention now also keys on variant; prior unverified variants survive as unconfirmed rather than disappearing. Prior input rows are not mutated.
- Itaú full fresh fetch: 548 rows vs 547, none removed. 127 explicit day lists/ranges are no longer truncated. One newly discovered row, El Deposito (`b=16790&c=31515`), says up to 30% on fees/event-2027 deposits, but start date field says 2025-11-24 while prose says 8 October 2026. Added an exact-hash pending review rather than claiming a fixed 30% or inventing a start. There are now **four** explicitly unresolved source rows, not three. Cached replay uses only the HTML downloaded in this bounded run.
- Focused suites: 27 Sudameris + 10 Itaú tests pass. Full Python suite before last extra tests: 153/155 passed; failures were existing unrelated geo evidence hashes (Familiar/BNF block79 files untouched by this change) and archived-favorite resolution in the base public catalog. Integrator must regenerate/verify combined public artifacts, not treat source tests as complete application QA.
