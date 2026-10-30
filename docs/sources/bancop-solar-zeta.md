# Bancop, Solar and Zeta — source boundary, 2026-10-30

Public-source inspection only. No login, credentials or installation. The public web catalog is not proof of exhaustive bank coverage.

## Bancop
- Entry: https://www.bancop.com.py/promociones
- Public HTML exposes 58 unique `data-id` promotion cards. Its inline modal handler documents POST `https://www.bancop.com.py/ajax/promocion.php` with only the public promotion ID; it retrieves information, not a contact form.
- All 58 modals inspected and their linked PDF terms downloaded on 30 October 2026. Extractor limit: 120 cards, four concurrent workers, 30-second request timeout, 15 MB/40 pages per document.
- Follow-on complete review: all 58 listing cards have an individual decision in `data/bancop_reviewed_catalog.json`. 52 cards yield 68 reviewed variants, including financing separately. Six cards are quarantined with specific defects: five omit the validity year (539,544,543,547,541); Nissei487 links a Visuar/Tienda Móvil document. No undated benefit is called current.
- Generic PDF fallback was removed: matching source URL, listing identity and exact PDF hash are required for reviewed rows. Changed/new documents are quarantined, not parsed into potentially misattributed offers. Neuland supermarket/library/minishop and shared financing are separated; Shell fuel and shop have different lists and caps. Biggie Farma excludes delivery and its refund follows the merchant discount. Tigo preserves “hasta” and model limitations; cash advances preserve the commission qualifier.
- Visual tables independently read for Ecop Ypané/Villa Hayes, Chortitzer, Restaurante Ecop, Shell/Laso and Neuland. Missing limits remain unknown (not unlimited); no geography or all-branch coverage is inferred.
- Exact binary document hashes gate all reviewed variants. Changed documents yield a specific review blocker and no replacement guessed rows. Initial regression cases Biggie Express526, Pedidos Ya468 and OktoberAFAPFEST550 remain covered.
- Biggie: until 31 March 2027; 20% Bancardcheck/Clásica/Oro with purchase 800,000 and refund 160,000 monthly per card; Infinite 25%, purchase 1,000,000/refund 250,000. Physical or QR through Infonet only. Source does not repeat weekday in Infinite bullet; do not infer that field.
- Pedidos Ya: until 31 December 2026, all days, 20%, purchase 250,000/refund 50,000 per month/card; official text's physical/QR/Infonet condition retained, not silently changed to online.
- OktoberAFAPFEST: 31 October–1 November 2026, 15% basic group /20% Infinite; purchase 1,000,000, refund 150,000/200,000 per card across campaign. Physical/QR Infonet, other processors excluded.
- Text fixtures are verbatim extraction from those linked documents; no fabricated messages/data.

## Solar
- https://www.solar.com.py/promociones embeds 30 public promotion records in `__NEXT_DATA__.props.pageProps.promos`, including per-card discount, refund, installments, purchase cap, dates, and exact official terms URL.
- 30 linked official PDFs read. 84 variants across 28 campaigns: CyberDay Nissei 3 variants visually verified against page 1 of the official PDF; exact PDF and structured-record hashes gate verification. Remaining 81 variants are **unconfirmed** pending visual PDF-table comparison. Biggie ended 27 October 2026 and is excluded; Quanta lacks the year and is excluded. Year is never inferred from publish date.
- CyberDay Nissei dates are 2–4 November 2026, future not active today. Its terms explicitly online on Nissei Paraguay, Infonet and card affinity restrictions.
- `total_discount` is never used as cashback: combined merchant discount plus refund must remain separate. Farmacenter and Energy terms say refund applies after merchant discount; summing rates overstates savings.
- Several monetary tables are embedded images. Structured web fields are retained with their provenance but not called financially verified. Premium is labeled as the site's premium affinity, not silently mapped to all cards.
- Farmacenter PDF unusual wording says valid for devices different from Infonet; do not silently correct its wording based on other campaigns. Needs bank clarification/review.

## Zeta
- Browser rendered https://www.zbanco.com.py/site?page=tarjetas successfully. Its actual **Beneficios** link was https://www.zbanco.com.py/uploads/55ba16aa-25d7-4192-9953-12a4c07d84c4.pdf (not the old indexed 2ab6889a PDF).
- Downloaded and read current linked brochure; Visual inspection of the complete one-page brochure (595 × 3757.9 points) also confirms no stated calendar validity. Most merchant logos are legible (including Bourbon, Piccolino, Óptica Meister, Óptica Arar, Farmacenter, Energy, Universo and Shopping China), but a few are uncertain; neither logos nor weekday schedules establish validity. No offers asserted current. Monitor fails closed with `blocked` metadata and no successful empty CSV.
- JS catalog link rediscovery and dated terms/visual identity matching remain required. The fixed observed URL is evidence of this inspection, not a durable complete discovery mechanism.

## Integration
Modules write `outputs/{bank}_beneficios_por_categoria.csv` only for nonempty rows and `outputs/{bank}_source_meta.json` for coverage. Register each source explicitly in run_all/normalization separately. `partial` must remain partial even when some valid rows exist. Do not expose operational metadata in consumer UI. Zeta intentionally exits nonzero and does not replace prior data with empty data. 15 deterministic tests cover dates, expiry, limits/card separation, duplicate IDs, changed-hash downgrade and unknown-source rejection.

Bancop card-field normalization: source bullet typo “Inifinite” is corrected to “Infinite” only where the same PDF’s Beneficiarios clause explicitly states Visa Infinite; verbatim source text is retained.
Zeta indexed alternative 2ab6889a-493f-33f5-a865-a43dc4f9f6fe.pdf was also read: document title Beneficios Zeta Banco-Web-20092024, no explicit validity. It is not used to claim current coverage.
