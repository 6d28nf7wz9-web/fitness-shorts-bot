
import json
import os

from google_auth_oauthlib.flow import Flow

# Needed because the redirect address is http://localhost
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

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

flow = Flow.from_client_config(
    config,
    scopes=SCOPES,
    redirect_uri=REDIRECT,
)

url, _ = flow.authorization_url(
    access_type="offline",
    prompt="consent",
    include_granted_scopes="true",
)

os.makedirs("output", exist_ok=True)

with open("output/auth_url.txt", "w", encoding="utf-8") as f:
    f.write(url)

print("\n1) Open this link in a NEW browser tab:\n")
print(url)

print("\n2) Sign in with the YouTube channel owner account.")
print("3) Approve all requested permissions.")
print("4) Copy the FULL address from the final browser page.")

response = input("\nPaste the full address here: ").strip()

if "code=" not in response:
    raise SystemExit("Authorization code not found in the supplied URL.")

flow.fetch_token(authorization_response=response)

creds = flow.credentials

if not creds.refresh_token:
    raise SystemExit(
        "No refresh token returned. Revoke the previous app access "
        "and run auth.py again with consent."
    )

with open("token.json", "w", encoding="utf-8") as f:
    json.dump(
        {"refresh_token": creds.refresh_token},
        f,
        indent=2,
    )

print("\nAuthorization successful!")
print("New refresh token saved in token.json.")
print("Update the YT_REFRESH_TOKEN GitHub Secret with this token.")
print("\nSaved token.json. You can now run upload.py")