#!/usr/bin/env python3
"""
run_daily.py — 전체 파이프라인 오케스트레이터

흐름:
  1. fetch_papers.py 로직으로 최근 논문 후보 수집 (Cell/Nature/Science)
  2. 후보 중 하나를 선정 (사람이 고르는 것을 기본값으로 함 — 아래 참고)
  3. draft_conceptual_advance.py 로직으로 초안 생성
  4. [필수 정지점] 사람 검수 — templates/review_checklist.md
  5. build_carousel.py 로직으로 이미지 생성
  6. 이미지를 호스팅에 업로드해 URL 확보 (사용자 구현 필요)
  7. post_to_instagram.py 로직으로 게시

중요한 설계 결정 — "완전 자동"으로 만들지 않은 이유:
  이 파이프라인은 3단계(후보 중 최종 선정)와 4단계(검수)에서 사람이
  개입하도록 일부러 멈추게 설계했다. 논문의 학술적 중요성 판단과
  conceptual advance 해석은 알고리즘으로 완전히 대체할 수 없는 영역이고,
  틀린 해석을 자동으로 대량 게시하면 계정 신뢰도에 치명적이기 때문이다.
  "완전 무인 자동화"를 원한다면 --auto-select와 --skip-review 플래그로
  가능하게 열어두긴 했지만, 기본값은 항상 사람 개입이다.

사용법 (한 번에 논문 1편 기준. 하루 3편을 만들려면 draft/build를 --doi와
--out-dir을 바꿔가며 3번 반복하면 되는데, 매일 자동으로 이걸 해주는 쪽은
.github/workflows/daily_post.yml 입니다 — 이 스크립트는 로컬에서 손으로
한 편씩 시험해볼 때 쓰는 용도입니다):
  python run_daily.py --stage fetch          # 후보 리스트 생성 후 정지
  python run_daily.py --stage draft --doi ... # 후보 중 하나 골라 초안 생성
  # -> 초안을 사람이 output/analysis_reviewed.json 으로 검수/저장
  python run_daily.py --stage build --analysis output/analysis_reviewed.json --reuse-mode ...
  # -> 이미지를 호스팅에 업로드, URL을 이미지 순서대로 확보
  python run_daily.py --stage publish --image-urls ... --caption-file ...
"""

import argparse
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}", file=sys.stderr)
    subprocess.run(cmd, check=True, cwd=ROOT)


def stage_fetch(args):
    mailto = os.environ.get("CROSSREF_MAILTO")
    if not mailto:
        print("환경변수 CROSSREF_MAILTO가 필요합니다 (config/.env 확인).", file=sys.stderr)
        sys.exit(1)
    run([
        sys.executable, "scripts/fetch_papers.py",
        "--journals", *args.journals,
        "--days-back", str(args.days_back),
        "--mailto", mailto,
        "--out", "output/paper_candidates.json",
    ])
    with open(os.path.join(ROOT, "output/paper_candidates.json"), encoding="utf-8") as f:
        candidates = json.load(f)
    print(f"\n{len(candidates)}건의 후보가 output/paper_candidates.json에 저장되었습니다.")
    print("이 중 오늘 다룰 논문들을 05_SELECTION_CHECKLIST.md 기준으로 직접 고르거나, "
          "scripts/auto_select.py --count 3 으로 자동 선정하세요.")


def stage_draft(args):
    with open(os.path.join(ROOT, "output/paper_candidates.json"), encoding="utf-8") as f:
        candidates = json.load(f)
    match = next((c for c in candidates if c["doi"] == args.doi), None)
    if not match:
        print(f"DOI {args.doi}를 후보 목록에서 찾지 못했습니다. --stage fetch를 먼저 실행하세요.", file=sys.stderr)
        sys.exit(1)

    cmd = [
        sys.executable, "scripts/draft_conceptual_advance.py",
        "--doi", match["doi"],
        "--title", match["title"],
        "--abstract", match.get("abstract_raw") or "(초록 없음 — 원문에서 직접 발췌 필요)",
        "--out", "output/analysis_draft.json",
    ]
    run(cmd)
    print(
        "\n초안이 output/analysis_draft.json에 저장되었습니다.\n"
        "templates/review_checklist.md로 검수한 뒤, 필요시 수정하여 "
        "output/analysis_reviewed.json으로 저장하세요 (그대로 써도 되면 복사만 하면 됩니다)."
    )


def stage_build(args):
    out_dir = args.out_dir
    screenshot_path = None
    if args.reuse_mode == "original_screenshot" and args.pdf_url and not args.no_auto_screenshot:
        screenshot_path = f"{out_dir}/_oa_screenshot.png"
        os.makedirs(os.path.join(ROOT, out_dir), exist_ok=True)
        try:
            run([
                sys.executable, "scripts/fetch_oa_screenshot.py",
                "--pdf-url", args.pdf_url,
                "--page", "0",
                "--out", screenshot_path,
            ])
        except subprocess.CalledProcessError:
            print(
                "[경고] OA PDF 자동 스크린샷 생성에 실패했습니다. 수동으로 채워야 합니다.",
                file=sys.stderr,
            )
            screenshot_path = None

    cmd = [
        sys.executable, "scripts/build_carousel.py",
        "--analysis", args.analysis,
        "--journal", args.journal,
        "--authors-short", args.authors_short,
        "--reuse-mode", args.reuse_mode,
        "--out-dir", out_dir,
    ]
    if screenshot_path:
        cmd += ["--screenshot-path", screenshot_path]
    run(cmd)
    print(
        "\n이미지가 output/carousel에 생성되었습니다.\n"
        "MISSING_SLIDE_02_SCREENSHOT.txt 파일이 있다면 그 안내대로 수동으로 채워야 합니다.\n"
        "다음: 이 이미지들을 본인 이미지 호스팅에 업로드하고 공개 URL을 확보한 뒤 "
        "--stage publish로 진행하세요 (Graph API는 로컬 파일이 아니라 URL을 요구합니다)."
    )


def stage_publish(args):
    cmd = [
        sys.executable, "scripts/post_to_instagram.py",
        "--image-urls", *args.image_urls,
        "--caption-file", args.caption_file,
    ]
    if args.dry_run:
        cmd.append("--dry-run")
    run(cmd)


def main():
    parser = argparse.ArgumentParser(description="인스타그램 과학 콘텐츠 파이프라인 오케스트레이터")
    sub = parser.add_subparsers(dest="stage", required=True)

    p_fetch = sub.add_parser("fetch")
    p_fetch.add_argument("--journals", nargs="+", default=["cell", "nature", "science"])
    p_fetch.add_argument("--days-back", type=int, default=30)

    p_draft = sub.add_parser("draft")
    p_draft.add_argument("--doi", required=True)

    p_build = sub.add_parser("build")
    p_build.add_argument("--analysis", default="output/analysis_reviewed.json")
    p_build.add_argument("--journal", required=True)
    p_build.add_argument("--authors-short", required=True)
    p_build.add_argument("--reuse-mode", required=True)
    p_build.add_argument("--pdf-url", default=None,
                          help="output/paper_candidates.json의 reuse.pdf_url 값 (CC-BY일 때 자동 스크린샷용)")
    p_build.add_argument("--no-auto-screenshot", action="store_true",
                          help="CC-BY라도 자동 스크린샷 생성을 건너뛰고 수동으로 채운다")
    p_build.add_argument("--out-dir", default="output/carousel",
                          help="하루 여러 편을 만들 때는 논문마다 다른 폴더를 지정하세요 "
                               "(예: output/carousel_1, output/carousel_2)")

    p_publish = sub.add_parser("publish")
    p_publish.add_argument("--image-urls", nargs="+", required=True)
    p_publish.add_argument("--caption-file", required=True)
    p_publish.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    os.makedirs(os.path.join(ROOT, "output"), exist_ok=True)

    {
        "fetch": stage_fetch,
        "draft": stage_draft,
        "build": stage_build,
        "publish": stage_publish,
    }[args.stage](args)


if __name__ == "__main__":
    main()
