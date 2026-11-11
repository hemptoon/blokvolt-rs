# L2-uk — result (11.11.2026)

Branch `l2-uk` from `dev` bb86f74. Files only in `content/world/i18n/uk/`.

- Keys translated: 274 (map 29, pay 93, press 54, b2b 33, embed 65). HOME2 not in `dev` yet — its home keys are for LANGI.
- texts.json: `pay` 6 nodes, `routes` 59 nodes, `sources_pages` 30 sources (was missing in uk).
- Cities: market UA — 4 cities in names, 1 city page (Львів); all present, decl_ok=1. Nothing added.
- check.py: 8 files + texts → 0 errors, 0 warnings.
- Back-translation: 60 random new strings, 60 ok, 0 mismatch; 7 style fixes applied (REVIEW.md).

Notes for LANG0/LANGI:
- pages_state has 138 SE and 6 NO city pages whose geonameid is missing in names/cities.csv (NOBIL) — for sv/nb sessions and the names file, not uk.
- world_press.py uses hard-coded de/fr fact sentences and month names; for uk the engine must take press f_* from strings_press and give {month} in the nominative («листопад 2026»).
