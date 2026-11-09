# Greek (el) back-translation QA

Method: `random.seed(743)`, 60 random (file, key) pairs from `strings_{map,pages,shell,prices}.json` (pl_* skipped). The Greek values were back-translated into English blind, then compared with the EN originals. Date: 2026-11-09.

## Summary

- Sampled: 60 (map 16, pages 15, shell 7, prices 22)
- ok: 57
- minor: 3
- mismatch: 0
- Rule violations in the sample: none (no first-person plural, no "η σύνταξη", no 24/7, no αμέσως/άμεσα, no Evolako, no network ratings).
- A full-file regex scan of all four strings files and texts.json for εμείς / μας / -ουμε / σύνταξη / 24/7 / αμέσως / άμεσα / Evolako / βαθμολογ* found only two hits, both negations that are correct and wanted: `strings_shell.about_p` ("χωρίς βαθμολογίες δικτύων" = "no network ratings") and `texts.about_data.intro` ("Ο χάρτης δεν βαθμολογεί δίκτυα" = "the map does not rate networks").
- Grammar and accents: no errors found in the sample. The Greek ano teleia (·) correctly replaces the EN semicolon in `prices.m2`.

## Minor items

### 1. prices.pay_sub vs prices.th_plan: inconsistent term for "plan"
- Greek (pay_sub): `Συνδρομές: {list}.`
- Back-translation: "Subscriptions: {list}."
- EN: "Plans: {list}."
- Greek (th_plan): `Πρόγραμμα` = "Programme/Plan"
- Comment: In EN the same word "plan" is used, but the Greek uses Συνδρομές in one key and Πρόγραμμα in the other. The meaning is close (a plan is a subscription in these networks), but the column header and the list label should match. c_lead and d_hub also use "με συνδρομή" for "with a plan".
- Suggested fix: use συνδρομή consistently, since that is what the rest of the file uses. Set `th_plan` → `Συνδρομή`, and keep `pay_sub` as is.

### 2. prices.d_hub: added gloss
- Greek: `... τιμές χωρίς συνδρομή (ad hoc) των δικτύων ανά χώρα, AC, DC και HPC, σε σύγκριση με το οικιακό ρεύμα. ...`
- Back-translation: "... prices without subscription (ad hoc) of the networks by country ..."
- EN: "... ad hoc prices of the networks by country ..."
- Comment: "χωρίς συνδρομή" is added as an explanation. It is accurate and helpful, but the word order "τιμές χωρίς συνδρομή (ad hoc) των δικτύων" is a little heavy for a meta description.
- Suggested fix (optional): `τιμές ad hoc (χωρίς συνδρομή) των δικτύων ανά χώρα` or `τιμές των δικτύων χωρίς συνδρομή, ανά χώρα`.

### 3. pages.d_city: slight redundancy
- Greek: `... φορτιστές ταχείας φόρτισης DC με ισχύ και βύσματα ...`
- Back-translation: "... fast-charging DC chargers with power and plugs ..."
- EN: "... fast DC chargers with power and connectors ..."
- Comment: "φορτιστές ταχείας φόρτισης" repeats "charg-". This is natural enough in Greek, just a bit wordy.
- Suggested fix (optional): `ταχείς φορτιστές DC με ισχύ και βύσματα`.

## Not flagged (accepted nuance)
- `pages.regional_guide`: "Περιφερειακός οδηγός ({country})" uses a parenthesis where the EN has "for {country}". The meaning is the same.
- `shell.search_none`: "instead" is dropped. This is fine.
- `prices.serbia_note`: "taken" is implicit. This is fine.
- `map.lead`: "σημεία φόρτισης" (charging points) is used for "chargers". This is fine.
