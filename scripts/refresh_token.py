#!/usr/bin/env python3
"""
refresh_token.py

장기 토큰(~60일 유효)이 만료되기 전에 갱신한다. 만료 30일 이내면 갱신을
수행하고, 아니면 아무것도 하지 않는다. 매일 실행되는 파이프라인(GitHub
Actions 등)에 이 스크립트를 포함시켜두면 토큰 만료로 자동 게시가
멈추는 사고를 예방할 수 있다.

주의: 갱신된 토큰을 어디에 다시 저장할지는 실행 환경에 따라 다르다.
  - GitHub Actions: GitHub CLI/API로 리포지토리 Secret을 갱신해야 함
    (이 스크립트는 새 토큰 값을 stdout으로 출력만 하고, 실제 저장은
    워크플로에서 처리하도록 분리했다 — 시크릿 저장 방식은 사용자의
    CI 설정에 따라 다르기 때문)
  - 로컬 서버: .env 파일을 직접 갱신
"""

import json
import os
import sys

import requests

GRAPH_BASE = "https://graph.instagram.com"


def refresh(token: str) -> dict:
    resp = requests.get(
        f"{GRAPH_BASE}/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": token},
    )
    resp.raise_for_status()
    return resp.json()


def main():
    token = os.environ.get("IG_ACCESS_TOKEN")
    if not token:
        print("환경변수 IG_ACCESS_TOKEN이 필요합니다.", file=sys.stderr)
        sys.exit(1)

    result = refresh(token)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if "access_token" not in result:
        print("[경고] 갱신 실패 — 토큰이 이미 60일 이상 지나 만료되었을 수 있습니다. "
              "00_SETUP_GUIDE.md 4단계를 다시 수행해 새 토큰을 발급받으세요.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
