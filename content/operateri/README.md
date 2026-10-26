# content/operateri

Ring 2 records (public charging networks, hosts, free locations). Edit these JSON files directly, then run `python3 build.py`. `scripts/add_operators.py` made the first version of them; it is a historical import and must never be re-run (it would overwrite later edits and the price history) — docs/RUNBOOK.md §2.

Search fields (SEO, 26.10.2026): `seo_title` is the page's `<title>` without " | BlokVolt" (build adds the suffix; a title longer than 60 characters drops it, build.py `_seo_title`), written the way drivers search (network name + "punjači" + what the page answers: cena, lokacije, stanje). `h1` is the page heading. Both are optional: without them the page uses `short_name`. Keep them true to the card: no "cena" in a title when the network publishes no price and the page shows none.
