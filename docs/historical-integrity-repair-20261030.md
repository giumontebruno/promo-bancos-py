# Historical integrity repairs — 2026-10-30

## Attested evidence bytes

Seven JSON documents referenced by the79 approved geographic reviews had been normalized from CRLF to LF. Restoring CRLF reproduces **each existing approved SHA256 exactly**. JSON semantic equality was checked before writing. No coordinate, merchant, branch, source, review approval or stored SHA was changed.

`.gitattributes` disables text conversion only for those seven exact evidence paths. Regression checks all79 existing evidence references, exactly seven protected paths, raw SHA matches and identical JSON semantics with either newline representation.

## Unavailable favorite identities

Two archived identities have neither a current offer nor a justified migration target:

- `84714bfec7199316`: Atlas / Martiderm; historical end date unknown.
- `6d3e46f1399d07fb`: Coop. Universitaria / SANTA CLARA; historical end2027-06-15 does **not** prove that the withdrawn source offer remains valid now.

A new additive manifest `favorite_unavailable` map explicitly accounts for these IDs with bank, merchant, original source, historical end date and reason `not_in_current_sources`. These entries are metadata, not promotions, aliases, benefits or notification candidates. They cannot reactivate a deal. Original user favorite IDs remain unchanged; returning current IDs or valid existing aliases clear the corresponding tombstone. Alias cycles still fail.

The archive itself is untouched. The migration audit still requires every historical identity to resolve: either a real catalog identity, or an explicit provenance-checked unavailable entry. It rejects invented alias destinations and unavailable entries for resolved IDs.

The existing consumer already preserves missing IDs. Main and beta empty favorites now distinguish no saved IDs from saved-but-unavailable offers, without exposing operational diagnostics. Filters remain handled by the existing non-personal-view branch; no favorite is deleted.
