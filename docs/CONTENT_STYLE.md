# BlokVolt — how pages are written (since the 2026-09 redesign)

The site is a reference portal. People come to find a charger, a price, a firm or a rule — fast.
Every page is short, calm and useful. Extra information exists, but it is folded away.

## Voice (Serbian, Latin, ekavica)

- Address the reader with "vi". Impersonal about the site: never "mi", "redakcija", "proverili smo",
  "sabrali smo", "tim". The portal just states facts.
- Short sentences (up to ~20 words). Plain words. One idea per paragraph, at most three sentences.
- No filler: no "važno je napomenuti", "ukratko", "ono što se prećutkuje", "dobra vest je", rhetorical
  questions, exclamation marks, or announcements of what the page will say.
- No meta talk about methodology, dates or sources in the body. Dates and sources are shown by the
  template (small "Ažurirano" line and a folded "Izvori" block).
- Numbers are exact and match the sources. Prices always say "sa PDV-om" or "bez PDV-a" when the
  source says so. Never invent or round a fact into something the source does not say.
- Evolako is one firm among others. No "naša ponuda", "mi ugrađujemo", no mentions of who runs the site
  outside /o-sajtu/. The word "nezavisni" is not used about the site.

## Page shape (markdown in content/podaci, content/javno, content/vodici)

Front matter keys: `title` (SEO title, up to ~65 chars), `h1` (short heading, up to ~40 chars),
`description` (up to ~155 chars), `lead` (one sentence, up to ~20 words), `kicker` (1–2 words, used by
search and breadcrumbs), `updated`, `next_check`, `published`, `modified`, `priority`, `path` (when the
URL is not /podaci/<slug>/), `sources` (`label :: url | label :: url`). Keep existing keys and values
that are not text (dates, priority, path).

Body:

1. A summary box with the 3–5 facts most readers need, numbers in bold:

   ```
   <div class="sum" markdown="1">
   - **5.000 €** za novi električni automobil
   - Rok za prijavu: **1. decembar 2026.**
   </div>
   ```

2. Two to five sections (`## Kratak naslov`), each up to ~90 words: short paragraphs, lists, or a
   table with at most four columns.
3. Secondary material — history, exceptions, legal article numbers, calculations, long lists,
   caveats — goes into folded blocks, placed right after the section they belong to:

   ```
   <details markdown="1">
   <summary>Detalji: kako je bilo 2025.</summary>

   ...

   </details>
   ```

4. No "Izvori" section and no disclaimer paragraph in the body — the template adds both.
5. Links: only the few that help the next step (up to ~5 per page), as normal markdown links.

Targets: the visible text (outside `<details>`) is about a third of what an old page had; everything
together is at most about 60 %.
