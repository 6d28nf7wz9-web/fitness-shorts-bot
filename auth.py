import json
import os

from google_auth_oauthlib.flow import Flow

# Needed because the redirect address is http://localhost
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
REDIRECT = "http://localhost:8080/"

config = {
    "installed": {
        "client_id": os.environ["YT_CLIENT_ID"],
        "client_secret": os.environ["YT_CLIENT_SECRET"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [REDIRECT],
    }
}

flow = Flow.from_client_config(config, scopes=SCOPES, redirect_uri=REDIRECT)
url, _ = flow.authorization_url(access_type="offline", prompt="consent")

os.makedirs("output", exist_ok=True)
with open("output/auth_url.txt", "w") as f:
    f.write(url)

print("\n1) Open this link in a NEW browser tab (also saved in output/auth_url.txt):\n")
print(url)
print("\n2) Sign in, allow access. The final page will fail to load. That is normal.")
print("3) Copy the FULL address from the address bar of that failed page.\n")

response = input("Paste the full address here and press Enter: ").strip()
if "code=" not in response:
    raise SystemExit("That doesn't contain 'code='. Paste the full address.")

flow.fetch_token(authorization_response=response)
creds = flow.credentials
if not creds.refresh_token:
    raise SystemExit("No refresh token returned. Run again and approve all permissions.")

with open("token.json", "w") as f:
    json.dump({"refresh_token": creds.refresh_token}, f)
print("\nSaved token.json. You can now run upload.py")