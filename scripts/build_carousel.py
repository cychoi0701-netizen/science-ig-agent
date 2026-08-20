#!/usr/bin/env python3
"""
build_carousel.py

conceptual advance 분석 결과(JSON, draft_conceptual_advance.py 출력 또는
사람이 검수한 최종본)로부터 인스타그램 캐러셀용 슬라이드 이미지를 생성한다.

슬라이드 구성:
  1. 후킹 슬라이드 (hook line)
  2. 논문 원본 스크린샷 자리 — reuse_mode가 original_screenshot일 때만 실제 스크린샷을
     별도로 준비해 이 자리에 끼워넣는다 (이 스크립트는 스크린샷을 대신 만들지 않는다 —
     저작권 판단은 사람이 최종 확인해야 하므로 자동 크롤링/캡처하지 않는다).
     reuse_mode가 custom_graphic이면 이 슬라이드 대신 핵심 결과를 텍스트로 요약한
     자체 제작 슬라이드를 생성한다.
  3. "Conceptual Advance" 박스 (기존 통념 vs 이번 발견)
  4. 한계(limitations) + 출처(저자/저널/DOI) 슬라이드

인스타그램 정사각형 캐러셀 표준 해상도 1080x1080을 사용한다.
"""

import argparse
import json
import os
import textwrap

from PIL import Image, ImageDraw, ImageFont

CANVAS = 1080
MARGIN = 80
BG = (250, 248, 244)
FG = (20, 20, 20)
ACCENT = (196, 30, 58)  # 브랜드 컬러 — 원하는 색으로 바꿔도 됨
MUTED = (110, 110, 110)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    # 시스템에 흔히 있는 DejaVu 폰트를 기본으로 사용 (한글 지원 필요시
    # 아래 candidates에 한글 폰트 경로를 추가해야 함 — README 참고)
    candidates_bold = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    candidates_reg = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in (candidates_bold if bold else candidates_reg):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap_and_draw(draw, text, font, x, y, max_width, fill, line_spacing=1.3, char_wrap=18):
    lines = textwrap.wrap(text, width=char_wrap, break_on_hyphens=False, break_long_words=False)
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        bbox = draw.textbbox((0, 0), line, font=font)
        y += int((bbox[3] - bbox[1]) * line_spacing)
    return y


def _wrap_by_pixel_width(draw, text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if draw.textlength(trial, font=font) <= max_width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_and_draw(draw, text, x, y, max_width, max_height, fill, bold=False,
                  start_size=36, min_size=22, line_spacing=1.3):
    """텍스트 길이가 가변적이므로, 주어진 박스(max_width x max_height)를 넘지 않을 때까지
    폰트 크기를 단계적으로 줄여가며 맞춘다. 캐러셀 이미지가 캔버스 밖으로 잘리는 것을
    방지하는 안전장치."""
    size = start_size
    lines, font, line_h = [], None, 0
    while size >= min_size:
        font = load_font(size, bold=bold)
        lines = _wrap_by_pixel_width(draw, text, font, max_width)
        bbox = draw.textbbox((0, 0), "Ag", font=font)
        line_h = int((bbox[3] - bbox[1]) * line_spacing)
        if line_h * len(lines) <= max_height:
            break
        size -= 2

    cy = y
    for line in lines:
        draw.text((x, cy), line, font=font, fill=fill)
        cy += line_h
    return cy


def slide_hook(hook_line: str, kicker: str = "SCIENCE BREAKTHROUGH") -> Image.Image:
    img = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, CANVAS, 12], fill=ACCENT)
    kicker_font = load_font(32, bold=True)
    hook_font = load_font(56, bold=True)
    draw.text((MARGIN, 140), kicker, font=kicker_font, fill=ACCENT)
    wrap_and_draw(draw, hook_line, hook_font, MARGIN, 220, CANVAS - 2 * MARGIN, FG, char_wrap=22, line_spacing=1.25)
    return img


def slide_custom_graphic(what_this_paper_shows: str, journal: str) -> Image.Image:
    """구독형(비오픈) 논문용 — 원본 figure 대신 자체 요약 슬라이드."""
    img = Image.new("RGB", (CANVAS, CANVAS), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, CANVAS, 12], fill=ACCENT)
    title_font = load_font(40, bold=True)
    draw.text((MARGIN, 100), "What they found", font=title_font, fill=ACCENT)
    fit_and_draw(draw, what_this_paper_shows, MARGIN, 190, CANVAS - 2 * MARGIN, CANVAS - 190 - 140,
                 FG, start_size=38, min_size=24)
    footer_font = load_font(24)
    draw.text(
        (MARGIN, CANVAS - 80),
        f"* Recreated as original graphic per {journal} reuse policy",
        font=footer_font,
        fill=MUTED,
    )
    return img


def slide_prior_consensus(prior: str) -> Image.Image:
    img = Image.new("RGB", (CANVAS, CANVAS), (25, 25, 28))
    draw = ImageDraw.Draw(img)
    label_font = load_font(30, bold=True)
    draw.text((MARGIN, 100), "WHAT WE THOUGHT", font=label_font, fill=(180, 180, 180))
    fit_and_draw(draw, prior, MARGIN, 170, CANVAS - 2 * MARGIN, CANVAS - 170 - 100,
                 (210, 210, 210), start_size=42, min_size=26)
    return img


def slide_conceptual_advance(advance: str) -> Image.Image:
    img = Image.new("RGB", (CANVAS, CANVAS), (25, 25, 28))
    draw = ImageDraw.Draw(img)
    label_font = load_font(30, bold=True)
    draw.rectangle([0, 0, CANVAS, 12], fill=ACCENT)
    draw.text((MARGIN, 100), "THE CONCEPTUAL ADVANCE", font=label_font, fill=ACCENT)
    fit_and_draw(draw, advance, MARGIN, 170, CANVAS - 2 * MARGIN, CANVAS - 170 - 100,
                 (255, 255, 255), start_size=42, min_size=26)
    return img


def slide_limitations_source(limitations: str, authors_short: str, journal: str, doi: str) -> Image.Image:
    img = Image.new("RGB", (CANVAS, CANVAS), BG)
    draw = ImageDraw.Draw(img)
    label_font = load_font(30, bold=True)
    source_font = load_font(26)

    draw.text((MARGIN, 100), "Limitations & open questions", font=label_font, fill=ACCENT)
    # 하단 출처 블록(약 130px)을 위해 본문 높이를 제한해둔다.
    fit_and_draw(draw, limitations, MARGIN, 160, CANVAS - 2 * MARGIN, CANVAS - 160 - 260,
                 FG, start_size=34, min_size=22)

    y = CANVAS - 260
    draw.line([(MARGIN, y), (CANVAS - MARGIN, y)], fill=(200, 200, 200), width=2)
    y += 30
    draw.text((MARGIN, y), f"{authors_short}", font=source_font, fill=MUTED)
    y += 40
    draw.text((MARGIN, y), f"{journal} · DOI: {doi}", font=source_font, fill=MUTED)
    return img


def main():
    parser = argparse.ArgumentParser(description="Conceptual advance JSON으로부터 캐러셀 이미지 생성")
    parser.add_argument("--analysis", required=True, help="사람이 검수 완료한 conceptual advance JSON 경로")
    parser.add_argument("--journal", required=True)
    parser.add_argument("--authors-short", required=True, help='예: "Füchtbauer L, et al."')
    parser.add_argument("--reuse-mode", required=True,
                         choices=["original_screenshot", "original_screenshot_restricted",
                                  "original_screenshot_check", "custom_graphic"])
    parser.add_argument("--screenshot-path", default=None,
                         help="fetch_oa_screenshot.py 등으로 미리 렌더링해둔 논문 페이지 PNG 경로. "
                              "제공되면 2번 슬라이드로 바로 끼워넣는다 (CC-BY 케이스에서 완전 자동화 가능). "
                              "제공되지 않으면 빈 자리 안내 파일만 만든다.")
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    with open(args.analysis, encoding="utf-8") as f:
        a = json.load(f)

    os.makedirs(args.out_dir, exist_ok=True)

    # 5개의 고정 슬롯(01~05)으로 관리한다. 슬롯 2(스크린샷)가 비어 있어도
    # 번호를 당겨쓰지 않는다 — 나중에 스크린샷을 끼워넣을 때 파일명 번호와
    # 실제 캐러셀 순서가 어긋나는 것을 방지하기 위함이다.
    # (이전 버전은 "기존 통념"과 "conceptual advance"를 한 슬라이드에 같이 넣었는데,
    # 실제 논문으로 테스트해보니 텍스트가 길면 캔버스 밖으로 잘리는 문제가 있어
    # 두 슬라이드로 분리했다. fit_and_draw()가 폰트 크기를 자동으로 줄여주지만,
    # 안전 마진을 위해 슬라이드도 나눴다.)
    slot1_hook = slide_hook(a["suggested_hook_line"])
    slot3_prior = slide_prior_consensus(a["prior_consensus"])
    slot4_advance = slide_conceptual_advance(a["why_conceptual_not_incremental"])
    slot5_limits = slide_limitations_source(a["limitations"], args.authors_short, args.journal, a["_doi"])

    slot2_img = None
    screenshot_gap = False

    if args.reuse_mode.startswith("original_screenshot"):
        if args.screenshot_path and os.path.exists(args.screenshot_path):
            slot2_img = Image.open(args.screenshot_path).convert("RGB")
        else:
            screenshot_gap = True
            note_path = os.path.join(args.out_dir, "MISSING_SLIDE_02_SCREENSHOT.txt")
            with open(note_path, "w", encoding="utf-8") as f:
                f.write(
                    "--screenshot-path가 제공되지 않았습니다.\n"
                    "이 폴더에 slide_02_paper_screenshot.png 파일을 직접 추가하세요 "
                    "(원본 논문 제목페이지 또는 핵심 figure). 번호(01~05)는 이미 고정되어 "
                    "있으니 파일만 채우면 순서가 자동으로 맞습니다.\n"
                    "CC-BY 논문이라면 scripts/fetch_oa_screenshot.py로 자동 생성할 수 있습니다.\n"
                    f"라이선스 상태: {args.reuse_mode}"
                )
    else:
        slot2_img = slide_custom_graphic(a["what_this_paper_shows"], args.journal)

    named_slides = [
        ("01_hook", slot1_hook),
        ("02_paper_screenshot" if args.reuse_mode.startswith("original_screenshot") else "02_custom_graphic", slot2_img),
        ("03_prior_consensus", slot3_prior),
        ("04_conceptual_advance", slot4_advance),
        ("05_limitations_source", slot5_limits),
    ]

    for name, slide in named_slides:
        out_path = os.path.join(args.out_dir, f"slide_{name}.png")
        if slide is None:
            continue  # screenshot_gap인 경우 — 사람이 채워야 할 자리, 안내 파일만 남겨둔다
        slide.save(out_path)
        print(f"저장: {out_path}")

    if screenshot_gap:
        print(
            "\n[확인 필요] 원본 스크린샷이 아직 없습니다 — MISSING_SLIDE_02_SCREENSHOT.txt 참고. "
            "이 상태로는 게시하지 마세요."
        )


if __name__ == "__main__":
    main()
