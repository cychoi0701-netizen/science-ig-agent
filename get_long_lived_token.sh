#!/usr/bin/env bash
# 단기(short-lived) 액세스 토큰을 장기(long-lived, ~60일) 토큰으로 교환한다.
# 사용법: ./get_long_lived_token.sh <APP_SECRET> <SHORT_LIVED_TOKEN>

set -euo pipefail

APP_SECRET="${1:?App Secret을 첫 번째 인자로 넘겨주세요}"
SHORT_TOKEN="${2:?단기 토큰을 두 번째 인자로 넘겨주세요}"

curl -sS -G "https://graph.instagram.com/access_token" \
  --data-urlencode "grant_type=ig_exchange_token" \
  --data-urlencode "client_secret=${APP_SECRET}" \
  --data-urlencode "access_token=${SHORT_TOKEN}" | python3 -m json.tool

echo ""
echo "위 응답의 access_token 값을 config/.env 의 IG_ACCESS_TOKEN에 저장하세요."
echo "expires_in은 초 단위이며 보통 약 5,184,000초(60일)입니다."
