# Science Instagram Auto-Poster

Cell / Nature / Science **본지**(자매지 제외 — Nature Communications, Cell Reports 등은 다루지 않습니다)에서 매일 3편을 골라 "conceptual advance"(왜 이 논문이 톱 저널에 실릴 수 있었는가)를 해설하는 캐러셀을 만드는 파이프라인입니다. Instagram Graph API로 완전 자동 게시하는 것도 가능하지만(`scripts/post_to_instagram.py`), 기본 설정은 초안까지만 자동 생성하고 실제 업로드는 사람이 직접 합니다.

## 폴더 구조

```
00_SETUP_GUIDE.md          계정/API 설정 방법 (최초 1회)
01_COPYRIGHT_POLICY.md     저작권/오픈액세스 판단 규칙 (필독)
05_SELECTION_CHECKLIST.md  논문 선정 기준
templates/
  conceptual_advance_framework.md   "왜 중요한가" 분석 틀
  caption_template.md               캡션 구조 설명
  review_checklist.md               게시 전 최종 검수
scripts/
  fetch_papers.py           Crossref(ISSN 필터, 본지만)+Unpaywall로 논문 후보 수집 및 OA 라이선스 판정
  auto_select.py             후보 중 오늘 다룰 논문 N편(기본 3편, 저널별 round-robin)을 규칙 기반으로 자동 선정
  draft_conceptual_advance.py  Claude API로 conceptual advance 초안 생성
  fetch_oa_screenshot.py     CC-BY 논문의 공개 PDF에서 페이지를 이미지로 렌더링
  build_carousel.py          1080x1080 캐러셀 이미지 5장 생성 (텍스트 길이에 따라 폰트 자동 축소)
  render_caption.py          캡션 텍스트 생성
  post_to_instagram.py       Instagram Graph API로 실제 게시
  test_connection.py / refresh_token.py / get_long_lived_token.sh   계정 연결/토큰 관리
run_daily.py                 위 스크립트들을 단계별로 묶은 오케스트레이터 (로컬 실행용)
.github/workflows/daily_post.yml   매일 자동 실행되는 GitHub Actions 워크플로
```

## 왜 이렇게 만들었는가 (설계 원칙)

1. **계정 안전이 최우선**: 브라우저 자동클릭이 아니라 Instagram 공식 API만 사용합니다. `00_SETUP_GUIDE.md` 참고.
2. **저작권 리스크 관리**: 논문마다 오픈액세스(CC-BY) 여부를 자동 판정해서, 원본 스크린샷을 써도 되는지 자체 제작 그래픽으로 바꿔야 하는지 결정합니다. CC-BY 논문은 공개 PDF를 직접 렌더링해 완전 자동화까지 가능합니다. `01_COPYRIGHT_POLICY.md` 참고.
3. **"왜 중요한가"는 고정된 분석틀로**: 논문의 conceptual advance를 아무 기준 없이 뽑지 않고, 4단계 프레임워크(기존 통념 → 뒤집은 지점 → 왜 재현이 아닌 새로운 개념인가 → 한계)로 구조화했습니다. `templates/conceptual_advance_framework.md` 참고.
4. **논문 선정도 재현 가능한 규칙으로**: "화제성" 같은 자의적 점수를 매기지 않고, CC-BY 우선/중복 방지/저널 편중 방지라는 명시적 규칙만 씁니다. `scripts/auto_select.py` 참고.
5. **게시는 사람이 직접 한다**: 현재 설정은 매일 초안(이미지+캡션)을 자동 생성해 GitHub Issue로 올려두기만 하고, 실제 Instagram 업로드는 본인이 직접 합니다. 그래서 Instagram Graph API 토큰이나 Meta 앱 심사 절차가 전혀 필요 없습니다 — `00_SETUP_GUIDE.md`는 건너뛰어도 됩니다. 나중에 완전 자동 게시로 바꾸고 싶어지면 `scripts/post_to_instagram.py`가 이미 준비되어 있으니 그때 `00_SETUP_GUIDE.md`대로 API 설정만 추가하면 됩니다.

## 빠른 시작

### A. 이 세션(클라우드 샌드박스)에서는 실행할 수 없는 이유

이 파이프라인은 외부 API(Crossref, Unpaywall, Instagram Graph API 등)와 통신해야 하는데, 지금 이 대화가 실행되고 있는 클라우드 환경은 보안상 패키지 레지스트리(pip, npm)만 접근 가능하고 일반 인터넷 접근이 막혀있습니다. 그래서 아래 두 가지 중 하나의 환경에서 실행해야 합니다.

### B. 추천: GitHub Actions로 매일 자동 실행 (초안 생성까지 자동, 게시는 직접)

1. 이 폴더 전체를 새 GitHub 리포지토리로 push
2. 리포지토리 Settings → Pages → Source를 "Deploy from a branch", 브랜치는 `main`, 폴더는 `/docs`로 설정 (이미지 공개 호스팅용)
3. Settings → Secrets and variables → Actions에서 아래 Secret 등록 (Instagram 관련 값은 필요 없습니다):
   - `ANTHROPIC_API_KEY` (conceptual advance 분석용)
   - `CROSSREF_MAILTO` (본인 이메일)
4. Actions 탭에서 `Daily science content draft` 워크플로를 한 번 수동 실행(workflow_dispatch)해서 정상 동작 확인 — 수동 실행 시 편수(`post_count`)를 원하는 만큼 바꿔서 테스트할 수 있습니다
5. 매일 정해진 시각에 GitHub Issue가 **편수만큼(기본 3개)** 올라옵니다 (`Draft IG post 1/3`, `2/3`, `3/3`처럼 번호가 붙습니다). `templates/review_checklist.md`로 각각 확인 후, 이미지를 다운로드해서 Instagram에 직접 캐러셀로 올리고 캡션을 붙여넣으면 됩니다.

### C. 로컬/개인 서버에서 수동으로 단계별 실행

```bash
pip install -r requirements.txt
cp config/.env.example config/.env   # 값 채워넣기
python scripts/test_connection.py    # 연결 확인

python run_daily.py fetch                        # 논문 후보 수집 (Cell/Nature/Science 본지만)
python scripts/auto_select.py --count 3           # (선택) 3편 자동 선정, 또는 05_SELECTION_CHECKLIST.md로 직접 고르기
python run_daily.py draft --doi <선택한 DOI 중 하나>   # conceptual advance 초안
# -> output/analysis_draft.json을 검수하고 output/analysis_reviewed.json으로 저장
python run_daily.py build --analysis output/analysis_reviewed.json \
    --journal "Cell" --authors-short "Doe J, et al." \
    --reuse-mode original_screenshot --pdf-url "<Unpaywall PDF URL>" \
    --out-dir output/carousel_1
# -> output/carousel_1 이미지가 완성되면 직접 Instagram 앱에서 캐러셀로 업로드하고
#    output/caption.txt 내용을 캡션으로 붙여넣으면 됩니다.
# 나머지 2편도 --doi와 --out-dir(carousel_2, carousel_3)만 바꿔 반복합니다.
```

(나중에 게시까지 자동화하고 싶어지면 `00_SETUP_GUIDE.md`대로 API를 설정한 뒤 `python run_daily.py publish --image-urls <url1> <url2> ... --caption-file output/caption.txt`를 추가로 실행하면 됩니다.)

## 알려진 한계 (정직하게 밝혀둡니다)

- `fetch_oa_screenshot.py`는 CC-BY 논문의 첫 페이지만 렌더링합니다. 논문에 따라 첫 페이지에 원하는 figure가 없을 수 있어 `--page` 값을 조정해야 할 수 있습니다.
- 비-오픈액세스(구독형) 논문은 `custom_graphic` 모드로 자동 전환되지만, 실제 그래픽 내용(`what_this_paper_shows`)은 LLM 초안 그대로입니다 — Issue를 열어보지 않고 그대로 게시하면 이 부분의 오류를 아무도 걸러내지 못합니다. 게시는 사람이 직접 하는 구조이니 반드시 한 번은 읽고 올려주세요.
- 하루 3편을 요구했는데 최근 며칠간 Cell/Nature/Science 본지 게재량이 적으면 3편을 못 채울 수 있습니다 (`auto_select.py`가 이 경우 경고를 출력합니다). 이땐 `fetch_papers.py`의 `--days-back` 값을 늘리세요.
- (나중에 완전 자동 게시로 전환할 경우) Meta Graph API 버전/요율 제한은 시간이 지나며 바뀝니다. 스크립트에 방어 로직(요율 조회, 재시도 대기)은 넣었지만, 주기적으로 `00_SETUP_GUIDE.md`와 공식 changelog를 확인하는 것을 권장합니다.
- 100k 팔로워는 콘텐츠 자동화만으로 달성되지 않습니다. 초기에는 결과물 품질을 직접 확인하고, 어떤 유형의 포스트(주제, 후킹 문장 스타일)가 저장/공유가 잘 되는지 계정 인사이트를 보며 `templates/conceptual_advance_framework.md`와 캡션 스타일을 계속 다듬는 것이 중요합니다.
