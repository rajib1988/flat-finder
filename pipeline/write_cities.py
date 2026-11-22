"""Write web/public/data/cities.json listing every city whose data has been built, in data/cities.json order."""
import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
WEB = ROOT / "web" / "public" / "data"
cfg = json.loads((ROOT / "data" / "cities.json").read_text())
built = {p.stem for p in WEB.glob("*.json")}
cities = {c: {"name": v["name"]} for c, v in cfg.items() if c in built}
(WEB / "cities.json").write_text(json.dumps(cities))
print("cities on the site:", ", ".join(cities))
