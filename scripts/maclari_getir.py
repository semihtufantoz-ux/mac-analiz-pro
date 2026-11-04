
import os
import json
import urllib.request
import urllib.parse
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

API_KEY = os.environ["API_FOOTBALL_KEY"]
URL = "https://v3.football.api-sports.io/fixtures"

today = datetime.now(ZoneInfo("Europe/Istanbul")).date()
matches = []

for day in [today, today + timedelta(days=1)]:
    params = urllib.parse.urlencode({
        "date": day.isoformat(),
        "timezone": "Europe/Istanbul"
    })

    request = urllib.request.Request(
        URL + "?" + params,
        headers={"x-apisports-key": API_KEY}
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)

    if data.get("errors"):
        raise RuntimeError(str(data["errors"]))

    for item in data.get("response", []):
        matches.append({
            "id": item["fixture"]["id"],
            "date": item["fixture"]["date"],
            "league": item["league"]["name"],
            "country": item["league"]["country"],
            "home": item["teams"]["home"]["name"],
            "away": item["teams"]["away"]["name"],
            "status": item["fixture"]["status"]["short"],
            "goals": item["goals"]
        })

os.makedirs("data", exist_ok=True)

with open("data/maclar.json", "w", encoding="utf-8") as f:
    json.dump(matches, f, ensure_ascii=False, indent=2)

print(f"{len(matches)} maç kaydedildi.")
