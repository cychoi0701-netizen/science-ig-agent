# 저작권 및 콘텐츠 소싱 규칙 (계정 보호를 위해 반드시 준수)

Cell(Elsevier), Nature(Springer Nature), Science(AAAS) 논문을 다룰 때 가장 큰 리스크는 팔로워 정지가 아니라 **저작권 침해로 인한 게시물 삭제/계정 신고/법적 경고**입니다. 벤치마킹하신 "scientists.ideas.sciences" 계정처럼 논문 원본 페이지를 그대로 스크린샷해서 올리는 방식은, 그 논문이 오픈액세스(CC-BY)가 아닌 이상 엄밀히는 저작권자(대개 출판사)의 허락 없는 재배포에 해당합니다. 지금까지 별 문제가 없었던 건 출판사들이 개별 소규모 계정을 적극적으로 단속하지 않기 때문이지, 합법이라서가 아닙니다. 팔로워가 늘고 계정이 커질수록(특히 브랜드 협업/광고가 붙으면) 이 리스크는 커집니다.

## 리서치 결과 요약

| 출판사 | 오픈액세스(CC-BY) 논문 | 구독형(비-오픈액세스) 논문 |
|---|---|---|
| **Elsevier (Cell)** | CC-BY 조건 하에 출처 표기하면 재사용 가능 | 재사용에 RightsLink/CCC를 통한 허가 필요 |
| **Springer Nature** | CC-BY는 출처 표기 조건으로 상업적 이용 포함 자유 재사용 가능. CC BY-NC-ND는 비상업적 공유만 가능, 변형·가공 불가 | 재사용/재배포에 허가 필요, 일부 공유는 "제한적"으로만 허용 |
| **Science (AAAS)** | Science Advances 등 일부 저널은 완전 오픈액세스(CC-BY). Science 본지는 대부분 구독형 | RightsLink를 통한 허가 필요 |

([Elsevier Permissions](https://www.elsevier.com/about/policies-and-standards/copyright/permissions), [Springer Nature Licensing](https://www.springernature.com/gp/open-science/policies/journal-policies/licensing-and-copyright), [Science Reprints and Permissions](https://www.science.org/content/page/reprints-and-permissions))

## 실행 규칙

1. **논문을 고를 때 라이선스를 먼저 확인한다.** 논문 페이지 상단/하단에 "Open Access", "CC BY", "This is an open access article" 등의 문구가 있는지 확인합니다 (이번에 보여주신 Cell Metabolism의 Fenoterol 논문은 정확히 "Open Access... CC BY 4.0 license"라고 명시되어 있어 재사용에 적합한 좋은 예시입니다).
2. **CC-BY 논문**: 원본 figure/제목페이지 스크린샷을 그대로 사용 가능. 단, 캡션에 저자명, 저널명, DOI, "CC BY 4.0" 라이선스를 반드시 명시 (출처 표기는 CC-BY의 필수 조건입니다).
3. **CC BY-NC-ND 논문**: 원본 이미지 재게시는 가능하나 자르거나 재가공하면 안 되고, 상업적 목적(협찬/광고 포함 게시물) 사용은 피합니다.
4. **구독형(비오픈) 논문**: 원본 figure를 스크린샷째로 올리지 않습니다. 대신
   - 논문의 핵심 결과를 요약한 **자체 제작 인포그래픽/도식**으로 재해석해서 올린다 (사실관계는 논문 기반이되, 시각 자료는 직접 제작 — 이게 저작권 이슈를 피하면서도 계정의 독자적 스타일을 만드는 방법입니다)
   - 캡션에서 논문 링크(DOI)로 트래픽을 보내고, "자세한 그림은 원문에서 확인하세요"로 유도
   - 제목 페이지(논문 첫 페이지, 저자/제목/저널 로고)는 통상 "사실 정보의 스크린샷"으로 보아 관행적으로 관대하게 다뤄지는 편이지만, 이것도 100% 안전하지는 않으므로 저널 로고를 활용한 자체 제작 카드로 대체하는 것을 권장합니다.
5. **매번 출처를 명시한다.** 저자명 전체 나열보다는 "1저자 외, 저널명, 연도, DOI 링크"가 실용적입니다. 이는 CC-BY 조건 충족뿐 아니라, 저자/연구자들에게 존중을 보여줘 협업 제안으로 이어질 수 있습니다.
6. **애매하면 보수적으로 판단한다.** 이 규칙은 법률 자문이 아니라 일반적 가이드라인입니다. 특정 논문/이미지 재사용이 불확실하면 출판사의 permissions 창구(RightsLink 등)에 문의하거나, 아예 자체 제작 그래픽으로 대체하는 쪽을 권장합니다.

`scripts/fetch_papers.py`는 각 논문의 오픈액세스 여부를 API로 함께 조회해서, "원본 스크린샷 가능" / "자체 제작 그래픽 필요"를 자동으로 라벨링합니다.
