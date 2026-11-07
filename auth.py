
import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

REDIRECT = "http://localhost:8080/"

flow = InstalledAppFlow.from_client_secrets_file(
    "client_secret.json",
    scopes=SCOPES,
    autogenerate_code_verifier=True,
)

flow.redirect_uri = REDIRECT

url, _ = flow.authorization_url(
    access_type="offline",
    prompt="consent",
    include_granted_scopes="true",
)

print("\nOpen this URL in your browser:\n")
print(url)

response = input(
    "\nPaste the FULL callback URL here: "
).strip()

if "code=" not in response:
    raise SystemExit("Authorization code not found.")

flow.fetch_token(authorization_response=response)

creds = flow.credentials

if not creds.refresh_token:
    raise SystemExit(
        "No refresh token returned. Revoke app access and retry."
    )

os.makedirs("output", exist_ok=True)

with open("token.json", "w", encoding="utf-8") as f:
    json.dump(
        {"refresh_token": creds.refresh_token},
        f,
        indent=2,
    )

print("\nAuthorization successful!")
print("Refresh token saved in token.json")
