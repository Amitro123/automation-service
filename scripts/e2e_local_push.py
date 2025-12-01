# scripts/e2e_local_push.py

import os
import json
import hmac
import hashlib
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = "http://localhost:8080/webhook"
SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "dev-secret")

# Adjust this path to any sample push payload you already have in tests
SAMPLE_PAYLOAD_PATH = Path("tests") / "data" / "sample_push_event.json"


def load_payload() -> str:
    if SAMPLE_PAYLOAD_PATH.is_file():
        with SAMPLE_PAYLOAD_PATH.open("r", encoding="utf-8") as f:
            return f.read()
    # Fallback minimal fake push event
    payload = {
        "ref": "refs/heads/main",
        "repository": {
            "full_name": os.getenv("REPOSITORY_OWNER", "your_username")
            + "/"
            + os.getenv("REPOSITORY_NAME", "your_repo")
        },
        "head_commit": {
            "id": "abc123",
            "message": "test: E2E local webhook",
        },
    }
    return json.dumps(payload)


def make_signature(body: str) -> str:
    mac = hmac.new(
        SECRET.encode("utf-8"),
        msg=body.encode("utf-8"),
        digestmod=hashlib.sha256,
    )
    return "sha256=" + mac.hexdigest()


def main() -> None:
    body = load_payload()
    signature = make_signature(body)

    headers = {
        "X-Hub-Signature-256": signature,
        "X-GitHub-Event": "push",
        "Content-Type": "application/json",
    }

    print(f"POST {WEBHOOK_URL}")
    resp = requests.post(WEBHOOK_URL, data=body, headers=headers, timeout=30)
    print("Status:", resp.status_code)
    print("Response:", resp.text)


if __name__ == "__main__":
    main()
