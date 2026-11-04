import os, json, urllib.request, urllib.parse, datetime, pathlib, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
DATA.mkdir(exist_ok=True)
KEY = os.environ.get('API_FOOTBALL_KEY', '').strip()
BASE = 'https://v3.football.api-sports.io'

LEAGUES = {
    39: ('İngiltere','Premier League'), 40: ('İngiltere','Championship'),
    45: ('İngiltere','FA Cup'), 48: ('İngiltere','EFL Cup'),
    78: ('Almanya','Bundesliga'), 79: ('Almanya','2. Bundesliga'),
    81: ('Almanya','DFB-Pokal'),
    140: ('İspanya','La Liga'), 141: ('İspanya','La Liga 2'),
    143: ('İspanya','Copa del Rey'),
    135: ('İtalya','Serie A'), 136: ('İtalya','Serie B'),
    137: ('İtalya','Coppa Italia'),
    88: ('Hollanda','Eredivisie'), 89: ('Hollanda','Eerste Divisie'),
    90: ('Hollanda','KNVB Kupası'),
    61: ('Fransa','Ligue 1'), 62: ('Fransa','Ligue 2'),
    66: ('Fransa','Coupe de France'),
    203: ('Türkiye','Süper Lig'), 204: ('Türkiye','1. Lig'),
    206: ('Türkiye','Türkiye Kupası'),
    2: ('Avrupa','Şampiyonlar Ligi'), 3: ('Avrupa','Avrupa Ligi'),
    848: ('Avrupa','Konferans Ligi'), 531: ('Avrupa','UEFA Süper Kupa'),
}
LIVE = {'1H','2H','HT','ET','BT','P','INT','LIVE'}
FINISHED = {'FT','AET','PEN'}

def get(path, params=None):
    if not KEY:
        raise RuntimeError('API_FOOTBALL_KEY GitHub secret eksik')
    url = BASE + path + ('?' + urllib.parse.urlencode(params) if params else '')
    req = urllib.request.Request(url, headers={'x-apisports-key': KEY})
    with urllib.request.urlopen(req, timeout=35) as response:
        payload = json.load(response)
    if payload.get('errors'):
        raise RuntimeError(str(payload['errors']))
    return payload.get('response', []), payload.get('results', 0)

def fixture_record(x):
    f = x['fixture']
    l = x['league']
    t = x['teams']
    g = x.get('goals') or {}
    country, league = LEAGUES[l['id']]
    return {
        'id': f['id'], 'date': f['date'], 'league_id': l['id'],
        'league': league, 'country': country,
        'home': t['home']['name'], 'away': t['away']['name'],
        'home_id': t['home']['id'], 'away_id': t['away']['id'],
        'home_logo': t['home'].get('logo'), 'away_logo': t['away'].get('logo'),
        'status': f['status']['short'],
        'minute': f['status'].get('elapsed'),
        'goals': {'home': g.get('home'), 'away': g.get('away')},
        'venue': (f.get('venue') or {}).get('name')
    }

def main():
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=3)))
    dates = [(now + datetime.timedelta(days=i)).date().isoformat()
             for i in (-1, 0, 1, 2)]
    all_fixtures = {}

    for day in dates:
        rows, count = get('/fixtures', {
            'date': day, 'timezone': 'Europe/Istanbul'
        })
        for x in rows:
            if x['league']['id'] in LEAGUES:
                rec = fixture_record(x)
                all_fixtures[rec['id']] = rec
        print(day, count, 'API fixtures')

    matches = sorted(all_fixtures.values(), key=lambda r: r['date'])
    (DATA / 'maclar.json').write_text(
        json.dumps(matches, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    print(len(matches), 'selected matches saved')

    detail_file = DATA / 'detaylar.json'
    try:
        details = json.loads(detail_file.read_text(encoding='utf-8')) if detail_file.exists() else {}
    except Exception:
        details = {}

    candidates = [m for m in matches if m['status'] in LIVE]
    candidates += [
        m for m in reversed(matches)
        if m['status'] in FINISHED and m not in candidates
    ]

    for m in candidates[:3]:
        try:
            rows, _ = get('/fixtures/statistics', {'fixture': m['id']})
            if rows:
                details[str(m['id'])] = {
                    'statistics': rows,
                    'updated_at': now.isoformat()
                }
            time.sleep(0.25)
        except Exception as e:
            print('stats unavailable', m['id'], str(e))

    keep = {str(m['id']) for m in matches}
    details = {k: v for k, v in details.items() if k in keep}

    detail_file.write_text(
        json.dumps(details, ensure_ascii=False), encoding='utf-8'
    )
    (DATA / 'guncelleme.json').write_text(
        json.dumps({
            'updated_at': now.isoformat(),
            'fixtures': len(matches)
        }, ensure_ascii=False),
        encoding='utf-8'
    )

if __name__ == '__main__':
    main()
