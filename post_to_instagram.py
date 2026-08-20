#!/usr/bin/env python3
"""
post_to_instagram.py

로컬에 생성해둔 캐러셀 이미지들 + 캡션을 Instagram Graph API로 게시한다.

전제:
  - 이미지가 공개적으로 접근 가능한 URL이어야 한다 (Graph API는 파일 업로드가
    아니라 이미지 URL을 참조하는 방식). 로컬 PNG를 그대로 쓸 수 없으므로,
    먼저 어딘가에 업로드해서 URL을 얻어야 한다 (예: 본인 소유의 정적 파일
    호스팅, S3, Cloudflare R2, GitHub raw 등). 이 스크립트는 URL 업로드
    단계는 포함하지 않는다 — 각자 인프라에 맞게 upload_images_and_get_urls()를
    구현해서 연결한다.

절차 (캐러셀):
  1. 각 이미지 URL로 개별 미디어 컨테이너 생성 (is_carousel_item=true)
  2. 모든 개별 컨테이너 ID를 모아 부모 컨테이너 생성 (media_type=CAROUSEL)
  3. 부모 컨테이너를 publish

실행 전 반드시:
  - config/.env 에 IG_USER_ID, IG_ACCESS_TOKEN 설정
  - templates/review_checklist.md 검수 완료
"""

import argparse
import os
import sys
import time

import requests

GRAPH_BASE = "https://graph.instagram.com"
API_VERSION = os.environ.get("IG_GRAPH_API_VERSION", "v23.0")
# 2026년 8월 기준 v25.0까지 공개되어 있음을 확인했으나, 오래된 버전은 주기적으로
# sunset(지원 종료)되므로 실행 전 반드시 최신 changelog에서 확인/갱신하세요:
# https://developers.facebook.com/docs/graph-api/changelog
# 필요시 환경변수 IG_GRAPH_API_VERSION으로 덮어쓸 수 있습니다.


def check_rate_limit(ig_user_id: str, token: str) -> None:
    url = f"{GRAPH_BASE}/{API_VERSION}/{ig_user_id}/content_publishing_limit"
    resp = requests.get(url, params={"access_token": token})
    resp.raise_for_status()
    data = resp.json()
    print(f"[rate limit] {data}", file=sys.stderr)


def create_item_container(ig_user_id: str, token: str, image_url: str) -> str:
    url = f"{GRAPH_BASE}/{API_VERSION}/{ig_user_id}/media"
    resp = requests.post(
        url,
        data={
            "image_url": image_url,
            "is_carousel_item": "true",
            "access_token": token,
        },
    )
    resp.raise_for_status()
    return resp.json()["id"]


def create_carousel_container(ig_user_id: str, token: str, children_ids: list[str], caption: str) -> str:
    url = f"{GRAPH_BASE}/{API_VERSION}/{ig_user_id}/media"
    resp = requests.post(
        url,
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(children_ids),
            "caption": caption,
            "access_token": token,
        },
    )
    resp.raise_for_status()
    return resp.json()["id"]


def publish_container(ig_user_id: str, token: str, container_id: str) -> dict:
    url = f"{GRAPH_BASE}/{API_VERSION}/{ig_user_id}/media_publish"
    resp = requests.post(
        url,
        data={"creation_id": container_id, "access_token": token},
    )
    resp.raise_for_status()
    return resp.json()


def wait_until_container_ready(container_id: str, token: str, timeout_s: int = 60) -> None:
    """캐러셀 자식 컨테이너가 Meta 서버에서 이미지 처리를 마칠 때까지 대기.
    바로 publish하면 IMAGE_NOT_READY 에러가 날 수 있어 status_code를 폴링한다."""
    url = f"{GRAPH_BASE}/{API_VERSION}/{container_id}"
    start = time.time()
    while time.time() - start < timeout_s:
        resp = requests.get(url, params={"fields": "status_code", "access_token": token})
        resp.raise_for_status()
        status = resp.json().get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError(f"컨테이너 처리 실패: {container_id}")
        time.sleep(3)
    raise TimeoutError(f"컨테이너 준비 대기 타임아웃: {container_id}")


def main():
    parser = argparse.ArgumentParser(description="Instagram 캐러셀 게시")
    parser.add_argument("--image-urls", nargs="+", required=True,
                         help="공개 접근 가능한 이미지 URL 목록 (순서대로 캐러셀에 반영)")
    parser.add_argument("--caption-file", required=True, help="캡션 텍스트 파일 경로")
    parser.add_argument("--dry-run", action="store_true", help="실제 게시 없이 흐름만 검증")
    args = parser.parse_args()

    ig_user_id = os.environ.get("IG_USER_ID")
    token = os.environ.get("IG_ACCESS_TOKEN")
    if not ig_user_id or not token:
        print("환경변수 IG_USER_ID, IG_ACCESS_TOKEN이 필요합니다. config/.env를 확인하세요.", file=sys.stderr)
        sys.exit(1)

    with open(args.caption_file, encoding="utf-8") as f:
        caption = f.read().strip()

    if args.dry_run:
        print("[dry-run] 아래 이미지로 캐러셀을 게시할 예정입니다 (실제 게시 안 함):")
        for u in args.image_urls:
            print(f"  - {u}")
        print(f"[dry-run] 캡션 미리보기:\n{caption[:200]}...")
        return

    check_rate_limit(ig_user_id, token)

    print("개별 미디어 컨테이너 생성 중...", file=sys.stderr)
    child_ids = []
    for url in args.image_urls:
        cid = create_item_container(ig_user_id, token, url)
        wait_until_container_ready(cid, token)
        child_ids.append(cid)
        print(f"  준비 완료: {cid}", file=sys.stderr)

    print("캐러셀(부모) 컨테이너 생성 중...", file=sys.stderr)
    parent_id = create_carousel_container(ig_user_id, token, child_ids, caption)
    wait_until_container_ready(parent_id, token)

    print("게시 중...", file=sys.stderr)
    result = publish_container(ig_user_id, token, parent_id)
    print(f"게시 완료: {result}")


if __name__ == "__main__":
    main()
