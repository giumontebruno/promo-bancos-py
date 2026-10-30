# Supermarket pilot — local review checkpoint, 2026-10-30

No remote push, merge or deployment performed. Main `app-web/`, backend and public catalog/location data unchanged.

## Implemented
- Beta public browsing; account controls remain opt-in, scoped account/guest storage retained.
- Opt-in supermarket query with exact issuer/card, payment method and purchase amount. Same evaluation rendered on list and map cards; date and existing branch linkage filters retained.
- Conservative three-state evaluator: affirmative only when every supplied proof is complete. Unknown payment methods are not invented exclusions. Published maximums never prove remaining personal cap.
- Official Familiar / Supermercado El País PDF reviewed 2026-10-30; provenance in `data/reviewed/el-pais-20261030.json`. Exact source/terms guard invalidates review if content changes.
- Distinct Visa Platinum and other documented card caps. InterExa is explicitly unresolved. Minimum not stated; QR not separately specified. Remaining shared monthly cap unknown. These remain “Falta confirmar”, with conditional estimate where supported.
- Familiar Superseis also reviewed from its official PDF. Only the explicit Denis Roa branch is linked to its existing verified map point; participation provenance and pre-existing BNF geographic provenance remain separate. Other 40 listed branches are not auto-linked.
- Official El País branch address shown. No map pin for El País: no verified coordinates exist in the current location data. Waze research found a street-number discrepancy; it was not promoted to trusted location data.
- BNF refrigerated-food offers retain existing verified proof and reliable location linkage; tests prevent map display names from breaking original merchant identity.
- Source health distinguishes catalog generation from failed/partial source extraction.
- Full reset clears the pilot query; native labeled controls, responsive CSS.

## Validation / limits
- JavaScript suite and production build pass locally (see final execution log for count).
- Reviewed real-data tests prove card options, separated caps, source invalidation, ambiguous QR/InterExa, no fabricated coordinates.
- Browser visual QA could not run: local Chromium socket sandbox denial, escalation environment could not initialize; existing cloud browser could not reach local server (separate environment). No tunnel/publication was created to bypass this. 390px/desktop screenshot and interactive visual review remain required before release.
- Python full suite not green: missing bs4/pdfplumber in system interpreter; two pre-existing data tests remain (reviewed evidence SHA reflects CRLF while git checkout contains LF; archived favorite IDs without live targets). MusicHall Python test now uses the same immutable reviewed fixture, and its live unconfirmed safety contract passes.
- Publication fix and packaging checks described in `docs/publication-freshness-20261030.md`. Successful local build does not mean the public site has changed.

## Release decision
Keep changes on isolated review branch until visual QA and review acceptance. Publishing requires the parent's explicit release decision; no deploy/main push is included here. Do not describe the pilot as complete supermarket coverage or guaranteed cashback.
