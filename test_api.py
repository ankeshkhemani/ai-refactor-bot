import os
import jwt
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("GITHUB_APP_ID")
PRIVATE_KEY_PATH = os.getenv("GITHUB_PRIVATE_KEY_PATH")
INSTALLATION_ID = os.getenv("GITHUB_INSTALLATION_ID")  # you'll set this manually for now

# Generate JWT
with open(PRIVATE_KEY_PATH, "rb") as f:
    private_key = f.read()

payload = {
    "iat": int(time.time()) - 60,
    "exp": int(time.time()) + (10 * 60),
    "iss": APP_ID
}

jwt_token = jwt.encode(payload, private_key, algorithm="RS256")

# Get installation access token
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Accept": "application/vnd.github+json"
}

installation_url = f"https://api.github.com/app/installations/{INSTALLATION_ID}/access_tokens"

response = httpx.post(installation_url, headers=headers)
access_token = response.json()["token"]

# Use the token to fetch repo info
repo_owner = "ankeshkhemani"
repo_name = "CarND-Behavioral-Cloning-Project"

headers = {
    "Authorization": f"token {access_token}",
    "Accept": "application/vnd.github+json"
}

repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
r = httpx.get(repo_url, headers=headers)

print("Repo info:", r.json())
