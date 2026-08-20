#!/usr/bin/env python3
"""
fetch_oa_screenshot.py

CC-BY 오픈액세스 논문에 한해서만, 공개 PDF를 내려받아 지정한 페이지를
이미지로 렌더링한다. 저작권 문제 없이 캐러셀 2번 슬라이드(원본 논문
페이지)를 자동으로 채우기 위한 용도다.

반드시 지켜야 할 전제:
  - 이 스크립트는 reuse_mode가 'original_screenshot'(=CC-BY 확인됨)인
    경우에만 호출한다. auto_select.py/build_carousel.py 파이프라인에서
    이 조건을 확인 후에만 실행하도록 되어 있다.
  - CC-BY라도 출처 표기(저자/저널/DOI)는 캡션에 반드시 포함해야 한다
    (01_COPYRIGHT_POLICY.md 참고) — 이 스크립트는 이미지만 만들고
    출처 표기는 build_carousel.py의 마지막 슬라이드가 담당한다.
  - PDF가 없거나(폐쇄형) 다운로드가 실패하면 조용히 실패하지 않고
    명확히 에러를 내고 종료한다 — 이 경우 사람이 수동으로 스크린샷을
    끼워넣어야 한다 (build_carousel.py가 만드는 안내 파일 참고).
"""

import argparse
import sys

import fitz  # PyMuPDF
import requests


def download_pdf(url: str, out_path: str) -> None:
    resp = requests.get(url, timeout=30, headers={"User-Agent": "ig-science-agent/1.0"})
    resp.raise_for_status()
    content_type = resp.headers.get("Content-Type", "")
    if "pdf" not in content_type.lower() and not resp.content[:4] == b"%PDF":
        raise ValueError(f"응답이 PDF가 아닙니다 (Content-Type: {content_type}). URL 확인 필요: {url}")
    with open(out_path, "wb") as f:
        f.write(resp.content)


def render_page(pdf_path: str, page_number: int, out_png: str, zoom: float = 2.5) -> None:
    doc = fitz.open(pdf_path)
    if page_number >= len(doc):
        raise ValueError(f"PDF에 페이지 {page_number}가 없습니다 (총 {len(doc)}페이지).")
    page = doc[page_number]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    pix.save(out_png)


def main():
    parser = argparse.ArgumentParser(description="OA 논문 PDF의 특정 페이지를 이미지로 렌더링")
    parser.add_argument("--pdf-url", required=True, help="Unpaywall best_oa_location.url_for_pdf")
    parser.add_argument("--page", type=int, default=0, help="0-indexed 페이지 번호 (기본: 첫 페이지)")
    parser.add_argument("--out", required=True, help="출력 PNG 경로")
    parser.add_argument("--tmp-pdf", default="/tmp/_oa_paper.pdf")
    args = parser.parse_args()

    print(f"PDF 다운로드 중: {args.pdf_url}", file=sys.stderr)
    download_pdf(args.pdf_url, args.tmp_pdf)

    print(f"페이지 {args.page} 렌더링 중...", file=sys.stderr)
    render_page(args.tmp_pdf, args.page, args.out)

    print(f"저장 완료: {args.out}")


if __name__ == "__main__":
    main()
