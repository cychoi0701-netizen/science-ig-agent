# 인스타그램 과학 계정 자동화 — 계정 설정 가이드

> **본인이 직접 게시하기로 하셨다면 이 문서 전체를 건너뛰어도 됩니다.**
> 지금 파이프라인은 매일 "콘텐츠 초안(캐러셀 이미지+캡션)"만 GitHub Issue로
> 만들어두고, 실제 Instagram 업로드는 사람이 직접 합니다. 이 방식이면
> Instagram Graph API 토큰, Meta 앱 생성, Facebook 페이지 연결 등 아래
> 내용이 전혀 필요 없습니다. `README.md`의 "빠른 시작"만 따라가면 됩니다.
>
> 이 문서는 나중에 "완전 자동 게시"로 전환하고 싶어질 때를 위해 남겨둡니다
> (`scripts/post_to_instagram.py`는 이미 만들어져 있어서, 그때 이 문서대로
> 설정만 하면 바로 쓸 수 있습니다).

---

이 문서는 Instagram Graph API로 게시물을 자동 업로드하기 위해 **한 번만** 해두면 되는 설정을 순서대로 안내합니다. 소요 시간은 약 20~30분입니다.

## 왜 이 설정이 필요한가

Instagram은 공식 API를 통해서만 자동 게시를 허용합니다. 브라우저 자동화로 로그인 후 직접 클릭해서 올리는 방식은 서비스 약관 위반이며 계정 정지(shadowban 또는 영구 정지) 위험이 있습니다. 아래 절차는 Meta(구 Facebook)가 공식적으로 제공하는 방법이라 계정에 안전합니다.

2024년 이후 Meta는 두 가지 API 경로를 제공합니다.

| 구분 | Instagram API with Instagram Login (신규, 추천) | Instagram Graph API with Facebook Login (기존) |
|---|---|---|
| Facebook 페이지 연결 | 불필요 | 필수 |
| 광고/파트너십 태깅 기능 | 없음 | 있음 |
| 우리 용도(본인 계정 자동 게시) | 충분함 | 과함 |

우리는 광고나 브랜드 파트너십 태깅이 필요 없으므로 **Instagram API with Instagram Login**(Facebook 페이지 불필요)을 사용합니다. 다만 이 경로는 계정 유형에 따라 지원 여부가 다를 수 있어, 안 될 경우를 대비해 기존 방식(Facebook 페이지 연결)도 함께 안내합니다.

또한 본인 소유 계정에만 게시하는 경우("Development 모드")에는 Meta의 앱 심사(App Review)가 필요 없습니다. 앱 심사는 다른 사람의 계정을 연결해 서비스를 제공할 때만 필요합니다. 우리는 본인 계정만 쓰므로 이 부분에서 시간이 크게 절약됩니다.

---

## 1단계 — Instagram 계정을 프로페셔널 계정으로 전환

1. Instagram 앱 → 프로필 → 메뉴(≡) → 설정 및 개인정보 → 계정 유형 및 도구
2. "프로페셔널 계정으로 전환" 선택
3. 카테고리는 "과학자(Scientist)" 또는 "교육(Education)" 계열 중 선택
4. 크리에이터(Creator) 계정을 추천합니다 — 개인 브랜드 콘텐츠 계정에 더 적합한 인사이트/기능 제공

## 2단계 — Meta 개발자 계정 및 앱 생성

1. https://developers.facebook.com 접속 후 본인 Facebook 계정으로 로그인 (Facebook 계정이 없다면 하나 만들어야 합니다 — 개발자 인증용으로만 쓰고 페이지 연결은 불필요)
2. "My Apps" → "Create App" 클릭
3. 앱 유형: "Business" 선택
4. 앱 이름 입력 (예: "scidea-nexus-bot" 등 원하는 이름)
5. 생성된 앱 대시보드에서 "Add Product" → **Instagram** 제품 추가

## 3단계 — 권한(Permission) 및 계정 연결

1. 앱 대시보드 → Instagram → API setup with Instagram login
2. 본인 Instagram 계정으로 로그인하여 앱과 연결
3. 필요한 권한(scope) 선택:
   - `instagram_business_basic`
   - `instagram_business_content_publish`
4. Meta가 발급하는 **Access Token**을 받습니다. 이 토큰은 처음엔 단기(short-lived, 1시간)이므로 반드시 **장기 토큰(long-lived token, 약 60일)**으로 교환해야 합니다. (아래 4단계)

만약 "Instagram API with Instagram Login" 경로가 계정에서 지원되지 않는다면 대안으로:
- Facebook 페이지를 하나 생성 (비어있어도 무방)
- Instagram 프로페셔널 계정 설정에서 해당 페이지에 연결
- 앱에서 "Facebook Login for Business"로 페이지와 연결된 Instagram 계정의 토큰 발급

## 4단계 — 장기 액세스 토큰 발급

단기 토큰을 아래 형태의 요청으로 장기 토큰으로 교환합니다 (curl 예시는 `scripts/get_long_lived_token.sh` 참고).

```
GET https://graph.instagram.com/access_token
    ?grant_type=ig_exchange_token
    &client_secret={앱의 App Secret}
    &access_token={단기 토큰}
```

장기 토큰은 약 60일마다 만료되므로, 만료 전에 자동으로 갱신하는 로직을 파이프라인에 포함해두었습니다 (`scripts/refresh_token.py`).

## 5단계 — 필요한 값 정리

아래 값들을 `.env` 파일에 저장해두면 이후 스크립트가 자동으로 읽습니다. `config/.env.example` 파일을 복사해서 `config/.env`로 만들고 채워주세요.

- `IG_USER_ID` — Instagram 비즈니스 계정 ID (Graph API Explorer에서 `/me?fields=id` 로 확인 가능)
- `IG_ACCESS_TOKEN` — 3~4단계에서 발급받은 장기 액세스 토큰
- `IG_APP_ID`, `IG_APP_SECRET` — 토큰 자동 갱신용

## 6단계 — 연결 테스트

`scripts/test_connection.py`를 실행해 계정 정보가 정상적으로 조회되는지 확인합니다. 이게 성공하면 게시 자동화 준비가 끝난 것입니다.

---

## 주의사항 (계정 보호를 위해 반드시 읽어주세요)

- **하루 게시 횟수**: Meta 공식 문서 내에서도 계정당 24시간 한도가 문서 위치에 따라 50건/100건으로 다르게 표기되어 있어 고정된 숫자로 단정하지 않는 것이 안전합니다. 대신 게시 전에 `GET /{ig-user-id}/content_publishing_limit` 엔드포인트로 실시간 잔여 한도를 조회하도록 `scripts/post_to_instagram.py`에 넣어두었습니다. 우리는 하루 1건만 올리므로 어느 쪽이든 한도에 걸릴 일은 없습니다.
- **토큰은 절대 공개 저장소(GitHub 등)에 커밋하지 마세요.** `.env` 파일은 `.gitignore`에 포함되어 있습니다.
- 자동화라 해도 콘텐츠 품질(특히 conceptual advance 해석)은 사람이 최종 검수하는 것을 강력히 권장합니다 — 이 부분은 `templates/review_checklist.md`에 정리해두었습니다.
