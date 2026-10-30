# Official native-PDF fixtures — retrieved 2026-10-30

`sources.json` records exact official URLs and PDF-byte SHA-256. Text is native
pdfplumber extraction (not OCR). These fixture texts are test evidence, not a claim
that the complete bank catalog is validated. Runtime re-discovers the finite
current index, retrieves every linked campaign once, and leaves unfamiliar
contracts in a review queue withheld from the consumer catalog. HTTP success is not validation success.

## Stratified validation

- **Basa AUTOLAV, p. 1:** single-scope 20% refund; Gs. 200,000 is a *purchase*
  cap per card account/month, not a Gs. 200,000 refund. Selected cards, Infonet POS,
  excluded corporate/prepaid/Gourmet cards retained. No invented starting date.
- **Basa Supermercados, pp. 1–2:** visually reviewed two-column table, 20% with
  Gs. 1.5m purchase cap vs Black/Signature 25% with Gs. 2m purchase cap. Shared
  monthly merchant pool. La Rosarina begins September 10, not March 5. Casa
  Paraná excluded from October 1; Basa Mastercard Oro excluded. Exact hash gate.
- **Basa Hoteles, pp. 1–2:** visually reviewed 15% Oro vs 20% Black/Signature;
  Gs. 3.5m monthly purchase cap shared by five named hotels. Up to 12 installments.
  Separate national-hotel financing scope is not mapped: marked partial, not full.
- **Basa Bernardino, p. 1:** visually reviewed 30% Fridays and Black 35% daily;
  Gs. 500,000 monthly purchase cap, not separate caps for both variants. Event carts
  excluded. Exact PDF hash is required before using this manual table review.
- **Interfisa ROCKIT, p. 1:** separate 25% Classic/Gold (Gs. 1.25m refund) and 30%
  premium (Gs. 1.5m refund), common Gs. 5m monthly purchase cap including additional
  cards; one explicit location. Full conditions and exclusion scope retained.
- **Interfisa Farmacias Energy, pp. 1–2:** October 31 only, not all Saturdays;
  refund 30% and up-to-6 installments separate. The common purchase-cap clause
  is retained for installments, with its applicability marked unconfirmed. Gs.
  450,000 refund maximum is not automatically treated as a financing cap. Listed branches retained; no coordinates inferred.
- **Interfisa Cole Haan, p. 1:** visually confirmed the actual source says
  **31/10/2027**, not 2026; never silently “correct” a bank's stated year. Both
  card-specific refund caps and the separate installment scope are preserved.

## Fail-closed regressions

Changed reviewed PDF hash; wrong merchant PDF; extra validity clause; funding or
separate purchase dates; missing/ambiguous cap; unrecognized benefits; expired
single-day campaign; future exact day; external/non-HTTPS URL; corporate-footer
PDFs excluded from campaign discovery. Ambiguous image-only or nonstandard table
contracts remain pending; no OCR-based financial claim is promoted.

## Coverage limits

Basa's reviewed hotel campaign covers named-hotel refunds, not every clause in
its PDF. Generic Basa tables containing multiple rates/tiers/recurrences are held.
Interfisa accepts only the explicit numbered-section/bulleted-card-scope template;
unknown aliases, additive offers, alternate date/action scopes and unfamiliar
caps are held. The index/page caption never overrides contract conditions.
Locations remain textual unless separately independently geocoded elsewhere.
No whole-bank completeness claim is justified while pending > 0.

## Independent-review correction

The 43 Interfisa installment variants retain the original shared purchase-cap
clause. Its application to installments is **unconfirmed**: they are not asserted
to be uncapped, nor assigned an inferred cap. Such documents remain partially
reviewed. Cached file modification times are never treated as HTTP fetch times;
legacy cache has null fetched_at unless a URL/hash/timestamp sidecar validates.
