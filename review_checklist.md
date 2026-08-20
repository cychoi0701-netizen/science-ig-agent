# 게시 전 사람 검수 체크리스트

에이전트가 생성한 초안을 게시 전 아래를 확인합니다. 5분이면 충분하고, 이게 계정 신뢰도와 저작권 리스크를 지켜주는 가장 중요한 단계입니다.

## 사실 검증
- [ ] `conceptual_advance` 분석이 논문 초록만이 아니라 본문(Introduction/Discussion) 근거로 작성되었다
- [ ] "기존 통념" 서술이 실제로 그 분야에서 통용되던 내용이 맞다 (지어낸 것이 아니다)
- [ ] 과장된 표현("완치", "혁명적", "모든 것을 바꿀") 없이 정확하게 서술했다
- [ ] 한계(limitations)가 최소 1개 포함되어 있다

## 저작권
- [ ] `01_COPYRIGHT_POLICY.md`의 reuse_mode를 확인했다
- [ ] original_screenshot인 경우: 실제로 논문 페이지 상단에 "Open Access"/"CC BY" 표기가 있는지 직접 눈으로 확인했다 (Unpaywall 판정은 100% 정확하지 않을 수 있음)
- [ ] custom_graphic인 경우: 원본 figure를 그대로 캡처하지 않고 재해석된 자체 그래픽을 사용했다
- [ ] 저자명/저널명/DOI가 캡션에 명시되어 있다

## 콘텐츠 품질
- [ ] 후킹 문장이 낚시성이 아니면서도 궁금증을 유발한다
- [ ] 슬라이드 텍스트에 오탈자가 없다
- [ ] 이미지가 1080x1080 정사각형이고 텍스트가 잘리지 않았다
- [ ] `prior_consensus`/`why_conceptual_not_incremental` 필드를 직접 수정했다면, "it was thought that"/"this shows that" 같은 프레이밍 어구 없이 담백한 서술문으로 남겨뒀다 (render_caption.py가 캡션에서 이 프레이밍을 자동으로 붙이므로, 필드 자체에 넣으면 "Scientists used to think it was thought that..."처럼 중복됨)

## 최종
- [ ] 이 논문을 발행 대상으로 고른 이유를 한 문장으로 설명할 수 있다 (설명이 안 되면 게시하지 않는다)
