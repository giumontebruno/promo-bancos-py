# Publication freshness repair — 2026-10-30

## Observed failure, not a cache assumption

The published catalog returned generation `2026-10-24T12:08:31Z` (3,182
records), while main revision `25c02d46704643859ae3b3b1773ffe961bc3253b`
contained generation `2026-10-30T14:12:39.471476+00:00` (3,601 records).

GitHub Actions run 41069894261 on 2026-10-30 failed during `npm test`:
https://github.com/giumontebruno/promo-bancos-py/actions/runs/41069894261

Two Music Hall assertions in `tests/block79-promotions.test.cjs` required an
expired campaign to remain `official_document` in the mutable daily catalog.
The extractor had retained the old variant records as `unconfirmed`; the
normalizer correctly does not attach reviewed campaign identity to those rows.
The required tests therefore blocked upload/deployment. Runs 25–30 October
failed; the last previously observed successful run was 40092721866 on 24 October.

## Repair

Historical favorites/calculation regression assertions now use a documented,
immutable reviewed snapshot. A separate assertion on the live catalog prevents
uncertain Music Hall variants being silently promoted. No bank data, validity,
source status, review hash, or eligibility has been changed to make tests pass.

The build additionally checks that the copied primary public files exactly
match their source bytes, that manifest count agrees with the catalog, and that
promotion IDs are present and unique. It emits `publication.json` containing
revision and SHA-256 hashes. The deployment workflow fetches and verifies the
actual public metadata and data after deployment, with bounded CDN propagation
retries. A fresh app bundle alone is no longer sufficient publication evidence.

Only trusted main-branch runs can deploy. `workflow_run` remains eligible when a
refresh is partial/failed, so preserved usable data and explicit source-health
warnings can still be published if validation passes. The checkout revision is
recorded separately as `PAYBACK_BUILD_REVISION` (GitHub's reserved `GITHUB_SHA`
is not overwritten).

## Limits

Publication verification proves that expected bytes were served. It does not
prove every bank was freshly extracted, every condition remains valid, or every
branch is eligible. `source_status.json`, its attempt/checked dates, and
promotion-level uncertainty remain necessary. No live deployment has been
performed as part of these local changes.
