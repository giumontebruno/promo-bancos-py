# Payback PY - implementation checkpoint

## September 14, 2026

- Official September UENO benefit and terms PDFs now replace the August page overrides.
- Level tables retain purchase/refund caps separately. Branch tables retain source URL and page.
- Exact duplicate IDs are prevented; unambiguous renewed benefits migrate favorite IDs.
- Unknown or conflicting limits do not produce guessed maximum savings.
- Source refresh failures preserve previous bank datasets and produce an audit report.
- Refresh is configured daily; Google location requests are bounded and require the repository secret.
- Recovered historical coordinates are not a new verification. Review-only matches are not map pins.
- Notification service implements opt-in Web Push, device tokens, favorite synchronization,
  expiry/day/level checks, duplicate-delivery protection and unsubscribe handling.
- Premium compact UI, high-contrast selected banks, one-line weekday filter and keyboard card access.
- Regression tests: `npm test` and `python -m unittest discover -s tests -p 'test_*.py'`.

## Remaining Verification

- All-bank source coverage is NOT certified complete. Inspect `outputs/promotions_quality_report.json`.
- BNF current catalogue access and merchant-level branch associations need further source verification.
- Every branch must still pass address and merchant matching; missing or ambiguous cities remain pending.
- End-to-end phone push delivery needs an opt-in subscription on an actual device.
- Runtime notification URL and daily dispatch secrets must be configured after service publication.
- Browser Maps key intentionally rejects localhost. Test production maps without weakening restrictions.

## September 14 data pass

- The five current BNF September PDFs are parsed into 75 merchant-level benefits and 994 branch source records.
- BNF purchase caps, refund caps and eligible card tiers are stored separately. Pharmacy financing is a separate benefit and cannot be combined with the refund.
- One contradictory BNF premium cap remains visibly flagged and is excluded from savings calculations until the bank clarifies it.
- BNF branch names and addresses now come from each PDF table heading and row; shopping centres are retained as addresses, not promoted to merchant names.
- Google enrichment rotates across banks and retains ambiguous candidates for review without placing them on the public map.
- All-uppercase merchant names are normalized for display while banking and merchant acronyms are preserved.

## Still not certified

- The Google batch is an automated candidate matcher, not proof that every one of the 994 BNF branches is correctly pinned.
- Promotions from all banks still require recurring PDF-versus-terms audits when the banks replace or amend monthly documents.
- End-to-end phone push delivery still needs a real-device opt-in test; server and browser unit tests pass.

Never commit backend API keys, VAPID private keys, device tokens or local credential files.
