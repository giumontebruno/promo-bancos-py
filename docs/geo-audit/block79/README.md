# Reviewed branches and promotion corrections — 20 October 2026

Approved scope: original84 candidates,79 accepted after final QA.53 new branch records: Electroban24, Burger King11, Nissei1, Pizza Hut1, Bristol16.26 existing Scavone IDs receive coordinates. Five ambiguous Scavone pins remain unchanged; see scavone-excluded.json. No other research candidates included.

All1935 existing location IDs preserved; only26 existing rows changed. Every accepted record binds the bank, merchant, address, locality, exact source URL and promotion IDs. Coordinates come from explicit operator pins/place coordinates, not viewport centers or city approximations. Locality labels follow operators; municipal boundaries are not independently surveyed.

Real-map visual inspection of31 Scavone candidates exposed five street/pin inconsistencies. Accepted26 plus53 other source-verified candidates. Rebuild retains superseded Google evidence in manifests and removes stale navigation fields from reviewed coordinates.

Music Hall: byte-identical official PDF with new URL; restore15% except audio,5% audio and up to12 installments. Three original variant IDs retained. Prior generic row archived in music-hall-before-review.json; historical favorites resolve to one campaign.

Atlas Feria de Viajes: official PDF hash reconfirmed before integration.20% premium including Signature delSol,15% Visa Clasica/Oro;23October only; minimum8000000PYG, accumulated purchase cap12000000PYG/account; up to18 installments. Preserve campaign and historical favorite aliases. No agency coordinates inferred.

Reproduce data: python promo_backend/normalize.py; python scrapers/build_locations.py --skip-geocoding. Rebuilding uses data/multibank_reviewed_branches_20261020.json and data/bnf_scavone_reviewed_locations.json. Evidence rows and hashes are included beside this report.

Validation:82/82 JavaScript tests, build and390/1440browser checks passed. Python116/117; known GNB677 failure comes from an older card JSON paired with a newer review CSV, outside this approved change. Do not remove data to hide it. Six location and five promotion/favorite regressions added. Browser verified79 Monday points and53 Tuesday points for this block; Scavone remains Monday-only. Prior Shell94/Farmacenter78/Catedral97/Petrochaco2 preserved. Cache version29.
