import os
import asyncio
from flask import Flask, request
from gidgethub import routing, sansio
from gidgethub.apps import get_installation_access_token
from dotenv import load_dotenv
import jwt

load_dotenv()

app = Flask(__name__)
router = routing.Router()

GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

"""
# For Private Repo
PRIVATE_KEY_PATH = os.getenv("GITHUB_PRIVATE_KEY_PATH")

with open(PRIVATE_KEY_PATH, "rb") as key_file:
    PRIVATE_KEY = key_file.read()
"""

# For Public repo using railway
PRIVATE_KEY = os.getenv("PRIVATE_KEY").encode()

@app.route("/ping", methods=["GET"])
def ping():
    return "pong", 200
    
# GitHub event handler
@router.register("push")
async def handle_push_event(event, gh, *args, **kwargs):
	print(f"Push to {event.data['repository']['full_name']} by {event.data['sender']['login']}")

"""
// Original webhook func

@app.route("/webhook", methods=["POST"])
def webhook():
    event = sansio.Event.from_http(request.headers, request.get_data(), secret=WEBHOOK_SECRET)
    asyncio.run(router.dispatch(event, gh=None))  # No gh client yet
    return "", 204
"""

@app.route("/webhook", methods=["POST"])
def webhook():
    event_type = request.headers.get("X-GitHub-Event", "ping")
    payload = request.get_json()
    print(f"📦 Received GitHub event: {event_type}")
    print(payload)
    return "", 204


def generate_jwt():
    return jwt.encode(
        {
            "iat": int(time.time()),
            "exp": int(time.time()) + (10 * 60),
            "iss": GITHUB_APP_ID
        },
        PRIVATE_KEY,
        algorithm="RS256"
    )
"""
if __name__ == "__main__":
    app.run(port=3000)
"""
# For railway
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)