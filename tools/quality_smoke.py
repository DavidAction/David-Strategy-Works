from __future__ import annotations

import base64
import io
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import server  # noqa: E402


def b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def install_temp_runtime(tmp: Path) -> None:
    server.DATA_DIR = tmp / "data"
    server.EXPORT_DIR = tmp / "exports"
    server.TEMPLATE_DIR = server.DATA_DIR / "templates"
    server.VERSION_DIR = server.DATA_DIR / "versions"
    server.DATASET_DIR = server.DATA_DIR / "datasets"
    server.COMPANY_FILE = server.DATA_DIR / "company.json"
    server.PROFILES_FILE = server.DATA_DIR / "profiles.json"
    server.GRANT_DATASET_FILE = server.DATASET_DIR / "grant_success_criteria.json"
    server.AI_USAGE_FILE = server.DATA_DIR / "ai_usage.jsonl"


def run() -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="dsw-quality-") as tmp_dir:
        install_temp_runtime(Path(tmp_dir))

        business_plan = (
            "브리웰은 조직 번아웃을 조기 발견하는 B2B 웰니스 SaaS입니다. "
            "고객 인터뷰 28건, 파트너 후보 3곳, 6개월 내 유료 PoC 5건을 목표로 합니다. "
            "핵심 기능은 모바일 체크인, AI 위험군 분류, 전문가 코칭 연결, HR 리포트 자동화입니다. "
            "지원금은 개인정보보호 체계, AI 리스크 분석 고도화, 시범 고객 운영에 사용합니다. "
        ) * 10

        insights = server.analyze_documents(
            [
                {"name": "existing_business_plan.txt", "content": b64(business_plan)},
                {"name": "business_registration.txt", "content": b64("사업자등록번호 123-45-67890 대표자 David 업태 서비스업")},
            ],
            "LOI와 예산 직접성을 강조",
        )

        template = server.analyze_template(
            "grant-template.txt",
            """
창업성장 지원사업 사업계획서
1. 문제 인식과 해결 필요성을 작성하시오. 1200자 이내
2. 제품/서비스 구현 계획을 작성하시오. 1400자 이내
3. 시장진입 및 사업화 전략을 작성하시오. 1400자 이내
필수 포함: 문제, 솔루션, 시장, 팀, 예산
""",
            [],
        )

        company = {
            "basic": {"companyName": "브리웰", "representative": "David"},
            "business": {
                "oneLine": "조직 번아웃을 조기 발견하고 관리하는 HR 웰니스 플랫폼",
                "targetCustomer": "50명 이상 성장 기업 HR 리더",
                "problem": "정신건강 리스크가 늦게 발견되어 생산성과 이탈률에 영향을 줌",
                "solution": "모바일 체크인, AI 위험군 분류, 전문가 코칭, HR 리포트 자동화",
                "product": "B2B 웰니스 SaaS",
                "stage": "초기 PoC",
            },
            "team": {"summary": "HR SaaS 기획, 임상심리 자문, 데이터 분석 경험"},
            "traction": {"summary": "고객 인터뷰 28건, 파트너 후보 3곳"},
        }

        plan = server.generate_plan(
            company,
            template,
            {
                "documentInsights": insights,
                "grantName": "창업성장 지원사업",
                "length": "balanced",
                "profileId": "quality-smoke",
                "templateGuidance": {
                    "targetPages": "5",
                    "strictFormat": True,
                    "focusPoints": "예산 직접성과 PoC 전환율",
                },
                "useAI": False,
            },
        )

        revised = server.revise_plan_with_comments(
            plan,
            "예산 집행 논리와 심사위원 반박 가능성을 앞쪽에 더 명확히 배치",
            "QA revised",
        )
        exported = server.create_export(revised)
        hwpx_file = next(item for item in exported["files"] if item["filename"].endswith(".hwpx"))
        hwpx_path = server.EXPORT_DIR / hwpx_file["filename"]
        with zipfile.ZipFile(io.BytesIO(hwpx_path.read_bytes())) as archive:
            entries = set(archive.namelist())

        unsafe_plan = json.loads(json.dumps(revised, ensure_ascii=False))
        unsafe_plan["evidenceLockReport"] = {"status": "needs_evidence"}
        unsafe_plan["unsupportedClaimAudit"] = {"highRiskClaims": 1}
        previous_block = os.environ.get("DSW_BLOCK_UNSAFE_EXPORT")
        os.environ["DSW_BLOCK_UNSAFE_EXPORT"] = "true"
        try:
            blocked_export = server.create_export(unsafe_plan)
        finally:
            if previous_block is None:
                os.environ.pop("DSW_BLOCK_UNSAFE_EXPORT", None)
            else:
                os.environ["DSW_BLOCK_UNSAFE_EXPORT"] = previous_block

        checks = {
            "documents": len(insights.get("documents", [])),
            "restrictedDocuments": insights.get("securityReport", {}).get("restrictedDocumentCount"),
            "businessUnderstandingAreas": len((insights.get("businessUnderstanding") or {}).get("knowledge", {})),
            "templateQuestions": len(template.get("questions", [])),
            "sections": len(plan.get("sections", [])),
            "templateRows": len((plan.get("templateFillManifest") or {}).get("rows", [])),
            "submissionFidelityStatus": (plan.get("submissionFidelityReport") or {}).get("status"),
            "judgeQuestions": len((plan.get("judgeReviewPack") or {}).get("judgeQuestions", [])),
            "visualPlacements": len((plan.get("visualPlacementPlan") or {}).get("placements", [])),
            "evidenceLockStatus": (revised.get("evidenceLockReport") or {}).get("status"),
            "consultantReadiness": (revised.get("consultantReview") or {}).get("readinessScore", 0),
            "costLedgerRows": len((revised.get("aiCostLedger") or {}).get("rows", [])),
            "secureTransferPolicy": (revised.get("secureTransferPolicy") or {}).get("status"),
            "revisionChangedSections": (revised.get("revisionDiff") or {}).get("changedSectionCount", 0),
            "exportFiles": len(exported.get("files", [])),
            "svgFiles": len([item for item in exported.get("files", []) if item.get("filename", "").endswith(".svg")]),
            "hwpxMediaSvgFiles": len([item for item in entries if item.startswith("Contents/Media/") and item.endswith(".svg")]),
            "hwpxEntriesOk": {
                "mimetype",
                "version.xml",
                "Contents/content.hpf",
                "Contents/header.xml",
                "Contents/section0.xml",
                "META-INF/container.xml",
            }.issubset(entries),
            "unsafeExportBlocked": bool(blocked_export.get("blocked")),
        }

        assert checks["documents"] == 2, checks
        assert checks["restrictedDocuments"] >= 1, checks
        assert checks["businessUnderstandingAreas"] >= 5, checks
        assert checks["templateQuestions"] >= 3, checks
        assert checks["sections"] >= 3, checks
        assert checks["templateRows"] >= 3, checks
        assert checks["submissionFidelityStatus"] in {"ok", "needs_review", "needs_work"}, checks
        assert checks["judgeQuestions"] >= 5, checks
        assert checks["visualPlacements"] >= 1, checks
        assert checks["evidenceLockStatus"] in {"locked", "needs_evidence"}, checks
        assert checks["consultantReadiness"] >= 0, checks
        assert checks["costLedgerRows"] >= 3, checks
        assert checks["secureTransferPolicy"] in {"ok", "confirmation_required"}, checks
        assert checks["revisionChangedSections"] >= 1, checks
        assert checks["exportFiles"] >= 3, checks
        assert checks["svgFiles"] >= 1, checks
        assert checks["hwpxMediaSvgFiles"] >= 1, checks
        assert checks["hwpxEntriesOk"], checks
        assert checks["unsafeExportBlocked"], checks
        return checks


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
