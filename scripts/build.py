#!/usr/bin/env python3
"""Checks the lists and builds dist/ from them.

    python scripts/build.py           build dist/ from categories.yaml and countries/*.yaml
    python scripts/build.py --check   check, and that dist/ is what a build makes

Needs PyYAML (pip install pyyaml).
"""

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
COUNTRIES = ROOT / "countries"
DIST = ROOT / "dist"

PACKAGE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*(\.[A-Za-z0-9_]+)+$")
STORES = {
    "bazaar": ("Bazaar", "بازار", "https://cafebazaar.ir/app/{}"),
    "myket": ("Myket", "مایکت", "https://myket.ir/app/{}"),
    "play": ("Google Play", "گوگل‌پلی", "https://play.google.com/store/apps/details?id={}"),
}
APP_KEYS = {"package", "name", "category", "stores", "note"}


class Invalid(Exception):
    pass


def load(path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as e:
        raise Invalid(f"{path.name}: {e}")


def names(value, where, need_fa=True):
    """A name in English, and in Persian (needed for a category; an app of
    a country where Persian is not spoken may have none)."""
    if not isinstance(value, dict) or set(value) - {"fa", "en"}:
        raise Invalid(f"{where}: name is {{fa, en}}")
    for lang in ("fa", "en"):
        if lang in value and (not isinstance(value[lang], str) or not value[lang].strip()):
            raise Invalid(f"{where}: name {lang} is empty")
    if "en" not in value or (need_fa and "fa" not in value):
        raise Invalid(f"{where}: name needs en" + (" and fa" if need_fa else ""))
    return {k: value[k].strip() for k in ("fa", "en") if k in value}


def read_categories():
    raw = load(ROOT / "categories.yaml")
    if not isinstance(raw, list) or not raw:
        raise Invalid("categories.yaml: a list of categories")
    categories = []
    for i, c in enumerate(raw):
        where = f"categories.yaml #{i + 1}"
        if not isinstance(c, dict) or set(c) != {"id", "name"} or not re.fullmatch(r"[a-z]+", str(c["id"])):
            raise Invalid(f"{where}: id (lowercase letters) and name")
        categories.append({"id": c["id"], "name": names(c["name"], where)})
    ids = [c["id"] for c in categories]
    if len(set(ids)) != len(ids):
        raise Invalid("categories.yaml: an id twice")
    return categories


def read_country(path, category_ids):
    raw = load(path)
    if not isinstance(raw, list) or not raw:
        raise Invalid(f"{path.name}: a list of apps")
    apps, seen = [], set()
    for i, a in enumerate(raw):
        where = f"{path.name} #{i + 1}"
        if not isinstance(a, dict):
            raise Invalid(f"{where}: an app")
        if set(a) - APP_KEYS:
            raise Invalid(f"{where}: unknown {sorted(set(a) - APP_KEYS)}")
        package = a.get("package")
        if not isinstance(package, str) or not PACKAGE.fullmatch(package):
            raise Invalid(f"{where}: package {package!r} is not an Android package name")
        where = f"{path.name} {package}"
        if package in seen:
            raise Invalid(f"{where}: listed twice")
        seen.add(package)
        if a.get("category") not in category_ids:
            raise Invalid(f"{where}: category {a.get('category')!r} is not in categories.yaml")
        stores = a.get("stores", [])
        if not isinstance(stores, list) or set(stores) - set(STORES) or len(set(stores)) != len(stores):
            raise Invalid(f"{where}: stores are some of {sorted(STORES)}")
        app = {
            "package": package,
            "name": names(a.get("name"), where, need_fa=False),
            "category": a["category"],
            "stores": [s for s in STORES if s in stores],
        }
        if "note" in a:
            if not isinstance(a["note"], str) or not a["note"].strip():
                raise Invalid(f"{where}: note is text")
            app["note"] = a["note"].strip()
        apps.append(app)
    return apps


def order(apps, category_ids):
    rank = {c: i for i, c in enumerate(category_ids)}
    return sorted(apps, key=lambda a: (rank[a["category"]], a["name"]["en"].lower(), a["package"]))


def build_json(code, apps, categories):
    used = {a["category"] for a in apps}
    out = {
        "country": code,
        "count": len(apps),
        "categories": [c for c in categories if c["id"] in used],
        "apps": [
            {
                "package": a["package"],
                "name": a["name"],
                "category": a["category"],
                "links": {s: STORES[s][2].format(a["package"]) for s in a["stores"]},
                **({"note": a["note"]} if "note" in a else {}),
            }
            for a in apps
        ],
    }
    return json.dumps(out, ensure_ascii=False, indent=1) + "\n"


def build_md(code, apps, categories):
    lines = [
        f"# {code.upper()}: apps that connect directly",
        "",
        f"{len(apps)} apps. Built from [countries/{code}.yaml](../countries/{code}.yaml) by `scripts/build.py`; do not edit.",
        "",
    ]
    for c in categories:
        group = [a for a in apps if a["category"] == c["id"]]
        if not group:
            continue
        lines += [f"## {c['name']['fa']} · {c['name']['en']} ({len(group)})", "",
                  "| نام | Name | Package | Stores |", "| --- | --- | --- | --- |"]
        for a in group:
            links = " · ".join(f"[{STORES[s][0]}]({STORES[s][2].format(a['package'])})" for s in a["stores"]) or "—"
            lines.append(f"| {a['name'].get('fa', '')} | {a['name']['en']} | `{a['package']}` | {links} |")
        lines.append("")
    return "\n".join(lines)


def build():
    categories = read_categories()
    ids = [c["id"] for c in categories]
    files = {}
    paths = sorted(COUNTRIES.glob("*.yaml"))
    if not paths:
        raise Invalid("countries/: no lists")
    for path in paths:
        code = path.stem
        if not re.fullmatch(r"[a-z]{2}", code):
            raise Invalid(f"{path.name}: named by its two-letter country code")
        apps = order(read_country(path, ids), ids)
        files[f"{code}.json"] = build_json(code, apps, categories)
        files[f"{code}.md"] = build_md(code, apps, categories)
        print(f"{code}: {len(apps)} apps")
    return files


def main():
    try:
        files = build()
    except Invalid as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    if "--check" in sys.argv[1:]:
        stale = [n for n, text in files.items() if not (DIST / n).exists() or (DIST / n).read_text(encoding="utf-8") != text]
        extra = [p.name for p in DIST.glob("*") if p.name not in files]
        if stale or extra:
            print(f"error: dist/ is not what a build makes ({', '.join(stale + extra)}); run python scripts/build.py", file=sys.stderr)
            return 1
        print("dist/ is current")
        return 0
    DIST.mkdir(exist_ok=True)
    for p in DIST.glob("*"):
        if p.name not in files:
            p.unlink()
    for n, text in files.items():
        (DIST / n).write_text(text, encoding="utf-8", newline="\n")
    print(f"built {len(files)} files in dist/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
