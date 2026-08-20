#!/usr/bin/env python3
"""연결 테스트 — 설정이 끝났는지 확인용. config/.env 값을 읽어 계정 정보를 조회한다."""

import os
import sys

import requests

GRAPH_BASE = "https://graph.instagram.com"
API_VERSION = os.environ.get("IG_GRAPH_API_VERSION", "v23.0")


def main():
    ig_user_id = os.environ.get("IG_USER_ID")
    token = os.environ.get("IG_ACCESS_TOKEN")
    if not ig_user_id or not token:
        print("환경변수 IG_USER_ID, IG_ACCESS_TOKEN이 필요합니다. config/.env를 확인하세요.", file=sys.stderr)
        sys.exit(1)

    url = f"{GRAPH_BASE}/{API_VERSION}/{ig_user_id}"
    resp = requests.get(url, params={"fields": "id,username,account_type,media_count", "access_token": token})

    if resp.status_code != 200:
        print(f"연결 실패 ({resp.status_code}): {resp.text}", file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    print("연결 성공! 계정 정보:")
    for k, v in data.items():
        print(f"  {k}: {v}")

    if data.get("account_type") not in ("BUSINESS", "MEDIA_CREATOR"):
        print(
            "\n[경고] account_type이 BUSINESS/MEDIA_CREATOR가 아닙니다. "
            "00_SETUP_GUIDE.md 1단계(프로페셔널 계정 전환)를 다시 확인하세요.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
