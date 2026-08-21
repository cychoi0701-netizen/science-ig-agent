#!/usr/bin/env python3
"""
auto_select.py

무인 스케줄 실행(GitHub Actions 등)에서 사람이 즉시 개입할 수 없을 때 쓰는
"결정론적 안전장치" 선택 규칙이다. 05_SELECTION_CHECKLIST.md에 있는 사람의
정성적 판단(다양성, 흥미도 등)을 대체하지 않는다 — 그럴 수 없다. 대신
아래의 명시적이고 재현 가능한 규칙만 적용한다:

  1. Research Article 타입만 (리뷰/코멘터리 제외 — Crossref 메타데이터의
     'type' 필드가 아니라 fetch_papers.py 단계에서 이미 journal-article로
     필터링되어 있음)
  2. Cell/Nature/Science 본지만 (자매지 제외 — fetch_papers.py에서 ISSN
     기준으로 이미 걸러져 있음)
  3. 아직 게시하지 않은(=이전에 초안으로 뽑히지 않은) DOI (posted_dois.json 기준)
  4. reuse_mode가 'original_screenshot'(CC-BY, 저작권 리스크 없음)인 후보 우선
  5. 하루 --count편(기본 3편)을 뽑을 때는 가능하면 Cell/Nature/Science에서
     한 편씩 고르게(round-robin) 뽑는다 — 하루 3편을 전부 같은 저널에서만
     뽑으면 다양성이 떨어지기 때문. 특정 저널에 그날 후보가 없으면 다른
     저널에서 채운다.

이 규칙에 없는 것: "화제성", "중요도" 같은 주관적 가중치는 절대 넣지
않는다 — 그런 지표를 자동화하려면 대리 지표(altmetric, 초록 감성 점수 등)를
써야 하는데, 이는 실제 학술적 중요성과 상관관계가 약하고 자칫 선정적인
논문만 고르게 될 위험이 있다. 이 규칙으로 고른 결과도 draft 단계 이후
사람이 templates/review_checklist.md로 최종 확인하는 것을 권장한다.
"""

import argparse
import json
import os


def load_json(path, default):
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return default


def select_n(candidates: list[dict], posted: set, count: int) -> list[dict]:
    eligible = [c for c in candidates if c["doi"] and c["doi"] not in posted]

    # 저널별로 묶고, 저널 내부에서는 CC-BY(reuse_mode=original_screenshot) 우선.
    by_journal: dict[str, list[dict]] = {}
    for c in eligible:
        by_journal.setdefault(c["searched_journal"], []).append(c)
    for journal_list in by_journal.values():
        journal_list.sort(key=lambda c: c["reuse"]["reuse_mode"] != "original_screenshot")

    # round-robin: cell -> nature -> science -> cell -> ... 순서로 한 편씩 뽑는다.
    journal_order = ["cell", "nature", "science"]
    queues = {j: list(by_journal.get(j, [])) for j in journal_order}

    selected = []
    seen_dois = set()
    while len(selected) < count and any(queues[j] for j in journal_order):
        for j in journal_order:
            if len(selected) >= count:
                break
            while queues[j]:
                candidate = queues[j].pop(0)
                if candidate["doi"] in seen_dois:
                    continue
                selected.append(candidate)
                seen_dois.add(candidate["doi"])
                break

    return selected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", default="output/paper_candidates.json")
    parser.add_argument("--posted-log", default="output/posted_dois.json")
    parser.add_argument("--count", type=int, default=3, help="하루에 고를 논문 편수")
    parser.add_argument("--out", default="output/selected.json")
    args = parser.parse_args()

    candidates = load_json(args.candidates, [])
    posted = set(load_json(args.posted_log, []))

    selected = select_n(candidates, posted, args.count)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)

    if not selected:
        print("선정 가능한 후보가 없습니다 (모두 이미 사용됨 또는 후보 없음).")
        return

    print(f"{len(selected)}편 선정 (요청: {args.count}편):")
    for s in selected:
        print(f"  - [{s['searched_journal']}] {s['title'][:70]} ({s['doi']}) reuse={s['reuse']['reuse_mode']}")

    if len(selected) < args.count:
        print(
            f"\n[알림] 요청한 {args.count}편보다 적은 {len(selected)}편만 선정되었습니다. "
            "최근 며칠간 후보가 이미 소진되었을 수 있습니다 — fetch_papers.py의 "
            "--days-back 값을 늘리는 것을 고려하세요."
        )
    print(
        "\n[알림] 이 선택은 재현 가능한 규칙 기반이며, 논문의 실제 중요성/화제성은 "
        "반영하지 않습니다. 가능하면 게시 전 05_SELECTION_CHECKLIST.md로 사람이 "
        "한번 더 확인하세요."
    )


if __name__ == "__main__":
    main()
