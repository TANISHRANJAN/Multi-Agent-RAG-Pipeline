import json
import os
import sys
from urllib.parse import urlparse

import requests


def main() -> int:
    base_url = os.getenv("DEPLOY_HEALTH_URL", "").strip().rstrip("/")
    if not base_url:
        print("ERROR: Set DEPLOY_HEALTH_URL to the deployed API's /health URL.", file=sys.stderr)
        return 2

    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        print("ERROR: DEPLOY_HEALTH_URL must be a valid http(s) URL.", file=sys.stderr)
        return 2

    try:
        response = requests.get(base_url, timeout=20)
        print("Health endpoint HTTP status:", response.status_code)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, json.JSONDecodeError) as exc:
        print(f"DEPLOYMENT VALIDATION FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if not isinstance(payload, dict) or payload.get("status") != "ok":
        print("DEPLOYMENT VALIDATION FAILED: health JSON did not contain status='ok'.", file=sys.stderr)
        return 1

    print("DEPLOYMENT VALIDATION PASSED")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
