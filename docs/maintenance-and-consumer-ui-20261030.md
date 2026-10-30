# Maintenance and consumer UI — 2026-10-30

Owner direction: operational source errors and missing coverage are reviewed outside the consumer app. The source-health panel is removed, not replaced with a dropdown. Individual promotion terms and uncertain eligibility remain visible so the app does not promise unverified savings. Beta asset versions were advanced to avoid mixing cached scripts from earlier releases.

## Existing daily refresh, strengthened
- Existing schedule retained: 07:00 UTC / 04:00 Paraguay. GitHub schedules may run late; this is not an uptime guarantee.
- No added permissions, API providers, secrets, geocoding quotas or payment integrations.
- Compare refreshed catalog against runner-local baseline, before committing data.
- Block commit on invalid/empty catalog, mismatched counts/IDs, missing source data, generation older than 36 hours, over 50% total/per-bank record loss, or a normalization report predating the current run.
- Preserve publication of usable partial refreshes. Fail/partial source status, no complete extraction within 72 hours, or no attempt within 36 hours still produce an attention-required CI result.
- Inspect `promotion-audit`, the workflow summary, `outputs/maintenance_report.json` and `outputs/maintenance_summary.md`. They are operational repository/CI diagnostics, not a private channel and not consumer UI.
- The completed refresh triggers deployment of validated latest `main`, not necessarily the workflow trigger's original SHA. Build and HTTP checks prove the actual served revision and hashes through `publication.json`.

## Boundaries
These checks detect failures; they do not repair bank access, review ambiguous financial conditions, prove remaining card limits, or confirm map identities. No new chat alert delivery was configured here. Source-specific repairs and broader coverage remain a separately reviewed backlog. Full Python regression coverage still has the separately documented dependency and historical-data issues.
