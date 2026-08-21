#!/usr/bin/env python3
"""
draft_conceptual_advance.py

templates/conceptual_advance_framework.md의 4개 질문에 따라
Claude API로 "초안"을 생성한다. 이건 최종 결과물이 아니라 사람이
검수/수정할 초안이다 — 이 스크립트가 만든 텍스트를 검수 없이 그대로
게시하지 말 것 (00_SETUP_GUIDE.md / templates/review_checklist.md 참고).

왜 사람이 검수해야 하는가:
  - LLM은 논문의 실제 novelty를 초록만 보고 과장하거나 오해할 수 있다.
  - "기존 통념"을 실제 선행연구 근거 없이 지어낼 위험이 있다.
  - 팔로워가 많은 전문가 계정일수록 사실 오류의 비용이 크다.

사용법:
  python scripts/draft_conceptual_advance.py --doi 10.1016/j.cmet.2026.07.012 \
      --title "..." --abstract "..." --full-text-excerpt "..."

--full-text-excerpt 에는 가능하면 Introduction 도입부 + Discussion 첫 문단을
붙여넣는 것을 권장한다 (초록만으로는 "기존 통념"을 정확히 판단하기 어렵다).
"""

import argparse
import json
import os
import sys

FRAMEWORK_PROMPT = """\
You are a science communicator analyzing this paper's conceptual advance from \
the perspective of a Cell/Nature/Science-caliber editor. Answer the 4 framework \
questions below strictly based on the paper text provided. If the given text does \
not support a claim, write "needs verification in full text" instead of guessing. \
Do not exaggerate or oversell the finding.

[FRAMEWORK]
1. What was the prior consensus in the field?
2. What specifically did this study overturn or extend relative to that consensus?
3. Why is this a genuine conceptual advance rather than a routine replication/extension? \
   (state which type applies: (a) shows an existing causal claim was wrong or incomplete / \
   (b) separates two phenomena previously assumed to go together / \
   (c) discovers a new mechanism, population, or phenomenon / \
   (d) connects concepts across previously separate fields)
4. What are the limitations and open questions?

[PAPER INFO]
Title: {title}
DOI: {doi}
Abstract: {abstract}
Full-text excerpt (if provided): {full_text_excerpt}

[OUTPUT FORMAT — respond with ONLY the JSON below, all values in English]
Write "prior_consensus" and "why_conceptual_not_incremental" as bare factual
clauses WITHOUT framing phrases like "it was thought that" or "this shows
that" — those framing words are added separately by the caption template, so
including them again would create a duplicated phrase like "Scientists used
to think it was thought that...". For example, for "prior_consensus" write
"BAT activation occurs mainly through the beta3-adrenergic receptor." not
"It was believed that BAT activation occurs mainly through the beta3-adrenergic
receptor."
{{
  "prior_consensus": "... (bare clause, no 'it was thought that')",
  "what_this_paper_shows": "...",
  "why_conceptual_not_incremental": "... (bare clause, no 'this study shows that')",
  "advance_type": "a|b|c|d",
  "limitations": "...",
  "confidence_note": "note any parts that are uncertain because only the abstract was available",
  "suggested_hook_line": "hook line for Instagram slide 1, in English, no hype/clickbait, under 16 words"
}}
"""


def call_claude(prompt: str, model: str | None = None) -> dict:
    # 모델 ID는 시간이 지나며 바뀌므로 하드코딩하지 않는다.
    # 환경변수로 지정하거나, 없으면 최신 모델 목록을 확인:
    # https://docs.claude.com/en/docs/about-claude/models
    model = model or os.environ.get("ANTHROPIC_MODEL")
    if not model:
        print(
            "모델 ID가 지정되지 않았습니다. 환경변수 ANTHROPIC_MODEL을 설정하세요 "
            "(예: export ANTHROPIC_MODEL=claude-sonnet-4-5-20250929). "
            "최신 모델 ID는 https://docs.claude.com/en/docs/about-claude/models 에서 확인하세요.",
            file=sys.stderr,
        )
        sys.exit(1)
    try:
        import anthropic
    except ImportError:
        print(
            "anthropic 패키지가 없습니다. `pip install anthropic` 후 다시 실행하세요.",
            file=sys.stderr,
        )
        sys.exit(1)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("환경변수 ANTHROPIC_API_KEY가 설정되어 있지 않습니다.", file=sys.stderr)
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = resp.content[0].text
    # 모델이 코드블록으로 감싸는 경우 대비
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)


def main():
    parser = argparse.ArgumentParser(description="Conceptual advance 초안 생성 (사람 검수 필수)")
    parser.add_argument("--doi", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--abstract", required=True)
    parser.add_argument("--full-text-excerpt", default="(제공되지 않음 — 초록만으로 분석, 신뢰도 낮음)")
    parser.add_argument("--out", default=None, help="저장할 JSON 경로 (미지정시 stdout)")
    args = parser.parse_args()

    prompt = FRAMEWORK_PROMPT.format(
        title=args.title,
        doi=args.doi,
        abstract=args.abstract,
        full_text_excerpt=args.full_text_excerpt,
    )
    result = call_claude(prompt)
    result["_doi"] = args.doi
    result["_title"] = args.title
    result["_requires_human_review"] = True
    result["_review_checklist"] = "templates/review_checklist.md 확인 후 게시"

    if not args.full_text_excerpt or args.full_text_excerpt.startswith("(제공되지"):
        print(
            "[경고] full-text-excerpt 없이 초록만으로 분석했습니다. "
            "'기존 통념' 판단은 특히 신뢰도가 낮으니 원문 Introduction/Discussion을 "
            "직접 확인하세요.",
            file=sys.stderr,
        )

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"저장 완료: {args.out}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
