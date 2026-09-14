# Beta readiness

Status: implemented locally, not activated or deployed. Authentication provider configuration and real-device checks remain required.

## Required hosted configuration

1. Supabase project: `ymmsnoicjfmakmmjttma`. Its site and redirect URL are configured as `https://giumontebruno.github.io/promo-bancos-py/app-web/`.
2. Google OAuth replaces email links for this beta; SMTP is not required for this login. Configure the Google provider with a web client whose callback is `https://ymmsnoicjfmakmmjttma.supabase.co/auth/v1/callback`. Request only openid, email and profile. The client uses PKCE. Permit Google identities to be created, while the server allowlist remains mandatory for all beta data and admin endpoints. Configure Google test users before invitations; do not enable anonymous sign-in or remove the server allowlist.
3. Set runtime SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY. This is the public publishable key, NOT a service-role key. Set BETA_ALLOWED_EMAILS and BETA_ADMIN_EMAILS to explicit comma-separated email allowlists. Empty allowlists deny everyone.
4. Deploy the Worker with the generated D1 migration before publishing the frontend. The beta is disabled until configured. Existing device notification routes now require the new nullable account_id column.
5. Run `npm run build` to generate the bundled SDK and frontend, then publish the built output. Do not publish the unbuilt app-web directory.

## Implemented

- Google authentication via Supabase; server verifies tokens with Auth /user and checks invitation/admin allowlists.
- Per-account favorite rows, capped at 100; no silent merge of device-local favorites into an account.
- Daily activity counters only after opt-in. No search text, coordinates, or merchant history in analytics. Retention: 30 days, pruned on event ingestion; admin queries also exclude older records. Revocation deletes counters immediately.
- Authenticated reports (max 10/day); authenticated administrator participant counters and last 100 reports.
- Push devices linked to accounts; scheduler reads account favorites and UENO level before sending, using existing expiry checks and daily deduplication.
- Sign-out disables this device's push subscription. Clear-beta-data removes account data, reports, counters, favorites and linked push devices; it does not delete the Supabase Auth identity. Identity removal must currently be handled by the administrator in Supabase.

## Must test before inviting friends

- Google login, cancelled consent, uninvited user, redirect and sign-out. The OAuth provider still needs to be connected before this test can pass.
- Two different accounts and two devices: no cross-account favorites; additions/removals sync on next account refresh or app reopen. No background realtime sync is claimed.
- Consent off means no events; revoke removes counters; tester cannot access admin endpoint.
- Notification delivery with app closed on Android and installed iOS PWA. Current dispatch schedule remains unchanged; user-defined notification times and card-tier preferences are not implemented.
- Report a missing merchant (e.g. Kaiseki), and verify the merchant/branch source separately before changing catalog data.
- Small-screen map and permission denial; offline and server-unavailable behavior.
- Review privacy notice, admin contact and account-deletion procedure before invitations.

No claim of complete catalog coverage or Play Store readiness is made by this release.
