# Handoff Guide

## 목적

David Strategy Works는 회사별 프로필, 업로드 문서, 지원사업 공고·양식, 추가 의견을 기반으로 정부지원사업 사업계획서 초안을 생성하고 HWPX/HTML/JSON으로 내보내는 로컬 웹앱입니다.

## 빠른 실행

```powershell
python server.py --port 8765
```

브라우저에서 `http://127.0.0.1:8765/`로 접속합니다.

새 PC 설치와 데이터 이전 절차는 `docs/INSTALL.md`를 기준으로 안내하세요.

## 현재 AI 배정

- Google `gemini-3.5-flash`: 한국어 사업계획서 1차 초안
- Google `gemini-3.1-flash-lite`: 업로드 문서 요약·사실 추출
- Google `gemini-3.1-pro-preview`: 긴 자료 기반 고급 초안 후보
- OpenAI `gpt-5.5`: 제출용 문장 정제, 구조화 출력, 형식 검증
- Anthropic `claude-opus-4.8`: 최종 심사위원 관점 리스크 리뷰
- Google `gemini-3-pro-image`: 이미지·인포그래픽 브리프

API 키가 없으면 로컬 규칙 기반 생성기로 동작합니다.

## 주요 파일

- `server.py`: API, 문서 추출, 양식 분석, 초안 생성, 버전 저장, HWPX/HTML export
- `static/index.html`: 화면 구조
- `static/app.js`: 프론트엔드 상태, 이벤트, 렌더링
- `static/styles.css`: 다크 컨설팅 UI, Pretendard Variable 스타일
- `static/fonts/PretendardVariable.woff2`: 번들 폰트
- `data/`: 로컬 프로필, 원본 양식, 버전, 선정 기준 데이터
- `exports/`: 생성된 HWPX/HTML/JSON 결과물

## 이어받는 사람이 먼저 볼 것

1. `README.md`
2. `docs/ARCHITECTURE.md`
3. `docs/ROADMAP.md`
4. `server.py`의 `generate_plan`, `validate_plan_format`, `create_export`
5. `static/app.js`의 `analyzeTemplate`, `generateDraft`, `saveDraftVersion`, `exportPlan`

## 이번 구현에서 완료된 것

- GitHub 업로드용 `.gitignore`, `.env.example`, 인수인계 문서 추가
- 원본 제출양식 파일을 `data/templates/`에 저장하고 export 시 원본·생성 HWPX·답변 매핑 JSON을 ZIP으로 묶음
- 이미지/스캔 문서 OCR 준비 상태 표시
- 초안 버전 저장·복원 API와 UI 추가
- 지원사업 유형별 선정 기준 데이터셋과 프론트 표시 추가
- UI 문구를 정상 한국어로 정리하고 전문 컨설팅 다크 테마 유지

## 주의사항

- 실제 사업자등록번호, 등기부등본, 재무자료, 고객정보는 민감정보입니다. GitHub public repo에 `data/`, `exports/`, `.env`를 올리지 마세요.
- 현재 원본 HWPX 보존은 "원본 파일 첨부 + 답변 매핑 JSON + 생성 HWPX" 방식입니다. 실제 정부 양식의 표/셀 내부에 직접 삽입하려면 HWPX XML 구조별 매핑 구현이 필요합니다.
- OCR은 Tesseract가 설치되어 있고 `TESSERACT_CMD`, `OCR_LANG`이 설정된 환경에서 동작합니다. 없으면 OCR 필요 상태를 표시합니다.

## Comment Revision Workflow

- Frontend entry points: `static/app.js`의 `reviseDraftFromComments`, `updateCurrentVersion`, `exportDraftVersion`.
- Backend entry points: `server.py`의 `/api/versions/revise`, `/api/versions/update`, `/api/versions/{profileId}/{versionId}/export`.
- Generated drafts are auto-saved, comment revisions create new versions, and each version can be opened, edited, updated, and exported independently.
- Document extraction hardening lives in `extract_text`, `text_from_pdf`, `ocr_pdf_bytes`, and `document_remediation_actions`.
- Submission quality reports are attached by `build_template_fill_manifest`, `build_judge_review_pack`, `build_visual_placement_plan`, `build_security_report`, and `attach_grounding_audit`.
- Operational documents: `docs/SECURITY.md` and `docs/TEST_PLAN.md`.
