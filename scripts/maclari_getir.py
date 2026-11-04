import os
import json
import urllib.request
import urllib.parse
import datetime
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

KEY = os.environ.get("API_FOOTBALL_KEY", "").strip()
BASE = "https://v3.football.api-sports.io"

LEAGUES = {
    39: ("İngiltere", "Premier League"),
    40: ("İngiltere", "Championship"),
    45: ("İngiltere", "FA Cup"),
    48: ("İngiltere", "EFL Cup"),
    78: ("Almanya", "Bundesliga"),
    79: ("Almanya", "2. Bundesliga"),
    81: ("Almanya", "DFB-Pokal"),
    140: ("İspanya", "La Liga"),
    141: ("İspanya", "La Liga 2"),
    143: ("İspanya", "Copa del Rey"),
    135: ("İtalya", "Serie A"),
    136: ("İtalya", "Serie B"),
    137: ("İtalya", "Coppa Italia"),
    88: ("Hollanda", "Eredivisie"),
    89: ("Hollanda", "Eerste Divisie"),
    90: ("Hollanda", "KNVB Kupası"),
    61: ("Fransa", "Ligue 1"),
    62: ("Fransa", "Ligue 2"),
    66: ("Fransa", "Coupe de France"),
    203: ("Türkiye", "Süper Lig"),
    204: ("Türkiye", "1. Lig"),
    206: ("Türkiye", "Türkiye Kupası"),
    2: ("Avrupa", "Şampiyonlar Ligi"),
    3: ("Avrupa", "Avrupa Ligi"),
    848: ("Avrupa", "Konferans Ligi"),
    531: ("Avrupa", "UEFA Süper Kupa"),
}

LIVE = {"1H", "2H", "HT", "ET", "BT", "P", "INT", "LIVE"}
FINISHED = {"FT", "AET", "PEN"}

def api_get(path, params=None):
    if not KEY:
        raise RuntimeError("API_FOOTBALL_KEY bulunamadi")
    url = BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url, headers={"x-apisports-key": KEY}
    )
    with urllib.request.urlopen(request, timeout=35) as response:
        result = json.load(response)
    if result.get("errors"):
        raise RuntimeError(str(result["errors"]))
    return result.get("response", [])

def convert(x):
    f = x["fixture"]
    l = x["league"]
    t = x["teams"]
    g = x.get("goals") or {}
    country, league = LEAGUES[l["id"]]
    return {
        "id": f["id"],
        "date": f["date"],
        "league_id": l["id"],
        "league": league,
        "country": country,
        "home": t["home"]["name"],
        "away": t["away"]["name"],
        "home_id": t["home"]["id"],
        "away_id": t["away"]["id"],
        "home_logo": t["home"].get("logo"),
        "away_logo": t["away"].get("logo"),
        "status": f["status"]["short"],
        "minute": f["status"].get("elapsed"),
        "goals": {
            "home": g.get("home"),
            "away": g.get("away")
        },
        "venue": (f.get("venue") or {}).get("name")
    }

def save_json(filename, value):
    (DATA / filename).write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def main():
    now = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=3))
    )
    dates = [
        (now + datetime.timedelta(days=i)).date().isoformat()
        for i in (-1, 0, 1)
    ]

    matches_by_id = {}
    successful_dates = 0

    for day in dates:
        try:
            rows = api_get("/fixtures", {
                "date": day,
                "timezone": "Europe/Istanbul"
            })
            successful_dates += 1
            count = 0
            for x in rows:
                if x["league"]["id"] in LEAGUES:
                    m = convert(x)
                    matches_by_id[m["id"]] = m
                    count += 1
            print(day, count, "selected matches")
        except Exception as error:
            print("Date skipped:", day, str(error))

    if successful_dates == 0:
        raise RuntimeError(
            "No accessible fixture dates. Existing data preserved."
        )

    matches = sorted(
        matches_by_id.values(), key=lambda m: m["date"]
    )

    if not matches:
        print("No selected matches. Existing data preserved.")
        return

    save_json("maclar.json", matches)
    print(len(matches), "matches saved")

    detail_path = DATA / "detaylar.json"
    try:
        details = json.loads(detail_path.read_text(encoding="utf-8"))
    except Exception:
        details = {}

    candidates = [m for m in matches if m["status"] in LIVE]
    candidates += [
        m for m in reversed(matches)
        if m["status"] in FINISHED
    ]

    for m in candidates[:2]:
        try:
            stats = api_get("/fixtures/statistics", {
                "fixture": m["id"]
            })
            if stats:
                details[str(m["id"])] = {
                    "statistics": stats,
                    "updated_at": now.isoformat()
                }
        except Exception as error:
            print("Statistics unavailable:", m["id"], str(error))

    valid_ids = {str(m["id"]) for m in matches}
    details = {
        k: v for k, v in details.items() if k in valid_ids
    }

    save_json("detaylar.json", details)
    save_json("guncelleme.json", {
        "updated_at": now.isoformat(),
        "fixtures": len(matches),
        "successful_dates": successful_dates
    })
    print("Update completed successfully")

if __name__ == "__main__":
    main()
