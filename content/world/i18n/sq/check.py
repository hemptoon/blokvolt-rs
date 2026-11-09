#!/usr/bin/env python3
"""Проверка локализации мирового слоя: content/world/i18n/<код>/ против EN.

Запуск: python3 content/world/i18n/sq/check.py   (из корня репозитория или откуда угодно)
Выход 0 — ошибок нет; иначе печатает ошибки и выходит с кодом 1.
"""
import csv, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANG = HERE.name
WORLD = HERE.parent.parent
ERR, WARN = [], []

PH = re.compile(r"\{[^{}]*\}")
TAG = re.compile(r"</?([a-zA-Z0-9]+)[^>]*>")
ENT = re.compile(r"&[a-zA-Z#0-9]+;")
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
BANNED = [r"24/7", r"\bmenjëherë\b", r"\bevolako\b"]


def plural_tags():
    try:
        from babel import Locale
        return set(Locale(LANG).plural_form.tags) | {"other"}
    except Exception as e:  # noqa
        WARN.append(f"Babel недоступен ({e}); категории форм не сверены")
        return None


def sig(s):
    return (sorted(PH.findall(s)), [t.lower() for t in TAG.findall(s)], sorted(ENT.findall(s)))


def check_str(where, en, tr):
    if not isinstance(tr, str) or not tr.strip():
        ERR.append(f"{where}: пустое значение"); return
    if sig(en) != sig(tr):
        ERR.append(f"{where}: плейсхолдеры/теги/сущности не совпадают\n   EN {sig(en)}\n   TR {sig(tr)}")
    if en.endswith(" | BlokVolt") and not tr.endswith(" | BlokVolt"):
        ERR.append(f"{where}: потерян хвост ' | BlokVolt'")
    for b in BANNED:
        if re.search(b, tr, re.I):
            ERR.append(f"{where}: запрещённое слово {b}")


def check_strings(tags):
    for f in ["strings_map", "strings_pages", "strings_shell", "strings_prices"]:
        en = {k: v["en"] for k, v in json.load(open(WORLD / f"{f}.json", encoding="utf-8")).items()}
        p = HERE / f"{f}.json"
        if not p.exists():
            ERR.append(f"нет файла {p.name}"); continue
        tr = json.load(open(p, encoding="utf-8"))
        for k in en.keys() - tr.keys():
            ERR.append(f"{f}.{k}: ключ отсутствует")
        for k in tr.keys() - en.keys():
            ERR.append(f"{f}.{k}: лишний ключ")
        for k in en.keys() & tr.keys():
            w = f"{f}.{k}"
            if k.startswith("pl_"):
                if not isinstance(tr[k], dict):
                    ERR.append(f"{w}: плюрал должен быть объектом"); continue
                if tags is not None and set(tr[k]) != tags:
                    ERR.append(f"{w}: категории {sorted(tr[k])} ≠ CLDR {sorted(tags)}")
                for c, v in tr[k].items():
                    if not str(v).strip():
                        ERR.append(f"{w}.{c}: пусто")
            else:
                check_str(w, en[k], tr[k])


def walk(where, en, tr):
    if type(en) is not type(tr):
        ERR.append(f"{where}: тип {type(en).__name__} ≠ {type(tr).__name__}"); return
    if isinstance(en, dict):
        if set(en) != set(tr):
            ERR.append(f"{where}: ключи различаются {sorted(set(en) ^ set(tr))}")
        for k in set(en) & set(tr):
            walk(f"{where}.{k}", en[k], tr[k])
    elif isinstance(en, list):
        if len(en) != len(tr):
            ERR.append(f"{where}: длина списка {len(en)} ≠ {len(tr)}")
        for i, (a, b) in enumerate(zip(en, tr)):
            walk(f"{where}[{i}]", a, b)
    elif isinstance(en, str):
        if en.strip():
            check_str(where, en, tr)


def check_texts():
    p = HERE / "texts.json"
    if not p.exists():
        ERR.append("нет texts.json"); return
    tr = json.load(open(p, encoding="utf-8"))
    for key, src in [("about_data", "about_data.json"), ("download", "download.json")]:
        en = json.load(open(WORLD / src, encoding="utf-8"))["en"]
        if key not in tr:
            ERR.append(f"texts.{key}: отсутствует"); continue
        walk(f"texts.{key}", en, tr[key])


def check_slugs():
    need = ["home", "map", "hub", "net", "about", "download", "gnet", "prices", "shell_about", "sources", "methodology"]
    s = json.load(open(HERE / "slugs.json", encoding="utf-8"))
    if sorted(s) != sorted(need):
        ERR.append(f"slugs.json: ключи {sorted(s)} ≠ {sorted(need)}")
    for k in ["net", "about", "download"]:
        if not SLUG.match(s.get(k, "")):
            ERR.append(f"slugs.{k}: не ASCII-сегмент: {s.get(k)!r}")
    full = [k for k in need if k not in ("net", "about", "download")]
    for k in full:
        v = s.get(k, "")
        segs = v.strip("/").split("/")
        if not (v.startswith(f"/{LANG}/") and v.endswith("/") and segs[0] == LANG
                and all(SLUG.match(x) for x in segs)):
            ERR.append(f"slugs.{k}: должен быть /{LANG}/…/ в ASCII: {v!r}")
    vals = [s[k] for k in full if k in s]
    if len(set(vals)) != len(vals):
        ERR.append("slugs.json: полные пути повторяются")


def check_csv():
    cc_src = {r["cc"] for r in csv.DictReader(open(WORLD / "names/countries.csv", encoding="utf-8"))}
    rows = list(csv.DictReader(open(HERE / "countries.csv", encoding="utf-8")))
    if rows and list(rows[0]) != ["cc", "name", "slug", "in_phrase", "note"]:
        ERR.append(f"countries.csv: колонки {list(rows[0])}")
    got = {r["cc"] for r in rows}
    if got != cc_src:
        ERR.append(f"countries.csv: страны различаются {sorted(got ^ cc_src)}")
    slugs = [r["slug"] for r in rows]
    if len(set(slugs)) != len(slugs):
        ERR.append("countries.csv: слаги стран повторяются")
    for r in rows:
        if not SLUG.match(r["slug"]): ERR.append(f"countries {r['cc']}: слаг {r['slug']!r}")
        if not r["name"].strip() or not r["in_phrase"].strip(): ERR.append(f"countries {r['cc']}: пусто")
    geo = {r["geonameid"] for r in csv.DictReader(open(WORLD / "names/cities.csv", encoding="utf-8"))}
    rows = list(csv.DictReader(open(HERE / "cities.csv", encoding="utf-8")))
    if rows and list(rows[0]) != ["geonameid", "name", "in_phrase", "decl_ok", "note"]:
        ERR.append(f"cities.csv: колонки {list(rows[0])}")
    ids = [r["geonameid"] for r in rows]
    if len(set(ids)) != len(ids): ERR.append("cities.csv: повтор geonameid")
    extra = set(ids) - geo
    if extra: ERR.append(f"cities.csv: geonameid нет в names/cities.csv: {sorted(extra)[:10]}")
    for r in rows:
        if not r["name"].strip() or not r["in_phrase"].strip():
            ERR.append(f"cities {r['geonameid']}: пусто")
        if r["decl_ok"] not in ("0", "1"):
            ERR.append(f"cities {r['geonameid']}: decl_ok={r['decl_ok']!r}")
    print(f"города: {len(rows)} из {len(geo)}; decl_ok=0: {sum(r['decl_ok']=='0' for r in rows)}")


if __name__ == "__main__":
    tags = plural_tags()
    check_strings(tags); check_texts(); check_slugs(); check_csv()
    for w in WARN: print("WARN", w)
    for e in ERR: print("ERR ", e)
    print(f"{LANG}: ошибок {len(ERR)}")
    sys.exit(1 if ERR else 0)
