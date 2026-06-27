# oauth_setup.py
import os, webbrowser, requests
from urllib.parse import urlencode
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.environ["STRAVA_CLIENT_ID"]
CLIENT_SECRET = os.environ["STRAVA_CLIENT_SECRET"]

# Build authorization URL
params = {
    "client_id": CLIENT_ID,
    "redirect_uri": "http://localhost/exchange_token",
    "response_type": "code",
    "approval_prompt": "force",
    "scope": "read,activity:read_all,profile:read_all"
}
auth_url = "https://www.strava.com/oauth/authorize?" + urlencode(params)

print("\n=== STEP 1: Open this URL in your browser ===\n")
print(auth_url)
print("\n=== STEP 2: Authorize, then copy the 'code' from the redirected URL ===")
print("URL will look like: http://localhost/exchange_token?state=&code=ABC123XYZ&scope=...")
print("(The page won't load — that's normal! Just copy the code value)\n")

try:
    webbrowser.open(auth_url)
except:
    pass

code = input("Paste the code value here: ").strip()

# Exchange code for tokens
print("\nExchanging code for tokens...")
r = requests.post("https://www.strava.com/oauth/token", data={
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "code": code,
    "grant_type": "authorization_code"
})

data = r.json()
if "refresh_token" not in data:
    print("ERROR:", data)
    exit(1)

print("\n✅ SUCCESS!\n")
print(f"Access Token:  {data['access_token']}")
print(f"Refresh Token: {data['refresh_token']}")
print(f"Expires at:    {data['expires_at']}")
print(f"Athlete:       {data['athlete']['firstname']} {data['athlete']['lastname']}")

print("\n👉 Add this to your .env file:")
print(f"STRAVA_REFRESH_TOKEN={data['refresh_token']}")