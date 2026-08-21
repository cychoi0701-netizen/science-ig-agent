#!/usr/bin/env python3
"""
render_caption.py

templates/caption_template.md의 구조를 코드로 구현해 검수된 conceptual
advance 분석(JSON)으로부터 실제 게시용 캡션 텍스트를 생성한다.
"""

import argparse
import json
import os
import re


def to_hashtag(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", s)


TEMPLATE = """{hook_line} \U0001f9ec

Scientists used to think {prior_consensus}

But this new {journal} paper shows {advance}

\U0001f4cc Limitation: {limitations}

Source: {authors_short}, {journal} ({year})
DOI: {doi}

This account breaks down one Cell/Nature/Science-level paper every day.
Follow for more \U0001f446

#science #research #{journal_tag} #biology #discovery #peerreviewed
"""


def main():
    parser = argparse.ArgumentParser(description="검수된 분석 JSON으로부터 캡션 텍스트 생성")
    parser.add_argument("--analysis", required=True)
    parser.add_argument("--journal", required=True)
    parser.add_argument("--authors-short", required=True)
    parser.add_argument("--year", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    with open(args.analysis, encoding="utf-8") as f:
        a = json.load(f)

    def lowercase_first(s: str) -> str:
        s = s.strip()
        return (s[0].lower() + s[1:]) if s else s

    caption = TEMPLATE.format(
        hook_line=a["suggested_hook_line"].rstrip("."),
        prior_consensus=lowercase_first(a["prior_consensus"]),
        advance=lowercase_first(a["why_conceptual_not_incremental"]),
        limitations=a["limitations"],
        authors_short=args.authors_short,
        journal=args.journal,
        year=args.year,
        doi=a["_doi"],
        journal_tag=to_hashtag(args.journal),
    )

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(caption)

    print(f"저장 완료: {args.out}")
    print("\n--- 미리보기 ---\n")
    print(caption)


if __name__ == "__main__":
    main()
