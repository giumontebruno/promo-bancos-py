# Historical regression fixture, not current promotion data

Captured 2026-10-30 from the currently published 2026-10-24 snapshot:
https://giumontebruno.github.io/promo-bancos-py/public/promotions.json

Only the three reviewed Music Hall variant records are retained. They apply
2026-10-19 through 2026-10-24 and must never be copied back into live data to
restore verification. Their PDF review and campaign identity are documented in
`data/sudameris_document_reviews.json` and `data/reviewed_campaign_identities.json`.

The fixture tests historical calculation and favorites behavior. A separate
current-catalog assertion prevents unconfirmed variants being promoted. Daily
source absence or verification failure must remain visible and must not make an
expired promotion's historical reviewed status a prerequisite for publishing
fresh data from unrelated banks.
