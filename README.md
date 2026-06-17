# David Strategy Works

회사 프로필, 업로드 문서, 지원사업 공고·양식, 추가 의견을 기반으로 정부지원사업 사업계획서 초안을 생성하고 HWPX/HTML/JSON으로 내보내는 로컬 웹앱입니다.

## 실행

```powershell
python server.py --port 8765
```

브라우저에서 `http://127.0.0.1:8765/`로 접속합니다.

Windows에서는 더 쉽게 실행할 수 있습니다.

```powershell
.\start-dsw.ps1
```

또는 `start-dsw.bat`을 더블클릭하세요.

다른 노트북/데스크탑 설치 방법은 [docs/INSTALL.md](docs/INSTALL.md)를 보세요.

## 주요 흐름

1. 회사별 프로필을 생성하거나 기존 프로필을 선택합니다.
2. 회사 기본정보, 법적 정보, 사업모델, 시장, 팀, 재무 정보를 입력하고 저장합니다.
3. 기존 사업계획서, 사업자등록증, 등기부등본, 재무자료, 인증자료를 업로드합니다.
4. 추가 의견·업데이트에 최근 성과와 이번 지원사업에서 강조할 메시지를 입력합니다.
5. 지원사업 공고문 또는 제출 양식을 업로드하거나 붙여넣어 문항과 평가 포인트를 분석합니다.
6. 제출 설계 브리프에 목표 페이지 수, 전체 구성, 주안점, 형식 규칙, 작성 코멘트를 입력합니다.
7. 전략 초안을 생성하고 문항별 내용을 편집합니다.
8. 초안 버전을 저장해 수정본을 관리합니다.
9. HWPX, 검토용 HTML, JSON, 원본 양식 보존 패키지를 생성합니다.

## 구현 범위

- 회사별 프로필 저장: `data/profiles.json`
- 원본 제출양식 저장: `data/templates/`
- 초안 버전 저장·복원: `data/versions/`
- 지원사업 선정 기준 데이터셋: `data/datasets/grant_success_criteria.json`
- 문서 분석: `.hwpx`, `.docx`, `.pdf`, `.txt`, `.md`, `.json`, 이미지 파일 일부
- 다문서 근거자료 최적화: 문서별 중요도 점수, 추출 품질, 중복 감지, 증빙 스니펫, 평가 항목 커버리지 자동 산출
- 기존 사업계획서 심층 이해: 업로드한 사업계획서 원문 텍스트를 보존하고 문제·고객·솔루션·시장·차별성·검증·수익모델·예산·팀·일정 단위로 재구성해 새 제출 양식의 문항별 근거로 반영
- 원문 근거 추적성: 생성된 각 문항이 어떤 업로드 문서 스니펫과 연결되는지 점수화하고, 원문에 없는 숫자·성과·과장 표현을 제출 전 점검
- OCR 준비 상태 표시: 이미지/스캔 PDF에서 Tesseract 사용 가능 여부와 OCR 필요 여부 표시
- 양식 분석: 문항, 요구사항, 키워드, 선정 기준, 원본 양식 메타데이터 추출
- 제출 형식 검증: 문항 수, 순서, 제목, 본문 누락, 페이지 분량, 구성 브리프, 형식 규칙 확인
- 시각자료 설계: 표, 인포그래픽, 이미지 생성 브리프를 초안과 검토 화면에 배치
- 심사/운영 리포트: HWPX 양식 기입 매핑, 심사위원 예상 질문, 탈락 리스크, 보안 점검, 워크스페이스 관리 리포트 표시
- 고도화 리포트: 제출 양식 충실도, 근거 잠금, 컨설턴트 최종 리뷰, AI 비용 추정, 민감문서 전송 정책 표시
- 내보내기 고도화: 표·인포그래픽 SVG, 시각자료 매니페스트, HWPX 내부 SVG 첨부, HWPX 충실도 리포트, 원본 HWPX placeholder 직접 치환 검토본 생성
- 제출 안전장치: `DSW_BLOCK_UNSAFE_EXPORT=true`이면 근거 부족·고위험 주장·민감문서 AI 전송 확인 누락 시 export 차단
- AI 운영 점검: `/api/ai/health`에서 모델 배정과 API 키 준비 상태 확인, `/api/ai/usage`에서 실제 호출 토큰·비용 로그 확인
- 내보내기: `.hwpx`, 검토용 `.html`, 초안 `.json`, 원본 양식·답변 매핑 패키지
- 글꼴: `static/fonts/PretendardVariable.woff2`를 번들링하고 웹앱·HTML·HWPX에서 Pretendard Variable 우선 사용

## AI 모델 배정

API 키가 있으면 단계별로 멀티 모델을 사용하도록 설계되어 있습니다. API 키가 없거나 호출에 실패하면 로컬 규칙 기반 생성기로 자동 전환합니다.

- 한글 초안 작성: Google `gemini-3.5-flash`
- 문서 분석: Google `gemini-3.1-flash-lite`
- 긴 자료 기반 고급 초안 후보: Google `gemini-3.1-pro-preview`
- 제출 문장 정제·형식 검증: OpenAI `gpt-5.5`
- 최종 심사위원 관점 리뷰: Anthropic `claude-opus-4-8` (Claude Opus 4.8)
- 이미지 생성 브리프: Google `gemini-3-pro-image`, fallback OpenAI `gpt-image-2`

환경 변수는 `.env.example`을 참고하세요.

## 운영 검증 명령

```powershell
python tools\quality_smoke.py
python tools\benchmark_proposals.py
python tools\ai_live_check.py --no-live
python tools\ocr_check.py
python tools\hwpx_template_probe.py
python tools\export_retention.py
```

`python tools\benchmark_proposals.py`는 기본적으로 외부 AI를 호출하지 않는 결정론 벤치마크입니다. 실제 Gemini/GPT/Claude 호출까지 포함하려면 `python tools\benchmark_proposals.py --live-ai`로 실행합니다.

실제 API 키를 `.env`에 넣은 뒤에는 `python tools\ai_live_check.py`로 Gemini/GPT/Claude 연결을 확인합니다. 정부 HWPX 양식 파일을 받은 경우 `python tools\hwpx_template_probe.py path\to\template.hwpx`로 표·셀·placeholder 구조를 먼저 진단하세요.

API 키는 채팅이나 GitHub에 올리지 말고 로컬에서 다음 스크립트로 입력합니다.

```powershell
.\tools\set_api_keys_local.ps1
python tools\ai_live_check.py
```

스캔 PDF/이미지 OCR을 쓰려면 관리자 권한 PowerShell에서 다음을 실행한 뒤 `python tools\ocr_check.py --require-ocr`로 확인합니다.

```powershell
.\tools\install_ocr_windows.ps1
```

실제 정부지원사업 HWPX 샘플을 받은 경우에는 다음 명령으로 private runtime library에 누적합니다. `data/`는 GitHub에 올라가지 않습니다.

```powershell
python tools\import_hwpx_samples.py C:\path\to\template.hwpx
```

## GitHub 업로드 주의

`data/`, `exports/`, `.env`, 로그 파일은 `.gitignore`에 포함되어 있습니다. 실제 사업자등록증, 등기부등본, 재무자료, 회사 기밀 문서는 public repository에 올리지 마세요.

다른 PC로 기존 작업을 옮기려면 GitHub clone 후 기존 PC의 `data/`, `exports/`, `.env`를 새 PC의 프로젝트 폴더로 복사하세요.

보안 운영 지침은 [docs/SECURITY.md](docs/SECURITY.md), 실전 검증 체크리스트는 [docs/TEST_PLAN.md](docs/TEST_PLAN.md), 제품 고도화 감사는 [docs/QUALITY_UPGRADE_AUDIT.md](docs/QUALITY_UPGRADE_AUDIT.md)를 참고하세요.

표준 회귀검증은 다음 명령으로 실행합니다.

```powershell
python tools\quality_smoke.py
```

## 다음 제품화 과제

- 실제 지원사업별 HWPX 양식 샘플을 누적해 placeholder 없는 표/셀 자동 매칭 정확도 개선
- 사용자별 로그인, 암호화 저장소, 팀 권한 분리
- 실제 합격/탈락 사업계획서 데이터셋 기반 평가 루브릭 보강
- 한컴 버전별 HWPX 본문 이미지 객체 삽입 호환성 검증

## Comment Revision Workflow

- 생성된 사업계획서는 자동으로 초안 버전에 저장됩니다.
- 전략 초안 워룸의 코멘트 기반 재작성 영역에서 코멘트를 입력하면 새 사업계획서 버전이 생성됩니다.
- 버전 라이브러리에서 각 버전을 열어 편집하고, 선택 버전을 업데이트할 수 있습니다.
- 각 버전은 별도로 HWPX/HTML/JSON export를 생성해 다운로드할 수 있습니다.
