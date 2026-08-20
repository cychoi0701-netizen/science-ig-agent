#!/usr/bin/env python3
"""
fetch_papers.py

Cell / Nature / Science 에서 최근 게재된 논문 후보를 수집하고,
각 논문의 오픈액세스(OA)/라이선스 상태를 판정해서 재사용 가능 방식을 라벨링한다.

데이터 소스:
  - Crossref REST API (무료, 키 불필요) — 논문 메타데이터 검색
  - Unpaywall API (무료, 본인 이메일만 필요) — OA 여부 및 라이선스(CC-BY 등) 판정

주의:
  이 스크립트는 "논문 후보 리스트 + 라이선스 상태"까지만 만든다.
  실제로 어떤 논문을 다룰지, conceptual advance가 무엇인지는
  이 리스트를 사람이(또는 draft_conceptual_advance.py로 초안을 뽑아
  사람이 검수해서) 판단해야 한다. 여기서 자동으로 "중요도 점수"를
  임의로 매겨서 순위를 매기지 않는다 — 논문의 학술적 중요성은
  피상적인 지표(altmetric, 초록 길이 등)로 대체할 수 없기 때문이다.
  대신 이 스크립트는 후보 "롱리스트"만 제공하고, 최종 선택은
  05_SELECTION_CHECKLIST.md의 기준에 따라 사람이 한다.
"""

import argparse
import datetime as dt
import json
import sys
import time
import urllib.parse
import urllib.request

CROSSREF_BASE = "https://api.crossref.org/works"
UNPAYWALL_BASE = "https://api.unpaywall.org/v2"

# 저널명 텍스트 검색(query.container-title)은 Crossref에서 relevance 기반 fuzzy
# 매칭이라 "Cell"로 검색하면 "Cell Reports", "Cell Metabolism", "Tissue and Cell"
# 처럼 이름에 "cell"이 들어가는 전혀 다른 저널까지 섞여 나온다는 것을
# 실제 API 응답으로 확인했다 (rows=20 기준 정확히 "Cell"인 결과가 0건이었음).
# 대신 각 저널의 ISSN으로 필터링하면 100% 정확히 그 저널만 걸러진다.
# 아래 ISSN은 ISSN 포털(portal.issn.org)에서 확인한 값이다.
JOURNAL_ISSNS = {
    "cell": "0092-8674",       # Cell (Cell Press/Elsevier)
    "nature": "0028-0836",     # Nature (print ISSN; Crossref는 print/online 중 하나만 있어도 매칭됨)
    "science": "0036-8075",    # Science (AAAS, print ISSN)
}
JOURNAL_DISPLAY_NAMES = {"cell": "Cell", "nature": "Nature", "science": "Science"}


def http_get_json(url: str, headers: dict | None = None, timeout: int = 20) -> dict:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_recent_from_journal(journal_key: str, days_back: int, rows: int, mailto: str,
                               min_references: int = 20) -> list[dict]:
    """Crossref에서 특정 저널(ISSN 기준, 자매지 제외)의 최근 논문 목록을 가져온다.

    중요: Crossref의 type:journal-article 필터는 실제 원저 연구 논문뿐 아니라
    뉴스, 사설(Editorial), 북리뷰, "In Science Journals" 같은 주간 요약
    코너까지도 journal-article로 잘못 분류해 함께 반환한다. 실제로 Science
    저널을 대상으로 확인해보니 "In Science Journals"(참고문헌 0개), "Magic or
    realism?"(0개), "Writing the hard way"(0개) 같은 비연구 콘텐츠가 섞여
    나왔고, 반면 진짜 원저 연구 논문은 참고문헌이 50~150개 수준이었다.
    그래서 참고문헌 수(reference-count)가 min_references 미만인 항목은
    원저 연구 논문이 아닐 가능성이 높다고 보고 걸러낸다. 이건 "품질"이
    아니라 "이게 애초에 분석할 만한 연구 논문인가"를 가르는 구조적 필터다.
    """
    issn = JOURNAL_ISSNS[journal_key]
    since = (dt.date.today() - dt.timedelta(days=days_back)).isoformat()

    params = {
        "filter": f"issn:{issn},from-pub-date:{since},type:journal-article",
        "sort": "published",
        "order": "desc",
        "rows": str(rows),
        "mailto": mailto,  # Crossref "polite pool" — 더 안정적인 응답을 받기 위함
    }
    url = f"{CROSSREF_BASE}?{urllib.parse.urlencode(params)}"
    data = http_get_json(url, headers={"User-Agent": f"ig-science-agent/1.0 (mailto:{mailto})"})

    items = data.get("message", {}).get("items", [])
    results = []
    for item in items:
        titles = item.get("title", [])
        if not titles:
            continue

        # ISSN 필터가 이미 정확히 이 저널만 걸러주지만, 만에 하나 Crossref 메타데이터가
        # 불완전한 경우를 대비해 container-title도 한 번 더 확인한다 (이중 안전장치).
        actual_container = ((item.get("container-title") or [None])[0] or "").strip()
        expected = JOURNAL_DISPLAY_NAMES[journal_key]
        if actual_container and actual_container != expected:
            continue

        reference_count = item.get("reference-count", 0) or 0
        if reference_count < min_references:
            continue  # 뉴스/사설/북리뷰 등 비연구 콘텐츠로 판단, 제외

        results.append(
            {
                "doi": item.get("DOI"),
                "title": titles[0],
                "container_title": (item.get("container-title") or [None])[0],
                "authors": [
                    f"{a.get('given', '')} {a.get('family', '')}".strip()
                    for a in item.get("author", [])
                ],
                "published": "-".join(
                    str(x) for x in item.get("published", {}).get("date-parts", [[None]])[0] if x
                ),
                "abstract_raw": item.get("abstract"),  # JATS XML 태그 포함, 있을 때만
                "reference_count": reference_count,
                "url": item.get("URL"),
                "crossref_license": item.get("license", []),
                "searched_journal": journal_key,
            }
        )
    return results


def classify_reuse(doi: str, mailto: str) -> dict:
    """Unpaywall로 OA 여부/라이선스를 확인하고 재사용 가능 방식을 라벨링한다."""
    if not doi:
        return {"is_oa": None, "license": None, "reuse_mode": "unknown", "reason": "DOI 없음"}

    url = f"{UNPAYWALL_BASE}/{urllib.parse.quote(doi)}?email={urllib.parse.quote(mailto)}"
    try:
        data = http_get_json(url)
    except Exception as e:  # noqa: BLE001
        return {"is_oa": None, "license": None, "reuse_mode": "unknown", "reason": f"조회 실패: {e}"}

    is_oa = data.get("is_oa")
    best_oa = data.get("best_oa_location") or {}
    license_ = best_oa.get("license")
    pdf_url = best_oa.get("url_for_pdf") or best_oa.get("url")

    if is_oa and license_ == "cc-by":
        reuse_mode = "original_screenshot"
        reason = "CC-BY 오픈액세스 — 원본 figure/제목페이지 스크린샷 재사용 가능 (출처 표기 필수)"
    elif is_oa and license_ in ("cc-by-nc", "cc-by-nc-nd", "cc-by-nd", "cc0"):
        reuse_mode = "original_screenshot_restricted"
        reason = f"오픈액세스이나 라이선스가 {license_} — 비상업적 사용/무변형 조건 확인 필요"
    elif is_oa:
        reuse_mode = "original_screenshot_check"
        reason = "오픈액세스로 표시되나 라이선스 유형 불명 — 개별 확인 필요"
    else:
        reuse_mode = "custom_graphic"
        reason = "구독형(비오픈) 논문 — 원본 figure 스크린샷 금지, 자체 제작 그래픽으로 재해석 권장"
        pdf_url = None  # 비-OA는 PDF를 자동으로 받지 않는다 (합법적 접근 경로가 없음)

    return {
        "is_oa": is_oa,
        "license": license_,
        "reuse_mode": reuse_mode,
        "reason": reason,
        "pdf_url": pdf_url,  # fetch_oa_screenshot.py 입력값 — original_screenshot 계열일 때만 채워짐
    }


def main():
    parser = argparse.ArgumentParser(description="Cell/Nature/Science 최근 논문 후보 수집")
    parser.add_argument("--journals", nargs="+", default=["cell", "nature", "science"],
                         choices=list(JOURNAL_ISSNS.keys()))
    parser.add_argument("--days-back", type=int, default=30,
                         help="며칠 전까지의 논문을 볼지. 실제 API로 확인해보니 Cell(Elsevier)의 "
                              "Crossref 등록 발행일은 '2026-08'처럼 월 단위까지만 있고 일(day)이 "
                              "없는 경우가 있다 (Crossref는 이를 그 달 1일로 취급하는 것으로 보임). "
                              "days-back을 짧게 주면 이번 달 1일 이후로 발행일이 찍힌 최신 Cell "
                              "논문이 통째로 안 잡히는 문제가 실제로 재현되어, 기본값을 30일로 "
                              "넉넉히 잡았다 (중복은 posted_dois.json으로 별도 방지되므로 안전함).")
    parser.add_argument("--rows-per-journal", type=int, default=30,
                         help="하루 3편씩 뽑으려면 후보가 넉넉해야 하므로 저널당 기본 30편을 가져온다")
    parser.add_argument("--mailto", required=True, help="Crossref/Unpaywall polite pool용 본인 이메일")
    parser.add_argument("--min-references", type=int, default=20,
                         help="이보다 참고문헌이 적으면 뉴스/사설 등 비연구 콘텐츠로 보고 제외")
    parser.add_argument("--out", default="output/paper_candidates.json")
    args = parser.parse_args()

    all_candidates = []
    for journal in args.journals:
        print(f"[fetch] {journal} 저널에서 최근 {args.days_back}일 논문 조회 중...", file=sys.stderr)
        try:
            candidates = fetch_recent_from_journal(
                journal, args.days_back, args.rows_per_journal, args.mailto,
                min_references=args.min_references,
            )
        except Exception as e:  # noqa: BLE001
            print(f"[warn] {journal} 조회 실패: {e}", file=sys.stderr)
            continue
        for c in candidates:
            print(f"  - classify: {c['title'][:60]}...", file=sys.stderr)
            c["reuse"] = classify_reuse(c["doi"], args.mailto)
            time.sleep(0.2)  # Unpaywall API에 과도한 부하를 주지 않기 위한 최소한의 딜레이
        all_candidates.extend(candidates)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(all_candidates, f, ensure_ascii=False, indent=2)

    print(f"\n총 {len(all_candidates)}건의 논문 후보를 {args.out}에 저장했습니다.", file=sys.stderr)
    oa_count = sum(1 for c in all_candidates if c["reuse"]["reuse_mode"] == "original_screenshot")
    print(f"이 중 원본 스크린샷 재사용 가능(CC-BY): {oa_count}건", file=sys.stderr)


if __name__ == "__main__":
    main()
