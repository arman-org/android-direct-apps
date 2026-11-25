# android-direct-apps

Android apps that should connect directly, not through a VPN: the banks,
payment apps, government services, operators, messengers, and stores of a
country that refuse a foreign address or only work from inside it. VPN and
proxy apps use these lists to leave such apps out of the tunnel.

Each app is listed with its Persian and English name, a category, the
stores it is in, and how often it was installed; what clients download is
only the package names. The
lists are kept by hand.

| Country | List | Browse |
| --- | --- | --- |
| Iran | [dist/ir.json](dist/ir.json) | [dist/ir.md](dist/ir.md) |
| Russia | [dist/ru.json](dist/ru.json) | [dist/ru.md](dist/ru.md) |

## Download

```
https://raw.githubusercontent.com/arman-org/android-direct-apps/main/dist/ir.json
https://cdn.jsdelivr.net/gh/arman-org/android-direct-apps@main/dist/ir.json
```

```json
{
 "country": "ir",
 "apps": [
  "cab.snapp.passenger",
  "ir.mci.ecareapp"
 ]
}
```

Only the package names: the names, categories, and stores in
`countries/` and `dist/<code>.md` are for reading and editing the lists.

## Adding or changing an app

1. Edit `countries/<code>.yaml`:

   ```yaml
   - package: ir.mci.ecareapp
     name: { fa: همراه من, en: MyMCI }
     category: telecom
     stores: [bazaar, myket, play]
     installs: { myket: 32000000 }      # optional: download counts by store
     note: Refuses a foreign address.   # optional: why it connects directly
   ```

   `category` is one of [categories.yaml](categories.yaml); `stores` are
   some of `bazaar`, `myket`, `play`, and the links are made from them.
   `installs` is what a store showed when last checked (Myket's download
   count for now); `dist/<code>.md` lists each category's apps by it, the
   most installed first.
2. Build: `pip install pyyaml`, then `python scripts/build.py`.
3. Commit the list and `dist/` together. Every push is checked (Actions,
   Check): package names, categories, no app twice, and `dist/` current.

A new country is a new `countries/<two-letter code>.yaml`.
