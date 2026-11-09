# MK back-translation check (60 strings)

Placeholders: all match EN in every key. First person ("ние/наш"): none. No real Serbianisms or spelling errors found. "мапа" is fine in Macedonian.

## Discrepancies / remarks (minor, none change meaning)

1. **shell.map_btn / prices.more_map**: EN "Open the map", BT "Open the map".
   Issue: uses the informal imperative "Отвори", while all other calls to action are polite ("Проверете", "Најдете"). The register is inconsistent.
   Fix: "Отворете ја мапата" (or keep "Отвори" if all buttons use the short form on purpose).

2. **prices.pay_adhoc**: EN "Without a contract (ad hoc price published): {list}.", BT "Without contract (published price without contract): {list}."
   Issue: "без договор" is repeated inside the brackets.
   Fix: "Без договор (објавена ad hoc цена): {list}." or "Без договор (објавена цена): {list}."

3. **prices.c_lead**: EN "...next to household electricity.", BT "...alongside household electricity."
   Issue: "покрај" reads as "in addition to" more than "compared with".
   Fix: "...без договор и со пакет, во споредба со струјата за домаќинства."

4. **pages.t_network / pages.t_country / prices.h_more** (`{country_u}`): the structure matches EN. Check that the MK `{country_u}` value includes its own preposition (e.g. "во Србија"). Without it you get "Полначи на {net} Србија". This is not an error in the string itself; it depends on what is put into the placeholder.

5. **map.c_price_note**: EN "Price from {d}", BT "Price as of {d}". "Цена од {d}" with a date is fine. Note only: if `{d}` could ever be a number rather than a date, it would read as "price starting at".

## Exact or equivalent meaning
All other keys match the meaning of the EN original. Some wording differs with no issue: "EV charging station" = "Полнач за електрични автомобили", and "Споредба со земјата и со полнење дома" is clearer than the EN.

OK: 57 / 60 (map_btn, more_map and pay_adhoc are flagged; items 3–5 are optional polish or checks)
