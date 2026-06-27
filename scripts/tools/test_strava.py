# test_strava.py
import os, requests, json
from dotenv import load_dotenv
load_dotenv()

def get_access_token():
    r = requests.post("https://www.strava.com/oauth/token", data={
        "client_id": os.environ["STRAVA_CLIENT_ID"],
        "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
        "refresh_token": os.environ["STRAVA_REFRESH_TOKEN"],
        "grant_type": "refresh_token"
    })
    data = r.json()
    print(f"Token refresh status: {r.status_code}")
    print(f"Scopes: {data.get('scope', 'NOT RETURNED — check below')}")
    return data["access_token"]

token = get_access_token()
headers = {"Authorization": f"Bearer {token}"}

# Test 1: Athlete info
me = requests.get("https://www.strava.com/api/v3/athlete", headers=headers).json()
print(f"\n✅ Connected as: {me.get('firstname')} {me.get('lastname')}")

# Test 2: Activities — with full debugging
print("\n--- Fetching activities ---")
resp = requests.get("https://www.strava.com/api/v3/athlete/activities",
                    headers=headers, params={"per_page": 5})
print(f"Status: {resp.status_code}")
print(f"Response type: {type(resp.json())}")
print(f"Raw response:\n{json.dumps(resp.json(), indent=2)[:500]}")

acts = resp.json()
if isinstance(acts, dict):
    print("\n❌ Got error dict instead of list — see message above.")
    print("Most likely: missing 'activity:read_all' scope.")
elif isinstance(acts, list):
    print(f"\n✅ Got {len(acts)} activities:\n")
    for a in acts:
        print(f"  {a['start_date'][:10]} | {a['type']:10} | "
              f"{a['distance']/1000:.1f} km | {a['name']}")