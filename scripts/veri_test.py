import os
import json
import urllib.request
import urllib.error

API_KEY = os.environ.get('API_FOOTBALL_KEY', '').strip()
URL = 'https://v3.football.api-sports.io/status'

def main():
    if not API_KEY:
        print('API_FOOTBALL_KEY ayarlanmamis.')
        return

    request = urllib.request.Request(
        URL,
        headers={'x-apisports-key': API_KEY}
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.load(response)
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except urllib.error.HTTPError as error:
        print('HTTP hatasi:', error.code)
    except Exception as error:
        print('Baglanti hatasi:', error)

if __name__ == '__main__':
    main()

