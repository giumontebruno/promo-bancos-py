# paybackpy beta — checkpoint, not deployed

Source: approved interface 5903bf5. Isolated branch based on production c18877f.
Candidate route: https://giumontebruno.github.io/promo-bancos-py/beta/ (NOT published/verified).

## Isolation
- Original app-web/, server/, public/, data/, drizzle/ unchanged.
- beta-web/ builds to dist/client/beta/ alongside existing production output.
- Manifest name/short_name exactly paybackpy beta; id/start_url/scope /promo-bancos-py/beta/.
- SW scope ./; no CacheStorage operations, push registration or notifications. Offline navigation shows a retry message. Production's legacy worker deletes origin-wide caches, so this beta deliberately keeps none.
- localStorage prefix paybackPyBeta.; Supabase storageKey paybackPyBeta.auth; signOut scope local.
- Favorites and UENO level local per authenticated account. Theme/profile preferences local to beta. No migration or writes to production favorites/preferences.
- Existing server validates session via GET /api/beta/me. Existing handler may INSERT OR IGNORE a new account as part of login; no server changes made. No beta event/report/admin/delete mutations. No synchronization or push notifications in this preview; UI says so.
- Existing Google login and backend identity checks retained. Public catalog/assets remain public. This is not private access protection.

## Verification
- Build passed with existing dependencies copied locally, no install/junction.
- 71 production application build files byte-identical to untouched source/build outputs.
- Local Chrome rendering via setContent, external network blocked: 360/390/1280 light/dark, no page/card/detail/map-sheet overflow, controls >=44px, secondary contrast >=5.66.
- Dates, empty search, favorites, theme, conditions, long card names, reduced motion tested.
- Unit suite includes existing production tests plus beta date/map/filter tests and storage/manifest/no-mutation tests.
- Real OAuth/GPS/iPhone installation not tested. No public deployment or CI run yet.

## Blocker
Supabase project ymmsnoicjfmakmmjttma Authentication / URL Configuration redirected to sign-in. Automated review denied clicking Continue with GitHub because initiating OAuth was outside current authorization. No grant or security change occurred; do not bypass.
Need user to open their existing Supabase session or explicitly authorize that sign-in. Then inspect Redirect URLs for exact https://giumontebruno.github.io/promo-bancos-py/beta/ . If missing, request authorization to add only that URL, no wildcard/site URL replacement/new credentials. Do not publish an unverified login return route.

## Publication after unblock
Fetch latest main, rebase only this beta branch, keep original app-web tree unchanged, rerun checks/build and compare production output. Review merge/push target carefully: never merge 5903bf5 UI into app-web. The existing Pages workflow packages both apps; modified paths trigger beta rebuilds. Publish only after return URL verified. Verify HTTP manifest/scripts/SW, actual Pages CI and production unchanged; test beta Google login if user permits, without closing main session. Separate manifest identity supports side-by-side installation but actual installation belongs to user's device.
Rollback: revert isolated beta commit; original app route/files unchanged. Remove beta installation on device separately if desired. No backend rollback needed.
