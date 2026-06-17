from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import html
import io
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent
STATIC_DIR = ROOT / "static"
DATA_DIR = ROOT / "data"
EXPORT_DIR = ROOT / "exports"
TEMPLATE_DIR = DATA_DIR / "templates"
VERSION_DIR = DATA_DIR / "versions"
DATASET_DIR = DATA_DIR / "datasets"
COMPANY_FILE = DATA_DIR / "company.json"
PROFILES_FILE = DATA_DIR / "profiles.json"
GRANT_DATASET_FILE = DATASET_DIR / "grant_success_criteria.json"
LOG_FILE = ROOT / "server.log"


AI_MODEL_ASSIGNMENTS: dict[str, Any] = {
    "provider": "Multi-provider",
    "api": "OpenAI Responses API + Anthropic Claude API + Google Gemini API",
    "decisionDate": "2026-06-17",
    "decisionSummary": (
        "단일 모델 고정이 아니라 역할별 최적 배치가 가장 유리합니다. "
        "Gemini 3.5 Flash는 한글 보고서 1차 초안, GPT는 제출용 정제와 형식 검증, "
        "Claude는 고난도 심사 관점 리뷰에 배치합니다."
    ),
    "primaryDraft": {
        "provider": "Google",
        "api": "Gemini API",
        "model": "gemini-3.5-flash",
        "reasoningEffort": "medium",
        "score": 94,
        "role": "한글 사업계획서 1차 보고서 초안 작성, 자연스러운 문장 흐름, 반복 생성",
        "why": "한글 보고서 초안의 자연스러운 문장, 속도, 비용 대비 품질이 좋아 초안 생성 주력 모델로 둡니다.",
    },
    "documentAnalysis": {
        "provider": "Google",
        "api": "Gemini API",
        "model": "gemini-3.1-flash-lite",
        "reasoningEffort": "low",
        "score": 90,
        "role": "업로드 문서 대량 요약, 사실 추출, 회사 프로필 보강 후보 생성",
        "why": "저비용·고속 처리에 강해 기존 사업계획서, 등기부, 사업자등록증 같은 대량 입력 전처리에 배치합니다.",
    },
    "firstDraftAlternative": {
        "provider": "Google",
        "api": "Gemini API",
        "model": "gemini-3.1-pro-preview",
        "reasoningEffort": "high",
        "score": 92,
        "role": "긴 자료를 한 번에 읽는 고급 1차 초안, 멀티모달 양식 이해",
        "why": "긴 입력과 복합 양식 이해가 중요할 때 Gemini 3.5 Flash의 고급 대체 모델로 둡니다.",
    },
    "finalPolish": {
        "provider": "OpenAI",
        "api": "Responses API",
        "model": "gpt-5.5",
        "reasoningEffort": "high",
        "score": 95,
        "role": "Gemini 초안을 제출용 문장으로 정제, 구조화 JSON 출력, 섹션별 논리 연결 강화",
        "why": "제출 문서의 지시 준수, 구조화 출력, 문항별 누락 방지와 형식 검증 안정성이 좋아 최종 정제에 배치합니다.",
    },
    "formatReview": {
        "provider": "OpenAI",
        "api": "Responses API",
        "model": "gpt-5.5",
        "reasoningEffort": "high",
        "score": 95,
        "role": "문항 순서, 분량, 제출 규칙, JSON/HWPX 배치 무결성 최종 검증",
        "why": "작성과 검증을 같은 스키마로 묶기 쉽고, 제출 양식 검증을 자동화하기 좋습니다.",
    },
    "strategicRedTeam": {
        "provider": "Anthropic",
        "api": "Claude API",
        "model": "claude-opus-4.8",
        "reasoningEffort": "adaptive",
        "score": 95,
        "role": "최종 제출 전 심사위원 반박 관점, 리스크, 과장 표현, 논리 공백 감사",
        "why": "Fable 5는 실사용 접근성이 제한되므로 제외합니다. 최종 심사 리뷰는 사용자가 지정한 대로 Opus 4.8 단독으로 진행해 가장 강한 반박 관점과 논리 감사를 우선합니다.",
        "fallbackModel": "",
    },
    "longContextReview": {
        "provider": "Anthropic",
        "api": "Claude API",
        "model": "claude-opus-4.8",
        "reasoningEffort": "adaptive",
        "score": 94,
        "role": "긴 문서 묶음의 일관성 검토, 기존 사업계획서와 신규 양식 간 충돌 확인",
        "why": "최종 심사 리뷰와 동일하게 Opus 4.8을 사용해 장문 자료의 논리 충돌과 심사 리스크를 강하게 검토합니다.",
    },
    "visualPlanning": {
        "provider": "Google",
        "api": "Gemini API",
        "model": "gemini-3-pro-image",
        "imageModel": "gemini-3-pro-image",
        "fallbackImageModel": "gpt-image-2",
        "quality": "high",
        "score": 93,
        "role": "제품 콘셉트 이미지, 고객 여정 이미지, 한국어 라벨이 필요한 비주얼 생성",
        "why": "Gemini 이미지 계열은 문맥 이해와 텍스트 렌더링 강점을 우선 활용하고, OpenAI GPT Image 2를 대체 후보로 유지합니다.",
    },
    "structuredOutput": {
        "strictJsonSchema": True,
        "role": "본문, 표, 인포그래픽, 검증 결과를 JSON 스키마로 받아 HWPX/HTML 배치 안정성 확보",
    },
    "comparisonMatrix": [
        {
            "provider": "OpenAI",
            "model": "gpt-5.5",
            "bestFor": "제출용 정제, 구조화 출력, 형식 검증, 툴 연계",
            "tradeoff": "Gemini보다 단가가 높아 초안 반복 작성보다 최종 정제에 집중",
            "inputPerMTok": "$5.00",
            "outputPerMTok": "$30.00",
            "verdict": "제출용 정제와 형식 검증에 채택",
        },
        {
            "provider": "Anthropic",
            "model": "claude-opus-4.8",
            "bestFor": "가장 어려운 추론, 장기 문맥, 최종 반박 검토",
            "tradeoff": "비용이 높으므로 모든 문항 생성이 아니라 최종 감사에 제한. 최종 리뷰는 fallback 없이 Opus 4.8로 고정",
            "inputPerMTok": "$5.00",
            "outputPerMTok": "$25.00",
            "verdict": "최종 심사위원 관점 리뷰에 채택",
        },
        {
            "provider": "Google",
            "model": "gemini-3.5-flash",
            "bestFor": "한글 보고서 초안, 빠른 반복 생성, 비용 대비 문장 품질",
            "tradeoff": "최종 제출 형식과 누락 검증은 GPT/Claude 보조가 필요",
            "inputPerMTok": "$1.50",
            "outputPerMTok": "$9.00",
            "verdict": "한글 보고서 1차 초안 주력 모델로 채택",
        },
        {
            "provider": "Google",
            "model": "gemini-3.1-pro-preview",
            "bestFor": "비용 효율형 고급 초안, 멀티모달 양식 이해",
            "tradeoff": "Preview 모델이므로 최종 제출 문장은 GPT/Claude 검토를 거침",
            "inputPerMTok": "$2.00",
            "outputPerMTok": "$12.00",
            "verdict": "긴 자료 기반 고급 초안 후보로 채택",
        },
        {
            "provider": "Google",
            "model": "gemini-3.1-flash-lite",
            "bestFor": "대량 문서 추출, 저비용 요약, 반복 전처리",
            "tradeoff": "최종 문장 품질보다 속도·비용 최적화 목적",
            "inputPerMTok": "$0.25",
            "outputPerMTok": "$1.50",
            "verdict": "문서 분석 기본 모델로 채택",
        },
        {
            "provider": "Google",
            "model": "gemini-3-pro-image",
            "bestFor": "텍스트 라벨 포함 이미지, 제품 콘셉트, 고객 여정 비주얼",
            "tradeoff": "숫자 표와 제출용 데이터는 이미지가 아니라 앱 구조화 표로 생성",
            "inputPerMTok": "$2.00",
            "outputPerMTok": "$12.00 + image output",
            "verdict": "이미지 생성 기본 모델로 채택",
        },
    ],
    "fallback": {
        "mode": "local_rule_based",
        "role": "외부 API 키가 없거나 API 호출이 실패할 때도 제출 가능한 초안을 생성",
    },
}


DEFAULT_COMPANY: dict[str, Any] = {
    "basic": {
        "name": "",
        "ceo": "",
        "founded": "",
        "location": "",
        "industry": "",
        "website": "",
        "contact": "",
    },
    "legal": {
        "businessNumber": "",
        "corporateNumber": "",
        "businessType": "",
        "businessItem": "",
        "capital": "",
        "registryOffice": "",
        "registrationStatus": "",
    },
    "business": {
        "oneLine": "",
        "problem": "",
        "solution": "",
        "product": "",
        "targetCustomer": "",
        "stage": "",
        "differentiation": "",
        "revenueModel": "",
    },
    "market": {
        "marketSize": "",
        "trend": "",
        "competitors": "",
        "positioning": "",
        "goToMarket": "",
    },
    "traction": {
        "metrics": "",
        "customers": "",
        "partnerships": "",
        "ip": "",
        "certifications": "",
        "pilotResults": "",
    },
    "team": {
        "founder": "",
        "members": "",
        "advisors": "",
        "hiringPlan": "",
    },
    "finance": {
        "fundingNeed": "",
        "useOfFunds": "",
        "salesPlan": "",
        "costPlan": "",
        "milestones": "",
    },
    "impact": {
        "jobCreation": "",
        "socialValue": "",
        "regionalImpact": "",
        "sustainability": "",
    },
    "knowledge": {
        "additionalNotes": "",
    },
}


DEFAULT_SECTIONS = [
    ("사업 개요", "overview"),
    ("문제 인식 및 고객 니즈", "problem"),
    ("제품·서비스 내용", "solution"),
    ("시장성 및 경쟁 환경", "market"),
    ("차별성 및 경쟁우위", "differentiation"),
    ("사업화 전략 및 수익모델", "business_model"),
    ("추진 일정 및 성장 계획", "growth"),
    ("자금 사용 계획", "budget"),
    ("팀 역량", "team"),
    ("기대 효과", "impact"),
]


CATEGORY_RULES: list[tuple[str, list[str], str]] = [
    (
        "problem",
        ["문제", "애로", "니즈", "필요성", "배경", "pain", "고객 불편"],
        "문제의 크기, 고객의 절박함, 기존 대안의 한계를 수치와 사례로 보여주세요.",
    ),
    (
        "solution",
        ["제품", "서비스", "솔루션", "기술", "아이템", "기능", "개발내용"],
        "제공 가치, 핵심 기능, 구현 수준, 사용자가 얻는 변화를 선명하게 연결하세요.",
    ),
    (
        "market",
        ["시장", "고객", "수요", "트렌드", "규모", "세분", "타깃"],
        "목표 고객군, 시장 규모, 진입 순서, 구매 의사결정자를 구체화하세요.",
    ),
    (
        "differentiation",
        ["경쟁", "차별", "우위", "대체재", "독창", "강점"],
        "경쟁사 대비 우위가 기능, 데이터, 운영, 가격, 파트너십 중 어디서 나오는지 증명하세요.",
    ),
    (
        "business_model",
        ["수익", "매출", "가격", "비즈니스모델", "판매", "마케팅", "판로", "사업화"],
        "누가 왜 돈을 내는지, 첫 매출까지의 경로와 반복 가능한 판매 구조를 제시하세요.",
    ),
    (
        "growth",
        ["일정", "로드맵", "추진", "목표", "성과", "확장", "스케일"],
        "지원기간 내 산출물과 이후 12개월 성장 지표를 마일스톤으로 제시하세요.",
    ),
    (
        "budget",
        ["자금", "예산", "사업비", "활용", "소요", "집행", "지원금"],
        "지원금 사용 항목이 사업 목표 달성에 어떻게 직접 연결되는지 설명하세요.",
    ),
    (
        "team",
        ["팀", "대표", "인력", "역량", "경험", "조직", "전문성"],
        "대표와 팀이 이 문제를 풀 수밖에 없는 경험, 실행력, 보완 계획을 보여주세요.",
    ),
    (
        "impact",
        ["고용", "기대효과", "사회", "지역", "파급", "ESG", "공공"],
        "매출 외 효과를 일자리, 지역경제, 사회적 가치, 확산 가능성으로 정리하세요.",
    ),
    (
        "risk",
        ["위험", "리스크", "대응", "한계", "보완"],
        "기술, 시장, 운영 리스크를 인정하고 검증 계획과 대안을 제시하세요.",
    ),
]


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    VERSION_DIR.mkdir(parents=True, exist_ok=True)
    DATASET_DIR.mkdir(parents=True, exist_ok=True)


def safe_filename(name: str, fallback: str = "file") -> str:
    stem = re.sub(r"[^0-9A-Za-z가-힣._-]+", "-", name or "").strip("-._")
    return stem[:120] or fallback


def store_template_source(filename: str, data: bytes, pasted_text: str = "") -> dict[str, Any]:
    ensure_dirs()
    ext = Path(filename or "").suffix.lower()
    if data:
        digest = hashlib.sha1(data).hexdigest()[:16]
        stored_name = f"{safe_filename(Path(filename).stem, 'template')}-{digest}{ext or '.bin'}"
        stored_path = TEMPLATE_DIR / stored_name
        stored_path.write_bytes(data)
        return {
            "mode": "uploaded_file",
            "filename": filename,
            "storedName": stored_name,
            "extension": ext,
            "sha1": hashlib.sha1(data).hexdigest(),
            "bytes": len(data),
            "preservable": ext in {".hwpx", ".docx", ".pdf", ".hwp"},
            "storedAt": dt.datetime.now().isoformat(timespec="seconds"),
        }
    if pasted_text.strip():
        digest = hashlib.sha1(pasted_text.encode("utf-8")).hexdigest()[:16]
        stored_name = f"pasted-template-{digest}.txt"
        (TEMPLATE_DIR / stored_name).write_text(pasted_text, encoding="utf-8")
        return {
            "mode": "pasted_text",
            "filename": filename or "pasted-template.txt",
            "storedName": stored_name,
            "extension": ".txt",
            "sha1": hashlib.sha1(pasted_text.encode("utf-8")).hexdigest(),
            "bytes": len(pasted_text.encode("utf-8")),
            "preservable": False,
            "storedAt": dt.datetime.now().isoformat(timespec="seconds"),
        }
    return {"mode": "none", "preservable": False}


def version_store_path(profile_id: str = "") -> Path:
    key = safe_filename(profile_id or "default-workspace", "default-workspace")
    return VERSION_DIR / f"{key}.json"


def read_version_store(profile_id: str = "") -> dict[str, Any]:
    ensure_dirs()
    path = version_store_path(profile_id)
    if not path.exists():
        return {"profileId": profile_id or "", "versions": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("versions"), list):
            return data
    except Exception:
        pass
    return {"profileId": profile_id or "", "versions": []}


def write_version_store(profile_id: str, store: dict[str, Any]) -> dict[str, Any]:
    ensure_dirs()
    store["profileId"] = profile_id or ""
    version_store_path(profile_id).write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")
    return store


def version_summary(version: dict[str, Any]) -> dict[str, Any]:
    plan = version.get("plan") or {}
    scorecard = plan.get("proposalScorecard") or {}
    return {
        "id": version.get("id", ""),
        "label": version.get("label", "초안"),
        "source": version.get("source", "manual"),
        "companyName": plan.get("companyName", ""),
        "grantName": plan.get("grantName", ""),
        "score": scorecard.get("score", ""),
        "sectionCount": len(plan.get("sections") or []),
        "createdAt": version.get("createdAt", ""),
        "updatedAt": version.get("updatedAt", ""),
    }


def list_draft_versions(profile_id: str = "") -> dict[str, Any]:
    store = read_version_store(profile_id)
    versions = sorted(store.get("versions", []), key=lambda item: item.get("createdAt", ""), reverse=True)
    return {"profileId": profile_id or "", "versions": [version_summary(version) for version in versions]}


def save_draft_version(payload: dict[str, Any]) -> dict[str, Any]:
    profile_id = payload.get("profileId") or "default-workspace"
    plan = payload.get("plan") or {}
    if not plan:
        raise ValueError("저장할 초안이 없습니다.")
    now = dt.datetime.now().isoformat(timespec="seconds")
    raw = json.dumps({"plan": plan, "workspace": payload.get("workspace") or {}, "createdAt": now}, ensure_ascii=False)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10]
    version = {
        "id": f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{digest}",
        "label": clean_text(payload.get("label") or "초안 저장본")[:80],
        "source": payload.get("source") or "manual",
        "plan": plan,
        "workspace": payload.get("workspace") or {},
        "createdAt": now,
        "updatedAt": now,
    }
    store = read_version_store(profile_id)
    versions = [version] + list(store.get("versions", []))
    store["versions"] = versions[:30]
    write_version_store(profile_id, store)
    return {"profileId": profile_id, "version": version_summary(version), "versions": list_draft_versions(profile_id)["versions"]}


def get_draft_version(profile_id: str, version_id: str) -> dict[str, Any]:
    store = read_version_store(profile_id)
    for version in store.get("versions", []):
        if version.get("id") == version_id:
            return {"profileId": profile_id, "version": version}
    raise FileNotFoundError("초안 버전을 찾을 수 없습니다.")


def update_draft_version(payload: dict[str, Any]) -> dict[str, Any]:
    profile_id = payload.get("profileId") or "default-workspace"
    version_id = payload.get("versionId") or ""
    plan = payload.get("plan") or {}
    if not version_id:
        raise ValueError("수정할 버전 ID가 필요합니다.")
    if not plan:
        raise ValueError("저장할 초안이 없습니다.")
    store = read_version_store(profile_id)
    now = dt.datetime.now().isoformat(timespec="seconds")
    for version in store.get("versions", []):
        if version.get("id") == version_id:
            version["label"] = clean_text(payload.get("label") or version.get("label") or "수정본")[:80]
            version["source"] = payload.get("source") or version.get("source") or "edited"
            version["plan"] = plan
            version["workspace"] = payload.get("workspace") or version.get("workspace") or {}
            version["updatedAt"] = now
            write_version_store(profile_id, store)
            return {"profileId": profile_id, "version": version_summary(version), "versions": list_draft_versions(profile_id)["versions"]}
    raise FileNotFoundError("수정할 초안 버전을 찾을 수 없습니다.")


def export_draft_version(profile_id: str, version_id: str) -> dict[str, Any]:
    version = get_draft_version(profile_id, version_id)["version"]
    result = create_export(version.get("plan") or {})
    result["version"] = version_summary(version)
    return result


def comment_lines(comments: str) -> list[str]:
    cleaned = clean_text(comments)
    lines = [line.strip(" -•\t") for line in re.split(r"[\n\r]+", cleaned) if line.strip(" -•\t")]
    if len(lines) <= 1:
        parts = re.split(r"(?<=[.!?。])\s+|[;；]+", cleaned)
        lines = [part.strip(" -•\t") for part in parts if part.strip(" -•\t")]
    return lines[:12]


def comment_targets(comment: str) -> set[str]:
    text = comment.lower()
    rules = {
        "problem": ["문제", "pain", "고객 불편", "니즈", "필요성"],
        "solution": ["솔루션", "해결", "제품", "서비스", "기능", "기술"],
        "market": ["시장", "고객", "타깃", "수요", "경쟁", "시장성"],
        "differentiation": ["차별", "경쟁", "강점", "우위", "대체재"],
        "business_model": ["수익", "매출", "가격", "bm", "비즈니스모델", "판매"],
        "growth": ["일정", "로드맵", "마일스톤", "성장", "확장"],
        "budget": ["예산", "자금", "지원금", "사업비", "비용"],
        "team": ["팀", "대표", "인력", "역량", "채용"],
        "impact": ["효과", "고용", "파급", "사회", "지역", "esg"],
        "risk": ["리스크", "위험", "보완", "한계", "대응"],
    }
    matched = {category for category, keywords in rules.items() if any(keyword in text for keyword in keywords)}
    return matched or {"overview"}


def section_revision_comments(section: dict[str, Any], lines: list[str]) -> list[str]:
    category = section.get("category") or "overview"
    heading = clean_text(section.get("heading", "")).lower()
    selected: list[str] = []
    for line in lines:
        targets = comment_targets(line)
        if category in targets or "overview" in targets or any(token and token in heading for token in re.findall(r"[0-9A-Za-z가-힣]{2,}", line.lower())[:4]):
            selected.append(line)
    return selected[:4]


def revise_plan_with_comments(base_plan: dict[str, Any], comments: str, label: str = "") -> dict[str, Any]:
    lines = comment_lines(comments)
    if not lines:
        raise ValueError("반영할 코멘트를 입력해 주세요.")
    plan = json.loads(json.dumps(base_plan, ensure_ascii=False))
    now = dt.datetime.now().isoformat(timespec="seconds")
    revision_no = len(plan.get("revisionHistory") or []) + 1
    memo = " / ".join(lines[:4])
    plan["title"] = f"{plan.get('companyName', '회사')} {plan.get('grantName', '지원사업')} 사업계획서 개정본 v{revision_no}"
    plan["summary"] = f"{plan.get('summary', '')}\n\n개정 방향: {memo}".strip()
    plan["generatedAt"] = now
    plan["revisedAt"] = now
    plan.setdefault("revisionHistory", []).append(
        {
            "version": revision_no,
            "label": label or f"코멘트 반영 v{revision_no}",
            "comments": lines,
            "createdAt": now,
        }
    )
    for index, section in enumerate(plan.get("sections") or [], start=1):
        selected = section_revision_comments(section, lines)
        if not selected:
            continue
        guidance = " ".join(selected)
        addition = (
            "\n\n개정 보강: 심사위원이 확인할 핵심 쟁점을 더 선명하게 만들기 위해 "
            f"{guidance} 방향을 반영했다. 따라서 본 항목은 기존 주장에 더해 실행 근거, 정량 지표, "
            "지원금 사용과 성과의 연결성을 우선적으로 제시한다."
        )
        section["content"] = f"{clean_text(section.get('content', ''))}{addition}".strip()
        section["answerStrategy"] = f"{section.get('answerStrategy', '')} 개정 코멘트 반영: {guidance[:220]}".strip()
        section.setdefault("revisionNotes", []).append({"comments": selected, "revisedAt": now})
        section["heading"] = section.get("heading") or f"{index}. 사업계획 항목"
    plan.setdefault("qualityChecks", []).append(
        {
            "label": "코멘트 기반 개정",
            "status": "ok",
            "message": f"{len(lines)}개 코멘트를 반영해 새 사업계획서 버전을 생성했습니다.",
        }
    )
    return plan


def revise_draft_version(payload: dict[str, Any]) -> dict[str, Any]:
    profile_id = payload.get("profileId") or "default-workspace"
    version_id = payload.get("versionId") or ""
    base_plan = payload.get("plan") or {}
    if version_id:
        base_plan = get_draft_version(profile_id, version_id)["version"].get("plan") or base_plan
    if not base_plan:
        raise ValueError("기준 사업계획서가 없습니다.")
    comments = payload.get("comments") or ""
    label = clean_text(payload.get("label") or "코멘트 반영본")[:80]
    revised_plan = revise_plan_with_comments(base_plan, comments, label)
    workspace = payload.get("workspace") or {}
    workspace["plan"] = revised_plan
    saved = save_draft_version(
        {
            "profileId": profile_id,
            "label": label,
            "source": "comment_revision",
            "plan": revised_plan,
            "workspace": workspace,
        }
    )
    return {"profileId": profile_id, "plan": revised_plan, "version": saved["version"], "versions": saved["versions"]}


DEFAULT_GRANT_SUCCESS_DATASET: dict[str, Any] = {
    "version": "DSW-Success-Criteria-2026.06",
    "updatedAt": "2026-06-17",
    "programTypes": [
        {
            "id": "early_startup",
            "name": "초기창업·사업화",
            "keywords": ["초기창업", "창업패키지", "사업화", "예비창업", "창업도약"],
            "scoringWeights": [
                {"label": "문제·고객 명확성", "weight": 15},
                {"label": "시장성과 사업화 가능성", "weight": 25},
                {"label": "차별성·실현 가능성", "weight": 20},
                {"label": "팀 역량", "weight": 15},
                {"label": "사업비 적정성", "weight": 15},
                {"label": "파급효과", "weight": 10},
            ],
            "successPatterns": [
                "초기 고객군이 좁고 명확하다.",
                "지원금 사용처가 MVP, 고객 검증, 매출 전환과 직접 연결된다.",
                "파일럿, 인터뷰, LOI, 재구매 의향 등 근거가 문항별로 연결된다.",
                "매출 계획이 고객 수, 가격, 전환율 가정으로 설명된다.",
            ],
            "rejectionRisks": [
                "시장 규모만 크고 초기 고객 확보 경로가 약하다.",
                "지원금 사용 계획이 산출물과 연결되지 않는다.",
                "팀 역량이 이력 나열에 머물고 실행 역할이 불분명하다.",
                "법적 정보, 사업자등록증, 증빙자료와 본문 내용이 불일치한다.",
            ],
            "evidenceChecklist": ["고객 인터뷰", "파일럿 결과", "시장 근거", "견적서", "사업자등록증", "팀 이력"],
        },
        {
            "id": "rnd_tech",
            "name": "R&D·기술개발",
            "keywords": ["R&D", "기술개발", "연구개발", "디딤돌", "창업성장", "초격차"],
            "scoringWeights": [
                {"label": "기술 혁신성", "weight": 25},
                {"label": "개발 목표 명확성", "weight": 20},
                {"label": "사업화 가능성", "weight": 20},
                {"label": "수행 역량", "weight": 20},
                {"label": "지식재산·인증", "weight": 15},
            ],
            "successPatterns": [
                "기술 개발 목표가 기능, 성능, 검증 방식으로 정의된다.",
                "기술 차별성이 경쟁 기술과 비교된다.",
                "개발 결과가 매출, 인증, 고객 도입으로 이어지는 경로가 있다.",
            ],
            "rejectionRisks": [
                "기술 용어는 많지만 검증 기준이 없다.",
                "개발 범위가 지원기간 대비 과도하다.",
                "사업화 고객이나 적용 시장이 불분명하다.",
            ],
            "evidenceChecklist": ["기술명세", "성능 목표", "특허/출원", "시험 계획", "개발 인력 이력"],
        },
        {
            "id": "voucher_export",
            "name": "바우처·수출·마케팅",
            "keywords": ["바우처", "수출", "마케팅", "판로", "글로벌", "해외"],
            "scoringWeights": [
                {"label": "목표 시장 적합성", "weight": 25},
                {"label": "실행 계획", "weight": 25},
                {"label": "성과 지표", "weight": 20},
                {"label": "예산 적정성", "weight": 15},
                {"label": "후속 성장성", "weight": 15},
            ],
            "successPatterns": [
                "타깃 채널과 고객 획득 비용 가정이 구체적이다.",
                "광고, 콘텐츠, 전시, 해외 진출 활동이 성과 지표와 연결된다.",
                "지원 이후 반복 가능한 판매 채널이 남는다.",
            ],
            "rejectionRisks": [
                "마케팅 활동 나열만 있고 성과 지표가 없다.",
                "예산이 매출 또는 고객 확보와 직접 연결되지 않는다.",
                "기존 고객/시장 근거가 부족하다.",
            ],
            "evidenceChecklist": ["채널별 계획", "고객 페르소나", "랜딩/콘텐츠", "견적서", "기존 매출/문의"],
        },
    ],
}


def read_grant_success_dataset() -> dict[str, Any]:
    ensure_dirs()
    if not GRANT_DATASET_FILE.exists():
        GRANT_DATASET_FILE.write_text(json.dumps(DEFAULT_GRANT_SUCCESS_DATASET, ensure_ascii=False, indent=2), encoding="utf-8")
        return DEFAULT_GRANT_SUCCESS_DATASET
    try:
        data = json.loads(GRANT_DATASET_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("programTypes"), list):
            if dataset_has_mojibake(data):
                GRANT_DATASET_FILE.write_text(json.dumps(DEFAULT_GRANT_SUCCESS_DATASET, ensure_ascii=False, indent=2), encoding="utf-8")
                return DEFAULT_GRANT_SUCCESS_DATASET
            return data
    except Exception:
        pass
    return DEFAULT_GRANT_SUCCESS_DATASET


def match_success_criteria(title: str, text: str) -> dict[str, Any]:
    dataset = read_grant_success_dataset()
    haystack = f"{title}\n{text[:8000]}".lower()
    best: dict[str, Any] | None = None
    best_score = -1
    for item in dataset.get("programTypes", []):
        score = sum(1 for keyword in item.get("keywords", []) if keyword.lower() in haystack)
        if score > best_score:
            best_score = score
            best = item
    if best is None:
        best = (dataset.get("programTypes") or [{}])[0]
    result = json.loads(json.dumps(best, ensure_ascii=False))
    result["matchedKeywordCount"] = max(best_score, 0)
    result["datasetVersion"] = dataset.get("version", "")
    return result


DEFAULT_GRANT_SUCCESS_DATASET = {
    "version": "DSW-Success-Criteria-2026.06",
    "updatedAt": "2026-06-17",
    "programTypes": [
        {
            "id": "early_startup",
            "name": "초기창업·사업화",
            "keywords": ["초기창업", "창업패키지", "사업화", "예비창업", "창업기업", "MVP", "고객검증"],
            "scoringWeights": [
                {"label": "문제·고객 명확성", "weight": 15},
                {"label": "시장성과 사업화 가능성", "weight": 25},
                {"label": "차별성·실현 가능성", "weight": 20},
                {"label": "팀 역량", "weight": 15},
                {"label": "사업비 적정성", "weight": 15},
                {"label": "파급효과", "weight": 10},
            ],
            "successPatterns": [
                "초기 고객군이 좁고 명확하며 반복되는 문제를 구체적으로 설명한다.",
                "지원금 사용처가 MVP 고도화, 고객 검증, 매출 전환과 직접 연결된다.",
                "파일럿, 인터뷰, LOI, 구매의향 등 증빙이 문항별 주장과 연결된다.",
                "매출 계획이 고객 수, 가격, 전환율 가정으로 설명된다.",
            ],
            "rejectionRisks": [
                "시장 규모만 크고 초기 고객 확보 경로가 약하다.",
                "지원금 사용 계획이 산출물과 연결되지 않는다.",
                "팀 이력이 나열에 머물고 실행 역할이 불분명하다.",
                "법적 정보, 사업자등록증, 증빙자료와 본문 내용이 불일치한다.",
            ],
            "evidenceChecklist": ["고객 인터뷰", "파일럿 결과", "시장 근거", "견적서", "사업자등록증", "팀 이력"],
        },
        {
            "id": "rnd_tech",
            "name": "R&D·기술개발",
            "keywords": ["R&D", "기술개발", "연구개발", "딥테크", "기술창업", "초격차", "특허"],
            "scoringWeights": [
                {"label": "기술 혁신성", "weight": 25},
                {"label": "개발 목표 명확성", "weight": 20},
                {"label": "사업화 가능성", "weight": 20},
                {"label": "수행 역량", "weight": 20},
                {"label": "지식재산·인증", "weight": 15},
            ],
            "successPatterns": [
                "기술개발 목표가 기능, 성능, 검증 방식으로 정의된다.",
                "기술 차별성이 경쟁 기술과 비교된다.",
                "개발 결과가 매출, 인증, 고객 도입으로 이어지는 경로가 있다.",
            ],
            "rejectionRisks": [
                "기술 용어는 많지만 검증 기준이 없다.",
                "개발 범위가 지원기간 대비 과도하다.",
                "사업화 고객이나 적용 시장이 불분명하다.",
            ],
            "evidenceChecklist": ["기술명세", "성능 목표", "특허/출원", "시험 계획", "개발 인력 이력"],
        },
        {
            "id": "voucher_export",
            "name": "바우처·수출·마케팅",
            "keywords": ["바우처", "수출", "마케팅", "판로", "글로벌", "해외", "브랜딩"],
            "scoringWeights": [
                {"label": "목표 시장 적합성", "weight": 25},
                {"label": "실행 계획", "weight": 25},
                {"label": "성과 지표", "weight": 20},
                {"label": "예산 적정성", "weight": 15},
                {"label": "후속 성장성", "weight": 15},
            ],
            "successPatterns": [
                "타깃 채널과 고객 획득 비용 가정이 구체적이다.",
                "광고, 콘텐츠, 전시, 해외 진출 활동이 성과 지표와 연결된다.",
                "지원 이후 반복 가능한 판매 채널이 남는다.",
            ],
            "rejectionRisks": [
                "마케팅 활동 나열만 있고 성과 지표가 없다.",
                "예산이 매출 또는 고객 확보와 직접 연결되지 않는다.",
                "기존 고객·시장 근거가 부족하다.",
            ],
            "evidenceChecklist": ["채널별 계획", "고객 페르소나", "브랜딩/콘텐츠", "견적서", "기존 매출/문의"],
        },
    ],
}


def dataset_has_mojibake(data: dict[str, Any]) -> bool:
    sample = json.dumps(data, ensure_ascii=False)[:4000]
    markers = ["珥", "吏", "怨", "??", "媛", "遺"]
    return sum(1 for marker in markers if marker in sample) >= 2


def log_line(message: str) -> None:
    line = f"[{dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n"
    try:
        if sys.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
    except Exception:
        pass
    try:
        with LOG_FILE.open("a", encoding="utf-8") as log:
            log.write(line)
    except Exception:
        pass


def load_env_file(path: Path | None = None) -> None:
    env_path = path or (ROOT / ".env")
    if not env_path.exists():
        return
    try:
        lines = env_path.read_text(encoding="utf-8-sig").splitlines()
    except UnicodeDecodeError:
        lines = env_path.read_text(encoding="cp949").splitlines()
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        value_text = raw_value.strip()
        if (value_text.startswith('"') and value_text.endswith('"')) or (value_text.startswith("'") and value_text.endswith("'")):
            value_text = value_text[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value_text


def openai_api_key() -> str:
    return os.environ.get("OPENAI_API_KEY", "").strip()


def anthropic_api_key() -> str:
    return os.environ.get("ANTHROPIC_API_KEY", "").strip()


def gemini_api_key() -> str:
    return os.environ.get("GEMINI_API_KEY", "").strip() or os.environ.get("GOOGLE_API_KEY", "").strip()


def provider_status() -> dict[str, Any]:
    return {
        "openai": {"configured": bool(openai_api_key()), "env": "OPENAI_API_KEY"},
        "anthropic": {"configured": bool(anthropic_api_key()), "env": "ANTHROPIC_API_KEY"},
        "google": {"configured": bool(gemini_api_key()), "env": "GEMINI_API_KEY or GOOGLE_API_KEY"},
    }


def ai_settings_payload() -> dict[str, Any]:
    providers = provider_status()
    return {
        "configured": any(item["configured"] for item in providers.values()),
        "apiKeyEnv": "OPENAI_API_KEY / ANTHROPIC_API_KEY / GEMINI_API_KEY",
        "providers": providers,
        "assignments": json.loads(json.dumps(AI_MODEL_ASSIGNMENTS, ensure_ascii=False)),
        "recommendation": (
            "역할별 최적 배치로 설정했습니다. 한글 보고서 1차 초안은 Gemini 3.5 Flash, "
            "제출용 정제와 형식 검증은 GPT-5.5, 최종 심사위원 관점 감사는 Claude Opus 4.8, "
            "이미지 생성은 Gemini 3 Pro Image를 우선 사용합니다."
        ),
        "runtimeNote": (
            "GEMINI_API_KEY가 있으면 Gemini 3.5 Flash로 1차 초안을 만들고, OPENAI_API_KEY가 있으면 GPT-5.5로 제출용 정제를 수행하며, "
            "ANTHROPIC_API_KEY가 있으면 Claude Opus 4.8로 최종 리스크 리뷰를 추가합니다. "
            "키가 없거나 호출에 실패하면 로컬 규칙 기반 생성기로 자동 전환합니다."
        ),
    }


def deep_merge(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    result = json.loads(json.dumps(base, ensure_ascii=False))
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def read_company() -> dict[str, Any]:
    if not COMPANY_FILE.exists():
        return DEFAULT_COMPANY
    try:
        return deep_merge(DEFAULT_COMPANY, json.loads(COMPANY_FILE.read_text(encoding="utf-8")))
    except Exception:
        return DEFAULT_COMPANY


def write_company(company: dict[str, Any]) -> dict[str, Any]:
    ensure_dirs()
    merged = deep_merge(DEFAULT_COMPANY, company)
    COMPANY_FILE.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return merged


def profile_id_for(name: str) -> str:
    base = clean_text(name or "company").lower()
    digest = hashlib.sha1(base.encode("utf-8")).hexdigest()[:10]
    slug = re.sub(r"[^0-9a-z가-힣]+", "-", base).strip("-")[:32] or "company"
    return f"{slug}-{digest}"


def profile_name(company: dict[str, Any]) -> str:
    return value(company, "basic.name", "미입력 회사")


def profile_summary(profile: dict[str, Any]) -> dict[str, Any]:
    company = deep_merge(DEFAULT_COMPANY, profile.get("company") or {})
    return {
        "id": profile.get("id"),
        "name": profile.get("name") or profile_name(company),
        "industry": value(company, "basic.industry", ""),
        "ceo": value(company, "basic.ceo", ""),
        "updatedAt": profile.get("updatedAt", ""),
        "createdAt": profile.get("createdAt", ""),
    }


def read_profiles_store() -> dict[str, Any]:
    ensure_dirs()
    if PROFILES_FILE.exists():
        try:
            store = json.loads(PROFILES_FILE.read_text(encoding="utf-8"))
            if isinstance(store, dict) and isinstance(store.get("profiles"), list):
                return store
        except Exception:
            pass

    profiles: list[dict[str, Any]] = []
    if COMPANY_FILE.exists():
        company = read_company()
        if any(value(company, f"basic.{field}") for field in ["name", "ceo", "industry", "location"]):
            now = dt.datetime.now().isoformat(timespec="seconds")
            name = profile_name(company)
            profiles.append(
                {
                    "id": profile_id_for(name),
                    "name": name,
                    "company": company,
                    "workspace": {"company": company},
                    "createdAt": now,
                    "updatedAt": now,
                }
            )
    store = {"activeProfileId": profiles[0]["id"] if profiles else "", "profiles": profiles}
    write_profiles_store(store)
    return store


def write_profiles_store(store: dict[str, Any]) -> dict[str, Any]:
    ensure_dirs()
    PROFILES_FILE.write_text(json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8")
    return store


def list_profiles() -> dict[str, Any]:
    store = read_profiles_store()
    return {
        "activeProfileId": store.get("activeProfileId", ""),
        "profiles": [profile_summary(profile) for profile in store.get("profiles", [])],
    }


def get_profile(profile_id: str) -> dict[str, Any] | None:
    store = read_profiles_store()
    for profile in store.get("profiles", []):
        if profile.get("id") == profile_id:
            profile["company"] = deep_merge(DEFAULT_COMPANY, profile.get("company") or {})
            profile.setdefault("workspace", {})
            return profile
    return None


def save_profile(payload: dict[str, Any]) -> dict[str, Any]:
    store = read_profiles_store()
    company = deep_merge(DEFAULT_COMPANY, payload.get("company") or {})
    name = profile_name(company)
    profile_id = payload.get("profileId") or payload.get("id") or profile_id_for(name)
    now = dt.datetime.now().isoformat(timespec="seconds")
    workspace = payload.get("workspace") or {}
    workspace["company"] = company

    profiles = store.get("profiles", [])
    existing = next((profile for profile in profiles if profile.get("id") == profile_id), None)
    if existing is None:
        existing = {
            "id": profile_id,
            "createdAt": now,
        }
        profiles.append(existing)

    existing.update(
        {
            "name": name,
            "company": company,
            "workspace": workspace,
            "updatedAt": now,
        }
    )
    store["profiles"] = profiles
    store["activeProfileId"] = profile_id
    write_profiles_store(store)
    write_company(company)
    return {"profile": existing, "profiles": list_profiles()["profiles"], "activeProfileId": profile_id}


def read_active_company() -> dict[str, Any]:
    store = read_profiles_store()
    active_id = store.get("activeProfileId", "")
    if active_id:
        profile = get_profile(active_id)
        if profile:
            return deep_merge(DEFAULT_COMPANY, profile.get("company") or {})
    return read_company()


def decode_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp949", "euc-kr", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def clean_text(value: str) -> str:
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def text_from_docx(data: bytes) -> str:
    lines: list[str] = []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = [
            name
            for name in archive.namelist()
            if name.startswith("word/") and name.endswith(".xml") and ("document" in name or "header" in name or "footer" in name)
        ]
        for name in names:
            try:
                root = ET.fromstring(archive.read(name))
            except ET.ParseError:
                continue
            for paragraph in root.iter():
                if not paragraph.tag.endswith("}p"):
                    continue
                text_parts: list[str] = []
                for node in paragraph.iter():
                    if node.tag.endswith("}t") and node.text:
                        text_parts.append(node.text)
                    elif node.tag.endswith("}tab"):
                        text_parts.append("\t")
                    elif node.tag.endswith("}br"):
                        text_parts.append("\n")
                line = "".join(text_parts).strip()
                if line:
                    lines.append(line)
    return clean_text("\n".join(lines))


def text_from_hwpx(data: bytes) -> str:
    lines: list[str] = []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        xml_names = [
            name
            for name in archive.namelist()
            if name.lower().endswith(".xml")
            and (
                "section" in name.lower()
                or name.lower().startswith("contents/")
                or name.lower().startswith("content/")
            )
        ]
        for name in sorted(xml_names):
            try:
                root = ET.fromstring(archive.read(name))
            except ET.ParseError:
                continue
            for paragraph in root.iter():
                if not paragraph.tag.endswith("}p") and paragraph.tag.split("}")[-1] not in {"p", "para"}:
                    continue
                text_parts: list[str] = []
                for node in paragraph.iter():
                    local = node.tag.split("}")[-1]
                    if local in {"t", "text"} and node.text:
                        text_parts.append(node.text)
                    elif local in {"lineBreak", "br"}:
                        text_parts.append("\n")
                    elif local == "tab":
                        text_parts.append("\t")
                line = "".join(text_parts).strip()
                if line:
                    lines.append(line)
    if lines:
        return clean_text("\n".join(lines))

    # Fallback for nonstandard XML: collect leaf text.
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for name in sorted(n for n in archive.namelist() if n.lower().endswith(".xml")):
            try:
                root = ET.fromstring(archive.read(name))
            except ET.ParseError:
                continue
            for node in root.iter():
                if node.text and node.text.strip():
                    lines.append(node.text.strip())
    return clean_text("\n".join(lines))


def text_from_pdf(data: bytes) -> str:
    try:
        import pdfplumber  # type: ignore
    except Exception as exc:
        raise RuntimeError("PDF 추출에는 pdfplumber가 필요합니다. Codex 번들 Python으로 실행하면 사용할 수 있습니다.") from exc

    lines: list[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages[:30]:
            page_text = page.extract_text() or ""
            if page_text.strip():
                lines.append(page_text)
    return clean_text("\n\n".join(lines))


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def ocr_image_bytes(data: bytes, ext: str, notes: list[str]) -> str:
    if not data:
        return ""
    cmd = os.environ.get("TESSERACT_CMD", "tesseract")
    lang = os.environ.get("OCR_LANG", "kor+eng")
    suffix = ext if ext in IMAGE_EXTENSIONS else ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(data)
        tmp_path = tmp.name
    try:
        result = subprocess.run(
            [cmd, tmp_path, "stdout", "-l", lang],
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            notes.append(f"OCR 엔진({cmd}, {lang})으로 이미지 텍스트를 추출했습니다.")
            return clean_text(result.stdout)
        detail = (result.stderr or result.stdout or "").strip()[:240]
        notes.append(f"OCR 엔진 호출 결과 텍스트를 얻지 못했습니다. {detail}".strip())
        return ""
    except FileNotFoundError:
        notes.append("OCR 엔진이 설치되어 있지 않습니다. Tesseract 설치 후 TESSERACT_CMD/OCR_LANG을 설정하면 이미지 문서를 분석할 수 있습니다.")
        return ""
    except Exception as exc:
        notes.append(f"OCR 처리 실패: {exc}")
        return ""
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def build_ocr_status(filename: str, extracted_text: str, notes: list[str]) -> dict[str, Any]:
    ext = Path(filename or "").suffix.lower()
    needs_ocr = ext in IMAGE_EXTENSIONS or (ext == ".pdf" and len(clean_text(extracted_text)) < 40)
    engine = os.environ.get("TESSERACT_CMD", "tesseract")
    available = bool(shutil.which(engine))
    status = "not_needed"
    if needs_ocr and extracted_text.strip():
        status = "completed_or_text_available"
    elif needs_ocr:
        status = "needs_ocr"
    return {
        "status": status,
        "needsOCR": needs_ocr,
        "engine": engine,
        "language": os.environ.get("OCR_LANG", "kor+eng"),
        "configured": available,
        "message": "텍스트 추출이 충분합니다."
        if status == "not_needed"
        else ("OCR 또는 이미지 텍스트 추출이 필요합니다." if status == "needs_ocr" else "OCR 또는 대체 추출로 텍스트를 확보했습니다."),
        "notes": notes,
    }


def extract_text(filename: str, data: bytes, pasted_text: str = "") -> tuple[str, list[str]]:
    ext = Path(filename or "").suffix.lower()
    notes: list[str] = []
    if pasted_text.strip():
        notes.append("붙여넣은 텍스트를 함께 반영했습니다.")
    try:
        if ext in {".txt", ".md", ".csv", ".json"}:
            extracted = decode_text(data)
        elif ext == ".docx":
            extracted = text_from_docx(data)
        elif ext == ".hwpx":
            extracted = text_from_hwpx(data)
        elif ext == ".pdf":
            extracted = text_from_pdf(data)
            if len(clean_text(extracted)) < 40 and data:
                notes.append("PDF에서 텍스트가 거의 추출되지 않았습니다. 스캔 PDF일 가능성이 있어 OCR 처리가 필요할 수 있습니다.")
        elif ext in IMAGE_EXTENSIONS:
            extracted = ocr_image_bytes(data, ext, notes)
        elif ext == ".hwp":
            extracted = ""
            notes.append("구형 .hwp 바이너리는 직접 텍스트 추출이 제한됩니다. 양식 내용을 텍스트로 붙여넣으면 분석 정확도가 올라갑니다.")
        elif data:
            extracted = decode_text(data)
            notes.append(f"{ext or '알 수 없는 형식'} 파일을 일반 텍스트로 해석했습니다.")
        else:
            extracted = ""
    except Exception as exc:
        extracted = ""
        notes.append(f"파일 텍스트 추출 실패: {exc}")

    combined = clean_text("\n\n".join(part for part in [extracted, pasted_text] if part and part.strip()))
    return combined, notes


def infer_document_type(filename: str, text: str) -> str:
    haystack = f"{filename}\n{text[:3000]}".lower()
    if "사업자등록" in haystack or "business registration" in haystack:
        return "business_registration"
    if "등기부" in haystack or "등기사항" in haystack or "법인등기" in haystack:
        return "corporate_registry"
    if "사업계획" in haystack or "business plan" in haystack or "창업아이템" in haystack:
        return "existing_business_plan"
    if "재무" in haystack or "손익" in haystack or "매출" in haystack or "balance sheet" in haystack:
        return "finance"
    if "특허" in haystack or "상표" in haystack or "인증" in haystack:
        return "ip_certification"
    return "general"


def document_type_label(document_type: str) -> str:
    labels = {
        "business_registration": "사업자등록증",
        "corporate_registry": "등기부등본",
        "existing_business_plan": "기존 사업계획서",
        "finance": "재무자료",
        "ip_certification": "지식재산·인증",
        "general": "일반 참고자료",
    }
    return labels.get(document_type, "일반 참고자료")


def compact_value(value_text: str) -> str:
    value_text = re.sub(r"\s+", " ", value_text).strip(" :：|/\t")
    value_text = re.sub(r"(발급|교부|증명|확인).*$", "", value_text).strip()
    return value_text[:120]


def find_labeled_value(text: str, labels: list[str]) -> str:
    for label in labels:
        patterns = [
            rf"{re.escape(label)}\s*[:：]\s*([^\n\r]+)",
            rf"{re.escape(label)}\s+([^\n\r]+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value_text = compact_value(match.group(1))
                if value_text and value_text != label:
                    return value_text
    return ""


def add_fact(facts: list[dict[str, str]], key: str, label: str, value_text: str, source: str) -> None:
    value_text = compact_value(value_text)
    if not value_text:
        return
    if any(fact.get("key") == key and fact.get("value") == value_text for fact in facts):
        return
    facts.append({"key": key, "label": label, "value": value_text, "source": source})


def extract_document_facts(text: str, document_type: str) -> tuple[list[dict[str, str]], dict[str, Any]]:
    facts: list[dict[str, str]] = []
    patch: dict[str, Any] = {"basic": {}, "legal": {}, "business": {}, "market": {}, "traction": {}, "team": {}, "finance": {}, "impact": {}, "knowledge": {}}

    business_number = re.search(r"\b\d{3}-\d{2}-\d{5}\b", text)
    if business_number:
        patch["legal"]["businessNumber"] = business_number.group(0)
        add_fact(facts, "legal.businessNumber", "사업자등록번호", business_number.group(0), document_type_label(document_type))

    corporate_number = re.search(r"\b\d{6}-\d{7}\b", text)
    if corporate_number:
        patch["legal"]["corporateNumber"] = corporate_number.group(0)
        add_fact(facts, "legal.corporateNumber", "법인등록번호", corporate_number.group(0), document_type_label(document_type))

    field_rules = [
        ("basic.name", "회사명", ["상호", "법인명", "회사명", "명칭"]),
        ("basic.ceo", "대표자", ["대표자", "대표이사", "성명"]),
        ("basic.location", "소재지", ["사업장 소재지", "본점", "주소", "소재지"]),
        ("basic.founded", "설립·개업일", ["개업년월일", "설립일", "회사성립연월일", "설립"]),
        ("legal.businessType", "업태", ["업태", "사업의 종류"]),
        ("legal.businessItem", "종목", ["종목", "목적", "사업목적"]),
        ("legal.capital", "자본금", ["자본금", "발행주식의 총수"]),
        ("legal.registryOffice", "등기 관할", ["등기소", "관할등기소"]),
        ("legal.registrationStatus", "등록 상태", ["사업자 상태", "상태", "등기상태"]),
    ]
    for path, label, labels in field_rules:
        found = find_labeled_value(text, labels)
        if found:
            group, key = path.split(".", 1)
            patch[group][key] = found
            add_fact(facts, path, label, found, document_type_label(document_type))

    if document_type == "existing_business_plan":
        first_pitch = find_business_plan_signal(text, ["한 줄", "요약", "개요", "사업 아이템", "창업아이템"])
        if first_pitch:
            patch["business"]["oneLine"] = first_pitch
            add_fact(facts, "business.oneLine", "사업 아이템 요약", first_pitch, "기존 사업계획서")
        problem = find_business_plan_signal(text, ["문제", "필요성", "고객 니즈", "배경"])
        if problem:
            patch["business"]["problem"] = problem
        solution = find_business_plan_signal(text, ["제품", "서비스", "솔루션", "기술"])
        if solution:
            patch["business"]["solution"] = solution
        market = find_business_plan_signal(text, ["시장", "고객", "수요", "타깃"])
        if market:
            patch["market"]["marketSize"] = market
        traction = find_business_plan_signal(text, ["성과", "검증", "실증", "고객", "매출"])
        if traction:
            patch["traction"]["metrics"] = traction

    patch = {group: {key: value for key, value in values.items() if value} for group, values in patch.items() if any(values.values())}
    return facts, patch


def find_business_plan_signal(text: str, keywords: list[str]) -> str:
    lines = [line.strip() for line in clean_text(text).splitlines() if 18 <= len(line.strip()) <= 180]
    for line in lines:
        if any(keyword in line for keyword in keywords):
            return compact_value(line)
    return ""


def document_summary(text: str, document_type: str) -> str:
    lines = [line.strip() for line in clean_text(text).splitlines() if 12 <= len(line.strip()) <= 180]
    if not lines:
        return "텍스트를 충분히 추출하지 못했습니다."
    priority_keywords = {
        "business_registration": ["상호", "대표자", "사업장", "업태", "종목"],
        "corporate_registry": ["법인명", "본점", "자본금", "목적", "대표이사"],
        "existing_business_plan": ["문제", "서비스", "시장", "차별", "매출", "성과"],
        "finance": ["매출", "손익", "비용", "자금", "투자"],
        "ip_certification": ["특허", "상표", "인증", "출원", "등록"],
        "general": ["사업", "고객", "시장", "성과", "계획"],
    }.get(document_type, ["사업", "고객", "시장", "성과", "계획"])
    selected = [line for line in lines if any(keyword in line for keyword in priority_keywords)]
    if len(selected) < 2:
        selected.extend(lines[: 3 - len(selected)])
    return " / ".join(selected[:3])


DOCUMENT_COVERAGE_AREAS: list[dict[str, Any]] = [
    {
        "id": "company_identity",
        "label": "회사 기본·법적 정보",
        "keywords": ["회사명", "상호", "대표", "사업자등록", "법인등록", "업태", "종목", "주소", "capital", "registration"],
    },
    {
        "id": "problem_customer",
        "label": "문제·고객 니즈",
        "keywords": ["문제", "고객", "니즈", "불편", "pain", "인터뷰", "수요", "VOC", "설문"],
    },
    {
        "id": "solution_product",
        "label": "제품·서비스·기술",
        "keywords": ["제품", "서비스", "솔루션", "기능", "기술", "플랫폼", "앱", "MVP", "prototype"],
    },
    {
        "id": "market_competition",
        "label": "시장·경쟁",
        "keywords": ["시장", "경쟁", "대체재", "TAM", "SAM", "SOM", "규모", "성장률", "트렌드", "market"],
    },
    {
        "id": "traction_evidence",
        "label": "검증·성과 증빙",
        "keywords": ["매출", "고객", "계약", "LOI", "MOU", "파일럿", "실증", "성과", "가입", "전환", "retention"],
    },
    {
        "id": "team_capability",
        "label": "팀 역량",
        "keywords": ["대표", "팀", "경력", "역량", "전문", "인력", "채용", "advisor", "mentor"],
    },
    {
        "id": "finance_budget",
        "label": "재무·예산·자금",
        "keywords": ["매출", "비용", "예산", "자금", "사업비", "견적", "손익", "투자", "funding", "budget"],
    },
    {
        "id": "ip_certification",
        "label": "지식재산·인증",
        "keywords": ["특허", "상표", "저작권", "인증", "허가", "출원", "등록", "IP", "certification"],
    },
    {
        "id": "impact_risk",
        "label": "기대효과·리스크",
        "keywords": ["고용", "파급", "효과", "사회", "지역", "ESG", "리스크", "대응", "보완"],
    },
]


DOCUMENT_TYPE_BASE_SCORE = {
    "existing_business_plan": 28,
    "business_registration": 20,
    "corporate_registry": 18,
    "finance": 24,
    "ip_certification": 22,
    "general": 12,
}


def content_signature(raw: bytes, text: str) -> str:
    if raw:
        return hashlib.sha1(raw).hexdigest()
    if text.strip():
        return hashlib.sha1(clean_text(text).encode("utf-8")).hexdigest()
    return ""


def evidence_candidate_lines(text: str) -> list[str]:
    lines = []
    for raw_line in clean_text(text).splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if 18 <= len(line) <= 260:
            lines.append(line)
    return lines[:900]


def line_signal_score(line: str, area: dict[str, Any]) -> int:
    compact = line.lower()
    score = 0
    for keyword in area.get("keywords", []):
        if keyword.lower() in compact:
            score += 8
    if re.search(r"\d", line):
        score += 5
    if re.search(r"\d{4}[.\-/년]\s*\d{1,2}|\d+(?:\.\d+)?\s*(?:%|명|건|원|만원|억원|개|회)", line):
        score += 8
    if any(token.lower() in compact for token in ["계약", "매출", "특허", "인증", "고객", "pilot", "loi", "mou", "revenue"]):
        score += 8
    return score


def build_evidence_snippets(text: str, document_type: str) -> list[dict[str, Any]]:
    lines = evidence_candidate_lines(text)
    candidates: list[dict[str, Any]] = []
    for line in lines:
        best_area = None
        best_score = 0
        for area in DOCUMENT_COVERAGE_AREAS:
            score = line_signal_score(line, area)
            if score > best_score:
                best_area = area
                best_score = score
        if best_area and best_score >= 12:
            candidates.append(
                {
                    "category": best_area["id"],
                    "categoryLabel": best_area["label"],
                    "text": line[:260],
                    "score": min(100, best_score),
                }
            )
    candidates.sort(key=lambda item: item["score"], reverse=True)
    seen: set[str] = set()
    snippets: list[dict[str, Any]] = []
    for item in candidates:
        marker = re.sub(r"\W+", "", item["text"].lower())[:90]
        if marker in seen:
            continue
        seen.add(marker)
        snippets.append(item)
        if len(snippets) >= 8:
            break
    return snippets


def build_coverage_tags(text: str, facts: list[dict[str, str]], snippets: list[dict[str, Any]], document_type: str = "") -> list[dict[str, Any]]:
    haystack = f"{text[:16000]}\n" + "\n".join(fact.get("label", "") + " " + fact.get("value", "") for fact in facts)
    compact = haystack.lower()
    snippet_counts: dict[str, int] = {}
    for snippet in snippets:
        snippet_counts[snippet["category"]] = snippet_counts.get(snippet["category"], 0) + 1
    tags: list[dict[str, Any]] = []
    for area in DOCUMENT_COVERAGE_AREAS:
        keyword_hits = sum(1 for keyword in area.get("keywords", []) if keyword.lower() in compact)
        snippet_count = snippet_counts.get(area["id"], 0)
        if keyword_hits or snippet_count:
            confidence = min(100, keyword_hits * 12 + snippet_count * 18)
            tags.append(
                {
                    "id": area["id"],
                    "label": area["label"],
                    "keywordHits": keyword_hits,
                    "snippetCount": snippet_count,
                    "confidence": confidence,
                }
            )
    default_coverage = {
        "existing_business_plan": ["problem_customer", "solution_product", "market_competition", "traction_evidence", "finance_budget"],
        "business_registration": ["company_identity"],
        "corporate_registry": ["company_identity"],
        "finance": ["finance_budget", "traction_evidence"],
        "ip_certification": ["ip_certification"],
    }
    existing_ids = {tag["id"] for tag in tags}
    if clean_text(text):
        for area_id in default_coverage.get(document_type, []):
            if area_id in existing_ids:
                continue
            area = next((item for item in DOCUMENT_COVERAGE_AREAS if item["id"] == area_id), None)
            if area:
                tags.append(
                    {
                        "id": area["id"],
                        "label": area["label"],
                        "keywordHits": 0,
                        "snippetCount": 0,
                        "confidence": 16,
                    }
                )
    tags.sort(key=lambda item: item["confidence"], reverse=True)
    return tags[:6]


def document_extraction_quality(text: str, notes: list[str], ocr_status: dict[str, Any]) -> dict[str, Any]:
    length = len(clean_text(text))
    score = 15
    if length >= 300:
        score += 25
    if length >= 1200:
        score += 25
    if length >= 3500:
        score += 15
    if ocr_status.get("status") == "needs_ocr":
        score -= 30
    if any("실패" in note or "failed" in note.lower() for note in notes):
        score -= 20
    score = max(0, min(100, score))
    if score >= 75:
        status = "strong"
        message = "본문 추출이 충분해 사업계획서 근거로 바로 활용하기 좋습니다."
    elif score >= 45:
        status = "partial"
        message = "핵심 문장은 추출됐지만 일부 항목은 원문 확인이나 보강이 필요합니다."
    else:
        status = "weak"
        message = "추출 텍스트가 부족합니다. 스캔본 OCR 또는 텍스트 직접 입력을 권장합니다."
    return {"score": score, "status": status, "message": message}


def document_relevance_score(document_type: str, text: str, facts: list[dict[str, str]], snippets: list[dict[str, Any]], coverage_tags: list[dict[str, Any]]) -> int:
    score = DOCUMENT_TYPE_BASE_SCORE.get(document_type, 12)
    score += min(22, len(facts) * 4)
    score += min(26, len(snippets) * 4)
    score += min(24, len(coverage_tags) * 4)
    if len(clean_text(text)) >= 1500:
        score += 8
    if re.search(r"\d+(?:\.\d+)?\s*(?:%|명|건|원|만원|억원|개|회)", text):
        score += 8
    return max(0, min(100, score))


def document_priority(score: int, quality: dict[str, Any], duplicate_of: str = "") -> str:
    if duplicate_of:
        return "duplicate"
    if quality.get("status") == "weak":
        return "needs_review"
    if score >= 75:
        return "high"
    if score >= 50:
        return "medium"
    return "low"


def recommended_document_use(document_type: str, coverage_tags: list[dict[str, Any]], score: int) -> str:
    labels = ", ".join(tag["label"] for tag in coverage_tags[:3]) or document_type_label(document_type)
    if score >= 75:
        return f"핵심 근거 문서로 우선 반영하세요. 주요 활용 영역: {labels}."
    if score >= 50:
        return f"보조 근거로 활용하고 부족한 정량 근거를 보강하세요. 관련 영역: {labels}."
    return f"참고 문서로 분류하고 추출 품질 또는 원문 내용을 확인하세요. 관련 영역: {labels}."


def build_document_library_summary(analyzed_docs: list[dict[str, Any]], facts: list[dict[str, str]]) -> dict[str, Any]:
    coverage: list[dict[str, Any]] = []
    for area in DOCUMENT_COVERAGE_AREAS:
        docs = [doc for doc in analyzed_docs if any(tag.get("id") == area["id"] for tag in doc.get("coverageTags", []))]
        snippets = sum(1 for doc in docs for snippet in doc.get("evidenceSnippets", []) if snippet.get("category") == area["id"])
        coverage.append(
            {
                "id": area["id"],
                "label": area["label"],
                "documentCount": len(docs),
                "snippetCount": snippets,
                "status": "covered" if docs else "missing",
            }
        )
    high_value = sorted(analyzed_docs, key=lambda doc: doc.get("relevanceScore", 0), reverse=True)[:8]
    warnings = [
        {
            "filename": doc.get("filename", ""),
            "message": "중복 문서입니다." if doc.get("duplicateOf") else doc.get("extractionQuality", {}).get("message", ""),
        }
        for doc in analyzed_docs
        if doc.get("extractionQuality", {}).get("status") == "weak" or doc.get("duplicateOf")
    ][:8]
    missing = [item["label"] for item in coverage if item["status"] == "missing"]
    actions: list[str] = []
    if missing:
        actions.append("부족한 근거 영역: " + ", ".join(missing[:4]))
    if any(doc.get("ocrStatus", {}).get("status") == "needs_ocr" for doc in analyzed_docs):
        actions.append("스캔 PDF/이미지 문서는 OCR 설정 또는 텍스트 직접 입력으로 보강하세요.")
    if not actions:
        actions.append("핵심 근거 영역이 고르게 확보되었습니다. 점수가 높은 문서를 초안 생성 근거로 우선 활용하세요.")
    return {
        "totalDocuments": len(analyzed_docs),
        "totalCharacters": sum(doc.get("extractedCharacters", 0) for doc in analyzed_docs),
        "totalFacts": len(facts),
        "totalEvidenceSnippets": sum(len(doc.get("evidenceSnippets", [])) for doc in analyzed_docs),
        "coverage": coverage,
        "highValueDocuments": [
            {
                "id": doc.get("id", ""),
                "filename": doc.get("filename", ""),
                "score": doc.get("relevanceScore", 0),
                "priority": doc.get("priority", ""),
            }
            for doc in high_value
        ],
        "warnings": warnings,
        "recommendedActions": actions,
    }


BUSINESS_UNDERSTANDING_AREAS: list[dict[str, Any]] = [
    {
        "id": "overview",
        "label": "사업 개요",
        "keywords": ["사업개요", "사업 개요", "아이템", "창업아이템", "비전", "미션", "핵심", "요약", "business", "overview"],
    },
    {
        "id": "problem",
        "label": "문제와 필요성",
        "keywords": ["문제", "필요성", "불편", "pain", "pain point", "애로", "한계", "배경", "수요", "needs", "고객 니즈"],
    },
    {
        "id": "customer",
        "label": "고객과 사용 시나리오",
        "keywords": ["고객", "사용자", "타깃", "목표 고객", "페르소나", "인터뷰", "VOC", "사용 시나리오", "customer", "user"],
    },
    {
        "id": "solution",
        "label": "해결 방식",
        "keywords": ["해결", "솔루션", "서비스", "제품", "기능", "플랫폼", "기술", "제공", "solution", "service", "product"],
    },
    {
        "id": "product",
        "label": "제품/서비스 구성",
        "keywords": ["MVP", "프로토타입", "제품 구성", "서비스 구성", "주요 기능", "개발", "기술 구현", "로드맵", "prototype"],
    },
    {
        "id": "market",
        "label": "시장과 경쟁",
        "keywords": ["시장", "경쟁", "대체재", "TAM", "SAM", "SOM", "규모", "성장률", "트렌드", "market", "competitor"],
    },
    {
        "id": "differentiation",
        "label": "차별성과 진입장벽",
        "keywords": ["차별", "경쟁력", "우위", "진입장벽", "독창", "혁신", "특허", "IP", "브랜드", "differentiation"],
    },
    {
        "id": "traction",
        "label": "검증/성과/증빙",
        "keywords": ["검증", "성과", "매출", "고객", "계약", "MOU", "LOI", "파일럿", "실증", "지표", "전환", "traction"],
    },
    {
        "id": "business_model",
        "label": "수익모델과 사업화",
        "keywords": ["수익", "BM", "비즈니스 모델", "가격", "매출", "구독", "판매", "사업화", "채널", "go-to-market", "revenue"],
    },
    {
        "id": "finance_budget",
        "label": "자금/예산/재무",
        "keywords": ["자금", "예산", "사업비", "비용", "인건비", "외주", "재료비", "마케팅비", "재무", "funding", "budget"],
    },
    {
        "id": "team",
        "label": "팀 역량",
        "keywords": ["대표", "팀", "역량", "경력", "전문성", "구성원", "채용", "파트너", "멘토", "advisor", "team"],
    },
    {
        "id": "roadmap",
        "label": "추진 일정과 마일스톤",
        "keywords": ["일정", "마일스톤", "추진", "단계", "월", "분기", "계획", "완료", "출시", "roadmap", "milestone"],
    },
    {
        "id": "impact",
        "label": "기대효과",
        "keywords": ["기대효과", "고용", "사회적", "파급", "지역", "ESG", "성과 확산", "impact", "효과"],
    },
    {
        "id": "risk",
        "label": "리스크와 보완계획",
        "keywords": ["리스크", "위험", "보완", "대응", "한계", "관리", "대안", "risk", "mitigation"],
    },
]


SECTION_UNDERSTANDING_MAP: dict[str, list[str]] = {
    "overview": ["overview", "problem", "customer", "solution", "business_model", "traction"],
    "problem": ["problem", "customer", "market", "traction"],
    "solution": ["solution", "product", "problem", "customer", "differentiation"],
    "market": ["market", "customer", "traction", "business_model"],
    "differentiation": ["differentiation", "solution", "product", "market"],
    "business_model": ["business_model", "traction", "market", "finance_budget"],
    "growth": ["roadmap", "traction", "business_model", "market"],
    "budget": ["finance_budget", "roadmap", "product", "traction"],
    "team": ["team", "roadmap", "differentiation"],
    "impact": ["impact", "traction", "market", "roadmap"],
    "risk": ["risk", "roadmap", "finance_budget", "market"],
}


def document_extraction_completeness(
    filename: str,
    document_type: str,
    text: str,
    notes: list[str],
    ocr_status: dict[str, Any],
) -> dict[str, Any]:
    length = len(clean_text(text))
    ext = Path(filename or "").suffix.lower()
    if ocr_status.get("status") == "needs_ocr" or (ext == ".hwp" and not length):
        return {
            "status": "blocked",
            "score": 0,
            "message": "원문 텍스트를 충분히 읽지 못했습니다. 스캔본 OCR 또는 원문 텍스트 붙여넣기가 필요합니다.",
            "requiresReview": True,
        }
    complete_threshold = 1500 if document_type == "existing_business_plan" else 350
    if length >= complete_threshold:
        return {
            "status": "complete",
            "score": 100,
            "message": "추출 가능한 텍스트 전체를 보존하고 사업계획서 작성 근거로 사용할 수 있습니다.",
            "requiresReview": False,
        }
    if length >= 120:
        return {
            "status": "partial",
            "score": 62,
            "message": "핵심 텍스트는 추출됐지만 원문 전체성 확인이 필요합니다. 중요한 표/이미지는 추가 텍스트 입력을 권장합니다.",
            "requiresReview": True,
        }
    failed = any("실패" in note or "failed" in note.lower() for note in notes)
    return {
        "status": "weak" if not failed else "blocked",
        "score": 30 if not failed else 10,
        "message": "추출 텍스트가 짧아 사업 이해 모델의 근거로 쓰기 어렵습니다. 원문 텍스트 보강이 필요합니다.",
        "requiresReview": True,
    }


def business_candidate_segments(text: str) -> list[str]:
    normalized = clean_text(text)
    if not normalized:
        return []
    line_segments = []
    for line in normalized.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if 18 <= len(line) <= 700:
            line_segments.append(line)
    raw_blocks = re.split(r"\n\s*\n+", normalized)
    segments: list[str] = list(line_segments)
    for block in raw_blocks:
        block = re.sub(r"\s+", " ", block).strip()
        if not block:
            continue
        if 28 <= len(block) <= 700:
            segments.append(block)
            continue
        if len(block) > 700:
            sentences = re.split(r"(?<=[.!?。！？다])\s+", block)
            window: list[str] = []
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                window.append(sentence)
                joined = " ".join(window)
                if len(joined) >= 180:
                    segments.append(joined[:700])
                    window = []
            if window:
                joined = " ".join(window).strip()
                if len(joined) >= 28:
                    segments.append(joined[:700])
    for line in evidence_candidate_lines(text):
        if line not in segments:
            segments.append(line)
    deduped: list[str] = []
    seen: set[str] = set()
    for segment in segments:
        marker = re.sub(r"\W+", "", segment.lower())[:120]
        if not marker or marker in seen:
            continue
        seen.add(marker)
        deduped.append(segment)
        if len(deduped) >= 1400:
            break
    return deduped


def business_segment_score(segment: str, area: dict[str, Any]) -> int:
    compact = segment.lower()
    score = 0
    for keyword in area.get("keywords", []):
        if keyword.lower() in compact:
            score += 12
    if re.search(r"\d", segment):
        score += 6
    if re.search(r"\d+(?:\.\d+)?\s*(?:%|명|건|개|원|만원|억원|회|월|년|MOU|LOI)", segment, re.I):
        score += 10
    if any(token in compact for token in ["검증", "고객", "매출", "계약", "특허", "파일럿", "실증", "예산", "일정"]):
        score += 6
    if 80 <= len(segment) <= 420:
        score += 4
    return score


def add_ranked_business_evidence(
    bucket: list[dict[str, Any]],
    source_doc: dict[str, Any],
    area: dict[str, Any],
    segment: str,
    score: int,
) -> None:
    bucket.append(
        {
            "area": area["id"],
            "areaLabel": area["label"],
            "sourceDocumentId": source_doc.get("id", ""),
            "source": source_doc.get("filename", ""),
            "documentType": source_doc.get("documentType", ""),
            "text": segment[:700],
            "score": min(100, score),
        }
    )


def dedupe_ranked_evidence(items: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    items = sorted(items, key=lambda item: item.get("score", 0), reverse=True)
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for item in items:
        marker = re.sub(r"\W+", "", item.get("text", "").lower())[:110]
        if not marker or marker in seen:
            continue
        seen.add(marker)
        output.append(item)
        if len(output) >= limit:
            break
    return output


def synthesize_business_area(area: dict[str, Any], evidence: list[dict[str, Any]]) -> str:
    if not evidence:
        return ""
    fragments = [clean_text(item.get("text", "")) for item in evidence[:3] if clean_text(item.get("text", ""))]
    if not fragments:
        return ""
    joined = " ".join(fragments)
    return joined[:900]


def business_source_documents(analyzed_docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique_docs = [doc for doc in analyzed_docs if not doc.get("duplicateOf") and clean_text(doc.get("_fullText", ""))]
    plan_docs = [doc for doc in unique_docs if doc.get("documentType") == "existing_business_plan"]
    if plan_docs:
        return sorted(plan_docs, key=lambda doc: doc.get("extractedCharacters", 0), reverse=True)
    return sorted(unique_docs, key=lambda doc: doc.get("relevanceScore", 0), reverse=True)[:8]


def build_business_plan_corpus(analyzed_docs: list[dict[str, Any]]) -> dict[str, Any]:
    source_docs = business_source_documents(analyzed_docs)
    documents: list[dict[str, Any]] = []
    retained_total = 0
    total_source = 0
    for doc in source_docs:
        text = clean_text(doc.get("_fullText", ""))
        if not text:
            continue
        per_doc_limit = 90000 if doc.get("documentType") == "existing_business_plan" else 30000
        remaining = max(0, 260000 - retained_total)
        if remaining <= 0:
            break
        retained = text[: min(per_doc_limit, remaining)]
        total_source += len(text)
        retained_total += len(retained)
        documents.append(
            {
                "documentId": doc.get("id", ""),
                "filename": doc.get("filename", ""),
                "documentType": doc.get("documentType", ""),
                "documentTypeLabel": doc.get("documentTypeLabel", ""),
                "sourceCharacters": len(text),
                "retainedCharacters": len(retained),
                "truncated": len(retained) < len(text),
                "text": retained,
            }
        )
    return {
        "documents": documents,
        "sourceDocumentCount": len(source_docs),
        "totalSourceCharacters": total_source,
        "retainedCharacters": retained_total,
        "retentionPolicy": "기존 사업계획서는 원문 텍스트를 우선 보존하고, AI 입력 한도를 넘는 경우에도 앞부분 원문과 사업 이해 근거은행을 함께 제공합니다.",
    }


def build_business_understanding(analyzed_docs: list[dict[str, Any]], notes: str = "") -> dict[str, Any]:
    source_docs = business_source_documents(analyzed_docs)
    source_meta = [
        {
            "documentId": doc.get("id", ""),
            "filename": doc.get("filename", ""),
            "documentType": doc.get("documentType", ""),
            "characters": doc.get("extractedCharacters", 0),
            "completeness": doc.get("extractionCompleteness", {}),
        }
        for doc in source_docs
    ]
    coverage: list[dict[str, Any]] = []
    knowledge: dict[str, Any] = {}
    evidence_bank: list[dict[str, Any]] = []
    for area in BUSINESS_UNDERSTANDING_AREAS:
        candidates: list[dict[str, Any]] = []
        for doc in source_docs:
            for segment in business_candidate_segments(doc.get("_fullText", "")):
                score = business_segment_score(segment, area)
                if score >= 14:
                    add_ranked_business_evidence(candidates, doc, area, segment, score)
        area_evidence = dedupe_ranked_evidence(candidates, 8)
        max_score = area_evidence[0].get("score", 0) if area_evidence else 0
        confidence = min(100, max_score + len(area_evidence) * 6)
        if len(area_evidence) >= 4 and confidence >= 62:
            status = "strong"
        elif area_evidence:
            status = "partial"
        else:
            status = "missing"
        synthesized = synthesize_business_area(area, area_evidence)
        coverage.append(
            {
                "id": area["id"],
                "label": area["label"],
                "status": status,
                "confidence": confidence,
                "evidenceCount": len(area_evidence),
                "sourceDocuments": sorted({item.get("source", "") for item in area_evidence if item.get("source")}),
            }
        )
        knowledge[area["id"]] = {
            "id": area["id"],
            "label": area["label"],
            "status": status,
            "confidence": confidence,
            "synthesized": synthesized,
            "evidence": area_evidence[:5],
        }
        evidence_bank.extend(area_evidence[:3])

    evidence_bank = dedupe_ranked_evidence(evidence_bank, 32)
    complete_docs = [doc for doc in source_docs if doc.get("extractionCompleteness", {}).get("status") == "complete"]
    partial_docs = [doc for doc in source_docs if doc.get("extractionCompleteness", {}).get("status") in {"partial", "weak"}]
    blocked_docs = [doc for doc in source_docs if doc.get("extractionCompleteness", {}).get("status") == "blocked"]
    missing = [item["label"] for item in coverage if item["status"] == "missing"]
    directives = [
        "기존 사업계획서의 원문 표현을 단순 요약하지 말고, 문제-고객-해결-시장-사업화-예산-일정의 논리 구조로 재배치합니다.",
        "근거가 있는 수치, 고객 반응, 계약/검증, 예산 항목은 새 양식의 해당 문항에 직접 연결합니다.",
        "원문에서 확인되지 않는 수치나 성과는 생성하지 않고 보완 필요 항목으로 남깁니다.",
    ]
    if notes.strip():
        directives.append("사용자 추가 의견도 기존 사업계획서 이해 모델과 함께 반영합니다.")
    return {
        "sourceDocuments": source_meta,
        "coverage": coverage,
        "knowledge": knowledge,
        "evidenceBank": evidence_bank,
        "extractionCompleteness": {
            "sourceDocumentCount": len(source_docs),
            "completeDocuments": len(complete_docs),
            "partialDocuments": len(partial_docs),
            "blockedDocuments": len(blocked_docs),
            "totalExtractedCharacters": sum(doc.get("extractedCharacters", 0) for doc in source_docs),
            "warnings": [
                f"{doc.get('filename', '')}: {doc.get('extractionCompleteness', {}).get('message', '')}"
                for doc in partial_docs + blocked_docs
            ][:8],
        },
        "writingDirectives": directives,
        "missingCriticalDetails": missing[:8],
    }


def build_business_understanding_patch(understanding: dict[str, Any]) -> dict[str, Any]:
    mapping = {
        "overview": ("business", "oneLine"),
        "problem": ("business", "problem"),
        "customer": ("business", "targetCustomer"),
        "solution": ("business", "solution"),
        "product": ("business", "product"),
        "market": ("market", "marketSize"),
        "differentiation": ("business", "differentiation"),
        "traction": ("traction", "metrics"),
        "business_model": ("business", "revenueModel"),
        "finance_budget": ("finance", "useOfFunds"),
        "team": ("team", "members"),
        "roadmap": ("finance", "milestones"),
        "impact": ("impact", "socialValue"),
        "risk": ("knowledge", "riskNotes"),
    }
    patch: dict[str, Any] = {}
    knowledge = understanding.get("knowledge") or {}
    for area_id, (group, key) in mapping.items():
        synthesized = clean_text((knowledge.get(area_id) or {}).get("synthesized", ""))
        if not synthesized:
            continue
        patch.setdefault(group, {})[key] = compact_value(synthesized)
    return patch


def business_understanding_summary_for_context(understanding: dict[str, Any]) -> str:
    lines: list[str] = []
    for item in understanding.get("coverage", []):
        if item.get("status") == "missing":
            continue
        area = (understanding.get("knowledge") or {}).get(item.get("id"), {})
        synthesized = clean_text(area.get("synthesized", ""))
        if synthesized:
            lines.append(f"- {item.get('label')}: {synthesized[:420]}")
    if understanding.get("missingCriticalDetails"):
        lines.append("보완 필요: " + ", ".join(understanding.get("missingCriticalDetails", [])[:6]))
    return "\n".join(lines[:18])


def public_document(doc: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in doc.items() if not key.startswith("_")}


def document_insights_for_ai(document_insights: dict[str, Any]) -> dict[str, Any]:
    if not document_insights:
        return {}
    documents = []
    for doc in document_insights.get("documents", [])[:12]:
        documents.append(
            {
                "id": doc.get("id", ""),
                "filename": doc.get("filename", ""),
                "documentType": doc.get("documentType", ""),
                "documentTypeLabel": doc.get("documentTypeLabel", ""),
                "extractedCharacters": doc.get("extractedCharacters", 0),
                "extractionCompleteness": doc.get("extractionCompleteness", {}),
                "summary": doc.get("summary", ""),
                "facts": doc.get("facts", [])[:8],
                "coverageTags": doc.get("coverageTags", [])[:6],
                "evidenceSnippets": doc.get("evidenceSnippets", [])[:8],
                "recommendedUse": doc.get("recommendedUse", ""),
            }
        )
    return {
        "businessUnderstanding": document_insights.get("businessUnderstanding") or {},
        "businessPlanCorpus": document_insights.get("businessPlanCorpus") or {},
        "combinedText": document_insights.get("combinedText", ""),
        "companyPatch": document_insights.get("companyPatch") or {},
        "facts": document_insights.get("facts", [])[:30],
        "librarySummary": document_insights.get("librarySummary") or {},
        "documents": documents,
        "additionalNotes": document_insights.get("additionalNotes", ""),
    }


def merge_patch(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(base, ensure_ascii=False))
    for group, values in patch.items():
        if not isinstance(values, dict):
            continue
        merged.setdefault(group, {})
        for key, value_text in values.items():
            if value_text and not str(merged[group].get(key, "")).strip():
                merged[group][key] = value_text
    return merged


def analyze_documents(documents: list[dict[str, Any]], notes: str = "") -> dict[str, Any]:
    analyzed_docs: list[dict[str, Any]] = []
    all_facts: list[dict[str, str]] = []
    company_patch: dict[str, Any] = {}
    seen_signatures: dict[str, str] = {}

    for index, item in enumerate(documents, start=1):
        filename = item.get("filename") or f"document-{index}.txt"
        raw = base64.b64decode(item.get("contentBase64", "") or b"")
        text, extraction_notes = extract_text(filename, raw, item.get("text", ""))
        document_type = item.get("documentType") or infer_document_type(filename, text)
        facts, patch = extract_document_facts(text, document_type)
        company_patch = merge_patch(company_patch, patch)
        all_facts.extend(facts)
        ocr_status = build_ocr_status(filename, text, extraction_notes)
        signature = content_signature(raw, text)
        duplicate_of = seen_signatures.get(signature, "") if signature else ""
        if signature and not duplicate_of:
            seen_signatures[signature] = filename
        evidence_snippets = build_evidence_snippets(text, document_type)
        coverage_tags = build_coverage_tags(text, facts, evidence_snippets, document_type)
        extraction_quality = document_extraction_quality(text, extraction_notes, ocr_status)
        extraction_completeness = document_extraction_completeness(filename, document_type, text, extraction_notes, ocr_status)
        relevance_score = document_relevance_score(document_type, text, facts, evidence_snippets, coverage_tags)
        priority = document_priority(relevance_score, extraction_quality, duplicate_of)
        analyzed_docs.append(
            {
                "id": f"d{index}",
                "filename": filename,
                "documentType": document_type,
                "documentTypeLabel": document_type_label(document_type),
                "sha1": signature,
                "byteSize": len(raw),
                "duplicateOf": duplicate_of,
                "extractedCharacters": len(text),
                "summary": document_summary(text, document_type),
                "facts": facts,
                "notes": extraction_notes,
                "ocrStatus": ocr_status,
                "extractionQuality": extraction_quality,
                "extractionCompleteness": extraction_completeness,
                "relevanceScore": relevance_score,
                "priority": priority,
                "coverageTags": coverage_tags,
                "evidenceSnippets": evidence_snippets,
                "recommendedUse": recommended_document_use(document_type, coverage_tags, relevance_score),
                "fullTextRetained": bool(text),
                "fullTextCharacters": len(text),
                "preview": text[:1200],
                "_fullText": text,
            }
        )

    combined_text_parts: list[str] = []
    if notes.strip():
        combined_text_parts.append(f"[추가 의견]\n{notes.strip()}")
        company_patch = merge_patch(company_patch, {"knowledge": {"additionalNotes": notes.strip()}})

    seen_fact_keys: set[tuple[str, str]] = set()
    unique_facts: list[dict[str, str]] = []
    for fact in all_facts:
        marker = (fact.get("key", ""), fact.get("value", ""))
        if marker in seen_fact_keys:
            continue
        seen_fact_keys.add(marker)
        unique_facts.append(fact)

    business_understanding = build_business_understanding(analyzed_docs, notes)
    if business_understanding.get("knowledge"):
        company_patch = merge_patch(company_patch, build_business_understanding_patch(business_understanding))
    business_plan_corpus = build_business_plan_corpus(analyzed_docs)
    library_summary = build_document_library_summary(analyzed_docs, unique_facts)
    combined_text_parts = []
    understanding_text = business_understanding_summary_for_context(business_understanding)
    if understanding_text:
        combined_text_parts.append("[기존 사업계획서 심층 이해 모델]\n" + understanding_text)
    ranked_docs = sorted(
        [doc for doc in analyzed_docs if not doc.get("duplicateOf")],
        key=lambda doc: (doc.get("relevanceScore", 0), len(doc.get("facts", [])), doc.get("extractedCharacters", 0)),
        reverse=True,
    )
    for doc in ranked_docs[:14]:
        snippets = "\n".join(f"- {snippet.get('categoryLabel')}: {snippet.get('text')}" for snippet in doc.get("evidenceSnippets", [])[:5])
        facts_text = "\n".join(f"- {fact.get('label')}: {fact.get('value')}" for fact in doc.get("facts", [])[:8])
        combined_text_parts.append(
            "\n".join(
                part
                for part in [
                    f"[{doc.get('priority', '').upper()} {doc.get('relevanceScore', 0)}점 | {doc.get('documentTypeLabel')}: {doc.get('filename')}]",
                    f"요약: {doc.get('summary', '')}",
                    f"추천 활용: {doc.get('recommendedUse', '')}",
                    f"핵심 증빙:\n{snippets}" if snippets else "",
                    f"추출 사실:\n{facts_text}" if facts_text else "",
                    f"원문 미리보기:\n{doc.get('preview', '')[:1800]}" if doc.get("preview") else "",
                ]
                if part
            )
        )
    if notes.strip():
        combined_text_parts.append(f"[추가 의견]\n{notes.strip()}")

    return {
        "businessUnderstanding": business_understanding,
        "businessPlanCorpus": business_plan_corpus,
        "documents": [public_document(doc) for doc in analyzed_docs],
        "facts": unique_facts,
        "companyPatch": company_patch,
        "librarySummary": library_summary,
        "additionalNotes": notes.strip(),
        "combinedText": "\n\n".join(combined_text_parts)[:40000],
        "analyzedAt": dt.datetime.now().isoformat(timespec="seconds"),
    }


def infer_category(text: str) -> tuple[str, str]:
    compact = text.lower()
    for category, keywords, focus in CATEGORY_RULES:
        if any(keyword.lower() in compact for keyword in keywords):
            return category, focus
    return "overview", "사업의 핵심 가설, 지원 필요성, 실행 가능성을 짧고 명확하게 연결하세요."


def normalize_prompt(line: str) -> str:
    line = re.sub(r"^\s*(\d+[\.\)]|[가-힣][\.\)]|[IVX]+[\.\)]|[○●□■\-])\s*", "", line, flags=re.I)
    line = re.sub(r"\s+", " ", line)
    return line.strip(" :;-")


def important_line(line: str) -> bool:
    if len(line) < 4 or len(line) > 150:
        return False
    if re.fullmatch(r"\d+|[-_= ]+", line):
        return False
    if re.search(r"\d+\s*(쪽|페이지|page|pages)", line, re.I) and any(keyword in line for keyword in ["이내", "내외", "분량", "작성", "제출"]):
        structural_keywords = ["사업 개요", "시장성", "제품", "서비스", "자금", "팀", "기대효과", "추진", "수익모델"]
        if not any(keyword in line for keyword in structural_keywords):
            return False
    if re.search(r"(쪽|page)\s*\d*$", line, re.I):
        return False
    heading = re.match(r"^\s*(\d+[\.\)]|[가-힣][\.\)]|[IVX]+[\.\)]|[○●□■])\s+", line, re.I)
    keywords = [
        "작성",
        "기재",
        "사업",
        "제품",
        "서비스",
        "시장",
        "경쟁",
        "고객",
        "매출",
        "자금",
        "예산",
        "추진",
        "역량",
        "팀",
        "성과",
        "효과",
        "계획",
        "필요",
        "내용",
        "차별",
    ]
    return bool(heading) or any(keyword in line for keyword in keywords) or line.endswith("?")


def analyze_template(filename: str, text: str, notes: list[str], template_source: dict[str, Any] | None = None) -> dict[str, Any]:
    lines = [line.strip() for line in clean_text(text).splitlines() if line.strip()]
    title = next((line for line in lines[:20] if "사업계획" in line or "신청" in line or "계획서" in line), "")
    if not title:
        title = Path(filename).stem if filename else "정부지원사업 사업계획서"

    questions: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line in lines:
        if line == title:
            continue
        if not important_line(line):
            continue
        prompt = normalize_prompt(line)
        if len(prompt) < 4:
            continue
        key = re.sub(r"\W+", "", prompt.lower())
        if key in seen:
            continue
        seen.add(key)
        category, focus = infer_category(prompt)
        questions.append(
            {
                "id": f"q{len(questions) + 1}",
                "prompt": prompt,
                "category": category,
                "evaluationFocus": focus,
                "answerStrategy": answer_strategy(category),
            }
        )
        if len(questions) >= 18:
            break

    if not questions:
        for prompt, category in DEFAULT_SECTIONS:
            _, focus = infer_category(prompt)
            questions.append(
                {
                    "id": f"q{len(questions) + 1}",
                    "prompt": prompt,
                    "category": category,
                    "evaluationFocus": focus,
                    "answerStrategy": answer_strategy(category),
                }
            )
        notes.append("양식 문항을 충분히 찾지 못해 표준 사업계획서 구조를 적용했습니다.")

    checklist = [
        line
        for line in lines
        if len(line) <= 130
        and (
            line.startswith(("※", "*", "-"))
            or "분량" in line
            or "이내" in line
            or "필수" in line
            or "유의" in line
            or "제외" in line
        )
    ][:12]

    keywords = extract_keywords(lines)
    requirements = extract_template_requirements(lines)
    success_criteria = match_success_criteria(title, text)
    return {
        "sourceFilename": filename,
        "title": title,
        "extractedCharacters": len(text),
        "questions": questions,
        "checklist": checklist,
        "requirements": requirements,
        "keywords": keywords,
        "successCriteria": success_criteria,
        "templateSource": template_source or {"mode": "none", "preservable": False},
        "notes": notes,
        "preview": "\n".join(lines[:30]),
        "analyzedAt": dt.datetime.now().isoformat(timespec="seconds"),
    }


def extract_keywords(lines: list[str]) -> list[str]:
    joined = " ".join(lines)
    terms = [
        "초격차",
        "창업",
        "사업화",
        "청년",
        "예비창업",
        "초기창업",
        "지역",
        "R&D",
        "디지털",
        "AI",
        "ESG",
        "고용",
        "수출",
        "매출",
        "투자",
        "혁신",
        "실증",
        "바우처",
    ]
    found = [term for term in terms if term.lower() in joined.lower()]
    return found[:10]


def extract_template_requirements(lines: list[str]) -> list[dict[str, str]]:
    requirements: list[dict[str, str]] = []
    joined = "\n".join(lines)
    page_matches = re.findall(r"(\d+)\s*(쪽|페이지|page|pages)\s*(이내|내외|이상|분량|까지)?", joined, flags=re.I)
    for number, unit, qualifier in page_matches[:4]:
        requirements.append(
            {
                "type": "page_limit",
                "label": "분량 제한",
                "value": f"{number}{unit} {qualifier}".strip(),
                "source": "양식 자동 감지",
            }
        )
    for line in lines:
        if len(line) > 160:
            continue
        if any(keyword in line for keyword in ["글자", "포인트", "pt", "장평", "줄간격", "여백", "표준양식", "양식 변경", "삭제 금지", "서식", "제출", "분량", "이내"]):
            requirements.append(
                {
                    "type": "format_note",
                    "label": "제출 형식",
                    "value": line,
                    "source": "양식 자동 감지",
                }
            )
        if len(requirements) >= 12:
            break
    return requirements


def parse_guidance_lines(text: str, limit: int = 12) -> list[str]:
    lines: list[str] = []
    for raw in clean_text(text or "").splitlines():
        line = normalize_prompt(raw)
        if len(line) >= 2:
            lines.append(line[:180])
        if len(lines) >= limit:
            break
    return lines


def normalize_template_guidance(guidance: dict[str, Any] | None) -> dict[str, Any]:
    guidance = guidance or {}
    page_count_raw = str(guidance.get("pageCount") or "").strip()
    page_count = ""
    if page_count_raw:
        match = re.search(r"\d+", page_count_raw)
        page_count = match.group(0) if match else page_count_raw
    return {
        "pageCount": page_count,
        "structure": clean_text(str(guidance.get("structure") or "")),
        "structureLines": parse_guidance_lines(str(guidance.get("structure") or "")),
        "focusPoints": clean_text(str(guidance.get("focusPoints") or "")),
        "formatRules": clean_text(str(guidance.get("formatRules") or "")),
        "comments": clean_text(str(guidance.get("comments") or "")),
        "strictFormat": bool(guidance.get("strictFormat")),
    }


def answer_strategy(category: str) -> str:
    strategies = {
        "overview": "한 문단 안에 고객, 문제, 솔루션, 수익모델, 지원금 사용처를 압축합니다.",
        "problem": "고객군별 불편, 기존 대안의 한계, 지금 해결해야 하는 이유 순서로 씁니다.",
        "solution": "핵심 기능과 사용 흐름을 먼저 쓰고, 구현 단계와 검증 계획을 붙입니다.",
        "market": "좁은 초기 시장에서 시작해 확장 시장으로 넘어가는 논리를 만듭니다.",
        "differentiation": "경쟁 비교표 관점으로 기술·운영·데이터·브랜드 우위를 나눕니다.",
        "business_model": "가격, 판매 채널, 첫 고객 확보, 반복 매출 구조를 연결합니다.",
        "growth": "지원기간 내 산출물, 6개월, 12개월 목표를 정량화합니다.",
        "budget": "인건비, 외주, 마케팅, 인증, 장비 등 항목별 산출 근거를 씁니다.",
        "team": "대표 경험과 팀의 보완 역량을 사업 성공요인에 직접 연결합니다.",
        "impact": "고용, 매출, 고객 편익, 지역·사회적 파급효과를 수치 중심으로 씁니다.",
        "risk": "가장 큰 리스크 3개와 검증 실험, 대안 경로를 제시합니다.",
    }
    return strategies.get(category, strategies["overview"])


def value(company: dict[str, Any], path: str, fallback: str = "") -> str:
    node: Any = company
    for part in path.split("."):
        if not isinstance(node, dict):
            return fallback
        node = node.get(part)
    if node is None:
        return fallback
    text = str(node).strip()
    return text or fallback


def sentence_text(text: str) -> str:
    text = clean_text(str(text or ""))
    return text.rstrip(" .。")


def sentence_clause(text: str) -> str:
    text = sentence_text(text)
    if not text:
        return ""
    if text.endswith(("다", "요", "음", "함")):
        return text + "."
    return text + "입니다."


def has_final_consonant(text: str) -> bool:
    for char in reversed(clean_text(text)):
        code = ord(char)
        if 0xAC00 <= code <= 0xD7A3:
            return (code - 0xAC00) % 28 != 0
    return False


def object_josa(text: str) -> str:
    return "을" if has_final_consonant(text) else "를"


def topic_josa(text: str) -> str:
    return "은" if has_final_consonant(text) else "는"


def subject_josa(text: str) -> str:
    return "이" if has_final_consonant(text) else "가"


def direction_josa(text: str) -> str:
    for char in reversed(clean_text(text)):
        code = ord(char)
        if 0xAC00 <= code <= 0xD7A3:
            jong = (code - 0xAC00) % 28
            return "로" if jong in (0, 8) else "으로"
    return "로"


def has_page_limit_within(template: dict[str, Any], guidance: dict[str, Any]) -> bool:
    format_blob = " ".join(
        [
            str(guidance.get("formatRules") or ""),
            " ".join(str(item.get("value", "")) for item in template.get("requirements", [])),
        ]
    )
    return any(keyword in format_blob for keyword in ["이내", "까지", "초과 금지", "분량 제한"])


def missing_fields(company: dict[str, Any], category: str) -> list[str]:
    fields = {
        "overview": ["business.oneLine", "business.targetCustomer", "business.product"],
        "problem": ["business.problem", "business.targetCustomer"],
        "solution": ["business.solution", "business.product", "business.stage"],
        "market": ["market.marketSize", "market.trend", "market.goToMarket"],
        "differentiation": ["business.differentiation", "market.competitors"],
        "business_model": ["business.revenueModel", "finance.salesPlan"],
        "growth": ["finance.milestones", "traction.metrics"],
        "budget": ["finance.fundingNeed", "finance.useOfFunds"],
        "team": ["team.founder", "team.members"],
        "impact": ["impact.jobCreation", "impact.socialValue"],
        "risk": ["finance.milestones", "market.competitors"],
    }.get(category, [])
    return [field for field in fields if not value(company, field)]


def generate_plan(company: dict[str, Any], template: dict[str, Any], options: dict[str, Any]) -> dict[str, Any]:
    questions = template.get("questions") or [
        {
            "id": f"q{i + 1}",
            "prompt": prompt,
            "category": category,
            "evaluationFocus": infer_category(prompt)[1],
            "answerStrategy": answer_strategy(category),
        }
        for i, (prompt, category) in enumerate(DEFAULT_SECTIONS)
    ]
    grant_name = options.get("grantName") or template.get("title") or "정부지원사업"
    tone = options.get("tone") or "심사위원 설득형"
    length = options.get("length") or "balanced"
    document_insights = options.get("documentInsights") or {}
    additional_notes = options.get("additionalNotes") or value(company, "knowledge.additionalNotes", "")
    template_guidance = normalize_template_guidance(options.get("templateGuidance") or {})
    if document_insights.get("companyPatch"):
        company = merge_patch(company, document_insights.get("companyPatch") or {})
    company_name = value(company, "basic.name", "회사")

    sections: list[dict[str, Any]] = []
    for index, question in enumerate(questions, start=1):
        category = question.get("category") or infer_category(question.get("prompt", ""))[0]
        planned_role = ""
        if index <= len(template_guidance.get("structureLines") or []):
            planned_role = template_guidance["structureLines"][index - 1]
        body = section_body(
            company,
            category,
            question.get("prompt", ""),
            length,
            document_insights,
            additional_notes,
            template_guidance,
            planned_role,
        )
        missing = missing_fields(company, category)
        if missing:
            body += "\n\n보완 필요: " + ", ".join(label_for_field(field) for field in missing) + " 정보를 입력하면 문항 설득력이 올라갑니다."
        evidence = evidence_needed(category)
        strategy = question.get("answerStrategy") or answer_strategy(category)
        if planned_role:
            strategy += f" 구성상 역할: {planned_role}"
        if template_guidance.get("focusPoints"):
            strategy += f" 중점 포인트: {template_guidance['focusPoints'][:220]}"
        sections.append(
            {
                "id": question.get("id") or f"q{index}",
                "heading": question.get("prompt") or f"{index}. 사업계획 항목",
                "category": category,
                "evaluationFocus": question.get("evaluationFocus") or infer_category(question.get("prompt", ""))[1],
                "answerStrategy": strategy,
                "content": body,
                "evidenceNeeded": evidence,
                "missingFields": missing,
                "plannedRole": planned_role,
            }
        )

    sections = expand_sections_for_page_target(sections, company, template_guidance, template)
    format_validation = validate_plan_format(sections, template, template_guidance)
    proposal_scorecard = evaluate_proposal_strength(company, sections, document_insights, format_validation)
    quality = quality_checks(company, sections, document_insights, format_validation)
    visual_assets = build_visual_assets(company, sections, template_guidance, proposal_scorecard)
    success_criteria = template.get("successCriteria") or match_success_criteria(grant_name, json.dumps(template, ensure_ascii=False))
    submission_format_manifest = build_submission_format_manifest(
        sections,
        template,
        template_guidance,
        format_validation,
        visual_assets,
    )
    quality.append(
        {
            "label": "표·인포그래픽 구성",
            "status": "ok",
            "message": f"표 {len(visual_assets.get('tables', []))}개, 인포그래픽 {len(visual_assets.get('infographics', []))}개, 이미지 브리프 {len(visual_assets.get('imageBriefs', []))}개를 초안과 내보내기에 배치합니다.",
        }
    )
    quality.append(
        {
            "label": "지원사업 합격 기준",
            "status": "ok",
            "message": f"{success_criteria.get('name', '일반 지원사업')} 유형의 선정 포인트와 탈락 리스크를 초안 검토 기준으로 연결했습니다.",
        }
    )
    summary = build_summary(company, grant_name, document_insights, additional_notes, template_guidance)
    plan = {
        "title": f"{company_name} {grant_name} 사업계획서 초안",
        "companyName": company_name,
        "grantName": grant_name,
        "tone": tone,
        "summary": summary,
        "sections": sections,
        "qualityChecks": quality,
        "proposalScorecard": proposal_scorecard,
        "formatValidation": format_validation,
        "submissionFormatManifest": submission_format_manifest,
        "templateSource": template.get("templateSource") or {"mode": "none", "preservable": False},
        "successCriteria": success_criteria,
        "visualAssets": visual_assets,
        "templateGuidance": template_guidance,
        "documentInsights": document_insights,
        "businessUnderstanding": document_insights.get("businessUnderstanding") or {},
        "additionalNotes": additional_notes,
        "aiEngine": build_ai_engine_report("local_fallback", "외부 AI API 키가 없어 로컬 생성기를 사용했습니다."),
        "generatedAt": dt.datetime.now().isoformat(timespec="seconds"),
    }
    if options.get("useAI", True):
        plan = enhance_plan_with_ai(plan, company, template, options)
    return attach_grounding_audit(plan, document_insights)


def build_ai_engine_report(mode: str, message: str, error: str = "") -> dict[str, Any]:
    providers = provider_status()
    return {
        "provider": AI_MODEL_ASSIGNMENTS["provider"],
        "api": AI_MODEL_ASSIGNMENTS["api"],
        "mode": mode,
        "apiKeyConfigured": any(item["configured"] for item in providers.values()),
        "providerStatuses": providers,
        "draftModel": AI_MODEL_ASSIGNMENTS["primaryDraft"]["model"],
        "analysisModel": AI_MODEL_ASSIGNMENTS["documentAnalysis"]["model"],
        "polishModel": AI_MODEL_ASSIGNMENTS["finalPolish"]["model"],
        "reviewModel": AI_MODEL_ASSIGNMENTS["formatReview"]["model"],
        "redTeamModel": AI_MODEL_ASSIGNMENTS["strategicRedTeam"]["model"],
        "imageModel": AI_MODEL_ASSIGNMENTS["visualPlanning"]["imageModel"],
        "reasoningEffort": AI_MODEL_ASSIGNMENTS["primaryDraft"]["reasoningEffort"],
        "message": message,
        "error": error[:500] if error else "",
        "assignments": ai_settings_payload()["assignments"],
    }


def openai_response_text(response: dict[str, Any]) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"]
    parts: list[str] = []
    for item in response.get("output", []) or []:
        for content in item.get("content", []) or []:
            if isinstance(content.get("text"), str):
                parts.append(content["text"])
            elif isinstance(content.get("output_text"), str):
                parts.append(content["output_text"])
    return "\n".join(parts).strip()


def openai_responses_create(payload: dict[str, Any], timeout: int = 90) -> dict[str, Any]:
    key = openai_api_key()
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"OpenAI API HTTP {exc.code}: {detail}") from exc


def gemini_generate_content(model: str, prompt: str, schema: dict[str, Any] | None = None, timeout: int = 90) -> dict[str, Any]:
    key = gemini_api_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY is not configured")
    payload: dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.35,
            "responseMimeType": "application/json",
        },
    }
    if schema:
        payload["generationConfig"]["responseSchema"] = schema
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    encoded_model = urllib.parse.quote(model, safe="")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{encoded_model}:generateContent?key={urllib.parse.quote(key)}"
    request = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"Gemini API HTTP {exc.code}: {detail}") from exc


def gemini_response_text(response: dict[str, Any]) -> str:
    parts: list[str] = []
    for candidate in response.get("candidates", []) or []:
        content = candidate.get("content") or {}
        for part in content.get("parts", []) or []:
            if isinstance(part.get("text"), str):
                parts.append(part["text"])
    return "\n".join(parts).strip()


def anthropic_messages_create(payload: dict[str, Any], timeout: int = 90) -> dict[str, Any]:
    key = anthropic_api_key()
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        method="POST",
        headers={
            "x-api-key": key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"Claude API HTTP {exc.code}: {detail}") from exc


def anthropic_response_text(response: dict[str, Any]) -> str:
    parts: list[str] = []
    for item in response.get("content", []) or []:
        if item.get("type") == "text" and isinstance(item.get("text"), str):
            parts.append(item["text"])
    return "\n".join(parts).strip()


def ai_plan_schema() -> dict[str, Any]:
    section_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["id", "heading", "evaluationFocus", "answerStrategy", "content"],
        "properties": {
            "id": {"type": "string", "description": "초안 섹션 ID. 입력된 id를 유지합니다."},
            "heading": {"type": "string", "description": "양식 원문 문항명 또는 섹션 제목"},
            "evaluationFocus": {"type": "string", "description": "심사위원이 확인할 평가 포인트"},
            "answerStrategy": {"type": "string", "description": "해당 문항을 설득력 있게 쓰는 전략"},
            "content": {"type": "string", "description": "한국어 사업계획서 본문. 제출 문체로 작성합니다."},
        },
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["summary", "sections", "qualityNotes"],
        "properties": {
            "summary": {"type": "string", "description": "초안 전체를 요약하는 제출용 한국어 문단"},
            "sections": {"type": "array", "items": section_schema},
            "qualityNotes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "최종 제출 전 보완할 핵심 사항",
            },
        },
    }


def compact_for_ai(payload: Any, limit: int = 48000) -> str:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...TRUNCATED_FOR_CONTEXT..."


def parse_json_object(text: str) -> dict[str, Any]:
    text = clean_text(text)
    if not text:
        raise RuntimeError("AI response was empty")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise


def ai_context_payload(
    plan: dict[str, Any],
    company: dict[str, Any],
    template: dict[str, Any],
    options: dict[str, Any],
) -> dict[str, Any]:
    return {
        "company": company,
        "template": {
            "title": template.get("title", ""),
            "requirements": template.get("requirements", []),
            "questions": template.get("questions", []),
        },
        "templateGuidance": options.get("templateGuidance") or plan.get("templateGuidance") or {},
        "documentInsights": document_insights_for_ai(options.get("documentInsights") or {}),
        "additionalNotes": options.get("additionalNotes") or "",
        "currentDraft": {
            "summary": plan.get("summary", ""),
            "sections": [
                {
                    "id": section.get("id", ""),
                    "heading": section.get("heading", ""),
                    "evaluationFocus": section.get("evaluationFocus", ""),
                    "answerStrategy": section.get("answerStrategy", ""),
                    "content": section.get("content", ""),
                }
                for section in plan.get("sections", [])
            ],
        },
    }


def merge_ai_plan_output(
    plan: dict[str, Any],
    enhanced: dict[str, Any],
    company: dict[str, Any],
    quality_label: str,
) -> dict[str, Any]:
    output = json.loads(json.dumps(plan, ensure_ascii=False))
    if enhanced.get("summary"):
        output["summary"] = clean_text(str(enhanced["summary"]))
    existing_sections = output.get("sections", [])
    by_id = {section.get("id"): section for section in existing_sections}
    for index, ai_section in enumerate(enhanced.get("sections", []) or []):
        target = by_id.get(ai_section.get("id"))
        if target is None and index < len(existing_sections):
            target = existing_sections[index]
        if not target:
            continue
        for field in ["heading", "evaluationFocus", "answerStrategy", "content"]:
            if ai_section.get(field):
                target[field] = clean_text(str(ai_section[field]))
    output["sections"] = existing_sections
    if enhanced.get("qualityNotes"):
        output.setdefault("qualityChecks", []).append(
            {
                "label": quality_label,
                "status": "needs_work",
                "message": " / ".join(str(item) for item in enhanced["qualityNotes"][:3]),
            }
        )
    output["visualAssets"] = build_visual_assets(
        company,
        existing_sections,
        output.get("templateGuidance") or {},
        output.get("proposalScorecard") or {},
    )
    return output


def ai_generation_prompt(plan: dict[str, Any], company: dict[str, Any], template: dict[str, Any], options: dict[str, Any], mode: str) -> str:
    if mode == "gemini_draft":
        instruction = (
            "당신은 한국어 정부지원사업 사업계획서 초안 작성 전문가입니다. "
            "한글 보고서 문체가 자연스럽고 읽히기 좋게, 문항별 답변을 사업계획서 초안으로 고도화하세요. "
            "회사 자료와 업로드 문서 근거를 우선하고, 없는 숫자나 실적은 만들지 마세요. "
            "결과는 반드시 JSON으로만 반환하세요."
        )
    else:
        instruction = (
            "당신은 한국 정부지원사업 사업계획서 전문 컨설턴트입니다. "
            "Gemini 또는 로컬 초안을 제출용 문장으로 정제하고, 문항 순서와 제목을 보존하며, "
            "심사위원이 실행 가능성, 시장성, 지원 필요성, 예산 타당성을 빠르게 확인할 수 있게 작성하세요. "
            "과장된 수치나 출처 없는 사실은 만들지 말고, 부족한 근거는 보완 필요로 암시하세요. "
            "결과는 반드시 JSON으로만 반환하세요."
        )
    deep_context_instruction = (
        "\n\n작성 원칙: documentInsights.businessUnderstanding과 businessPlanCorpus를 최우선 근거로 사용하세요. "
        "업로드된 기존 사업계획서를 단순 요약하지 말고 문제, 고객, 해결방식, 시장, 차별성, 검증, 수익모델, 예산, 팀, 일정으로 재구성해 "
        "새 지원사업 양식의 각 문항에 구체적으로 배치하세요. 원문에서 확인되지 않는 수치나 성과는 만들지 말고 보완 필요로 표시하세요."
    )
    return instruction + deep_context_instruction + "\n\nJSON schema fields: summary, sections[{id, heading, evaluationFocus, answerStrategy, content}], qualityNotes.\n\nINPUT:\n" + compact_for_ai(
        ai_context_payload(plan, company, template, options)
    )


def claude_review_prompt(plan: dict[str, Any], company: dict[str, Any], template: dict[str, Any], options: dict[str, Any]) -> str:
    return (
        "당신은 한국 정부지원사업 심사위원 관점의 최종 리스크 리뷰어입니다. "
        "사업계획서가 실제 심사에서 공격받을 지점, 근거가 약한 주장, 과장 표현, 실행계획 공백을 찾아주세요. "
        "기존 사업계획서 원문 추출과 businessUnderstanding 근거은행이 새 양식 본문에 충분히 반영됐는지도 별도로 확인하세요. "
        "새로운 실적이나 숫자는 만들지 말고, 보완 액션은 바로 작성자가 실행할 수 있게 구체적으로 쓰세요. "
        "반드시 JSON 객체만 반환하세요. 필드: readinessScore(number 0-100), decision(string), "
        "risks(string[]), priorityActions(string[]), judgeQuestions(string[]), polishNotes(string[]).\n\nINPUT:\n"
        + compact_for_ai(ai_context_payload(plan, company, template, options), limit=62000)
    )


def merge_claude_review(
    plan: dict[str, Any],
    review: dict[str, Any],
    model: str,
) -> dict[str, Any]:
    output = json.loads(json.dumps(plan, ensure_ascii=False))
    risks = [clean_text(str(item)) for item in review.get("risks", []) if clean_text(str(item))]
    actions = [clean_text(str(item)) for item in review.get("priorityActions", []) if clean_text(str(item))]
    questions = [clean_text(str(item)) for item in review.get("judgeQuestions", []) if clean_text(str(item))]
    notes = [clean_text(str(item)) for item in review.get("polishNotes", []) if clean_text(str(item))]
    readiness_score = review.get("readinessScore")
    try:
        readiness_score = int(float(readiness_score))
    except (TypeError, ValueError):
        readiness_score = 0

    output["claudeReview"] = {
        "model": model,
        "readinessScore": readiness_score,
        "decision": clean_text(str(review.get("decision") or "")),
        "risks": risks[:6],
        "priorityActions": actions[:6],
        "judgeQuestions": questions[:6],
        "polishNotes": notes[:6],
        "reviewedAt": dt.datetime.now().isoformat(timespec="seconds"),
    }
    review_message_parts = actions[:2] or risks[:2] or notes[:2]
    output.setdefault("qualityChecks", []).append(
        {
            "label": "Claude 최종 심사 리스크 리뷰",
            "status": "ok" if readiness_score >= 85 and not risks else "needs_work",
            "message": " / ".join(review_message_parts) if review_message_parts else "심사위원 관점의 추가 보완 사항이 크지 않습니다.",
        }
    )

    scorecard = output.setdefault("proposalScorecard", {})
    existing_actions = list(scorecard.get("priorityActions") or [])
    for action in reversed(actions[:3]):
        if action and action not in existing_actions:
            existing_actions.insert(0, action)
    scorecard["priorityActions"] = existing_actions[:6]
    if readiness_score:
        scorecard["message"] = (
            f"{scorecard.get('message', '')} Claude 최종 리뷰 준비도는 {readiness_score}점이며, "
            "우선 보완 액션을 반영하면 제출 완성도를 더 높일 수 있습니다."
        ).strip()
    return output


def apply_gemini_draft(
    plan: dict[str, Any],
    company: dict[str, Any],
    template: dict[str, Any],
    options: dict[str, Any],
) -> dict[str, Any]:
    model = AI_MODEL_ASSIGNMENTS["primaryDraft"]["model"]
    prompt = ai_generation_prompt(plan, company, template, options, "gemini_draft")
    response = gemini_generate_content(model, prompt, ai_plan_schema(), timeout=120)
    enhanced = parse_json_object(gemini_response_text(response))
    return merge_ai_plan_output(plan, enhanced, company, "Gemini 3.5 초안 보완 메모")


def apply_openai_polish(
    plan: dict[str, Any],
    company: dict[str, Any],
    template: dict[str, Any],
    options: dict[str, Any],
) -> dict[str, Any]:
    model = AI_MODEL_ASSIGNMENTS["finalPolish"]["model"]
    payload = {
        "model": model,
        "store": False,
        "reasoning": {"effort": AI_MODEL_ASSIGNMENTS["finalPolish"]["reasoningEffort"]},
        "instructions": (
            "당신은 한국 정부지원사업 사업계획서 전문 컨설턴트입니다. "
            "Gemini 또는 로컬 초안을 제출용 문장으로 정제하고, 문항 순서와 제목을 보존하며, "
            "회사 프로필·업로드 문서 근거·작성 브리프를 바탕으로 "
            "심사위원이 실행 가능성, 시장성, 지원 필요성, 예산 타당성을 빠르게 확인할 수 있게 작성하세요. "
            "과장된 수치나 출처 없는 사실은 만들지 말고, 부족한 근거는 보완 필요로 암시하세요. "
            "표·인포그래픽 배치는 별도 구조화 엔진이 담당하므로 본문에는 그 근거가 되는 정확한 설명을 포함하세요."
        ),
        "input": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": ai_generation_prompt(plan, company, template, options, "openai_polish"),
                    }
                ],
            }
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "korean_grant_business_plan",
                "strict": True,
                "schema": ai_plan_schema(),
            }
        },
        "max_output_tokens": 16000,
    }
    response = openai_responses_create(payload, timeout=150)
    enhanced = parse_json_object(openai_response_text(response))
    return merge_ai_plan_output(plan, enhanced, company, "GPT-5.5 제출 정제 메모")


def apply_claude_review(
    plan: dict[str, Any],
    company: dict[str, Any],
    template: dict[str, Any],
    options: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    primary_model = AI_MODEL_ASSIGNMENTS["strategicRedTeam"]["model"]
    fallback_model = AI_MODEL_ASSIGNMENTS["strategicRedTeam"].get("fallbackModel", "")
    prompt = claude_review_prompt(plan, company, template, options)
    last_error = ""
    for model in [primary_model, fallback_model]:
        if not model:
            continue
        payload = {
            "model": model,
            "max_tokens": 4000,
            "temperature": 0.2,
            "system": "한국어 정부지원사업 사업계획서의 최종 심사 리스크를 점검하는 전문 리뷰어입니다. JSON 객체만 반환합니다.",
            "messages": [{"role": "user", "content": prompt}],
        }
        try:
            response = anthropic_messages_create(payload, timeout=120)
            review = parse_json_object(anthropic_response_text(response))
            return merge_claude_review(plan, review, model), model
        except Exception as exc:
            last_error = str(exc)
            log_line(f"Claude review failed with {model}: {exc}")
    raise RuntimeError(last_error or "Claude review failed")


def enhance_plan_with_ai(
    plan: dict[str, Any],
    company: dict[str, Any],
    template: dict[str, Any],
    options: dict[str, Any],
) -> dict[str, Any]:
    output = json.loads(json.dumps(plan, ensure_ascii=False))
    pipeline: list[dict[str, str]] = []
    errors: list[str] = []

    if gemini_api_key():
        model = AI_MODEL_ASSIGNMENTS["primaryDraft"]["model"]
        try:
            output = apply_gemini_draft(output, company, template, options)
            pipeline.append({"stage": "한글 보고서 1차 초안", "provider": "Google", "model": model, "status": "ok"})
        except Exception as exc:
            errors.append(f"Gemini draft: {exc}")
            log_line(f"Gemini draft fallback: {exc}")

    if openai_api_key():
        model = AI_MODEL_ASSIGNMENTS["finalPolish"]["model"]
        try:
            output = apply_openai_polish(output, company, template, options)
            pipeline.append({"stage": "제출용 본문 정제", "provider": "OpenAI", "model": model, "status": "ok"})
        except Exception as exc:
            errors.append(f"OpenAI polish: {exc}")
            log_line(f"OpenAI polish fallback: {exc}")

    if anthropic_api_key():
        model = AI_MODEL_ASSIGNMENTS["strategicRedTeam"]["model"]
        try:
            output, used_model = apply_claude_review(output, company, template, options)
            pipeline.append({"stage": "심사위원 관점 최종 리뷰", "provider": "Anthropic", "model": used_model, "status": "ok"})
        except Exception as exc:
            errors.append(f"Claude review: {exc}")
            log_line(f"Claude review fallback: {exc}")
            fallback_model = AI_MODEL_ASSIGNMENTS["strategicRedTeam"].get("fallbackModel") or model
            pipeline.append({"stage": "심사위원 관점 최종 리뷰", "provider": "Anthropic", "model": fallback_model, "status": "failed"})

    if pipeline:
        successful = [item for item in pipeline if item.get("status") == "ok"]
        if successful:
            message = " -> ".join(f"{item['provider']} {item['model']}" for item in successful) + " 순서로 사업계획서를 보강했습니다."
            output["aiEngine"] = build_ai_engine_report("multi_provider_pipeline", message, " | ".join(errors))
            output["aiEngine"]["pipeline"] = pipeline
            output["aiEngine"]["errors"] = errors
            return output

    if errors:
        output["aiEngine"] = build_ai_engine_report(
            "local_fallback",
            "외부 AI 호출이 실패해 로컬 생성기를 사용했습니다.",
            " | ".join(errors),
        )
    else:
        output["aiEngine"] = build_ai_engine_report(
            "local_fallback",
            "외부 AI API 키가 없어 로컬 생성기를 사용했습니다. GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY를 추가하면 단계별 AI 파이프라인이 작동합니다.",
        )
    return output


def enhance_plan_with_openai(
    plan: dict[str, Any],
    company: dict[str, Any],
    template: dict[str, Any],
    options: dict[str, Any],
) -> dict[str, Any]:
    return enhance_plan_with_ai(plan, company, template, options)


def section_body(
    company: dict[str, Any],
    category: str,
    prompt: str,
    length: str,
    document_insights: dict[str, Any] | None = None,
    additional_notes: str = "",
    template_guidance: dict[str, Any] | None = None,
    planned_role: str = "",
) -> str:
    name = value(company, "basic.name", "회사")
    one_line = value(company, "business.oneLine", f"{name}의 핵심 사업 아이템")
    target = value(company, "business.targetCustomer", "목표 고객")
    problem = value(company, "business.problem", "고객이 겪는 핵심 문제")
    solution = value(company, "business.solution", f"{name}의 해결 방식")
    product = value(company, "business.product", "제품·서비스")
    stage = value(company, "business.stage", "현재 개발 단계")
    diff = value(company, "business.differentiation", "차별화 요소")
    revenue = value(company, "business.revenueModel", "수익모델")
    market_size = value(company, "market.marketSize", "목표 시장 규모")
    trend = value(company, "market.trend", "시장 변화")
    competitors = value(company, "market.competitors", "기존 대안과 경쟁사")
    gtm = value(company, "market.goToMarket", "초기 고객 확보 전략")
    metrics = value(company, "traction.metrics", "현재 검증 지표")
    customers = value(company, "traction.customers", "초기 고객·파트너")
    founder = value(company, "team.founder", "대표자의 관련 경험")
    members = value(company, "team.members", "팀 구성")
    funding = value(company, "finance.fundingNeed", "필요 자금")
    use = value(company, "finance.useOfFunds", "지원금 사용 계획")
    sales = value(company, "finance.salesPlan", "매출 계획")
    milestones = value(company, "finance.milestones", "추진 마일스톤")
    job = value(company, "impact.jobCreation", "고용 창출 계획")
    social = value(company, "impact.socialValue", "사회적 가치")
    business_number = value(company, "legal.businessNumber", "")
    corporate_number = value(company, "legal.corporateNumber", "")
    legal_line = ""
    if business_number or corporate_number:
        legal_items = []
        if business_number:
            legal_items.append(f"사업자등록번호 {business_number}")
        if corporate_number:
            legal_items.append(f"법인등록번호 {corporate_number}")
        legal_line = " 법적 기본정보는 " + ", ".join(legal_items) + "로 확인됩니다."

    bodies = {
        "overview": [
            f"{name}{topic_josa(name)} 핵심 고객을 다음과 같이 설정합니다: {target}. 이를 바탕으로 {one_line}{object_josa(one_line)} 추진하는 창업기업입니다.",
            f"현재 고객이 겪는 핵심 문제는 다음과 같습니다. {sentence_clause(problem)} {name}{topic_josa(name)} {product}{object_josa(product)} 통해 이 문제를 더 빠르고 지속 가능한 방식으로 개선합니다.{legal_line}",
            f"이번 지원사업에서는 {stage} 수준의 아이템을 시장 검증과 사업화 단계로 끌어올리고, {use}에 집중해 첫 성과를 만들겠습니다.",
        ],
        "problem": [
            f"목표 고객은 {target}입니다. 이들이 반복적으로 겪는 핵심 문제는 다음과 같습니다. {sentence_clause(problem)}",
            f"기존 대안은 {competitors} 등이며, 비용, 접근성, 지속성, 개인화 측면에서 한계가 있습니다.",
            f"따라서 본 사업은 단순한 기능 개발이 아니라 고객의 행동 변화와 구매 전환을 만드는 문제 해결 과제입니다.",
        ],
        "solution": [
            f"{name}의 핵심 해결책은 {sentence_clause(solution)}",
            f"제품·서비스는 {product}로 구성되며, 현재 단계는 {sentence_clause(stage)}",
            f"지원기간에는 핵심 기능 완성, 고객 테스트, 피드백 반영, 유료 전환 검증 순서로 실행하겠습니다.",
        ],
        "market": [
            f"진입 시장은 {target}{object_josa(target)} 중심으로 설정합니다.",
            f"시장 근거는 {sentence_text(market_size)}이며, 최근 변화는 {sentence_text(trend)}입니다.",
            f"초기에는 {gtm}으로 고객 접점을 만들고, 검증된 세그먼트에서 반복 판매 구조를 확장하겠습니다.",
        ],
        "differentiation": [
            f"주요 경쟁·대체재는 {competitors}입니다.",
            f"{name}의 차별성은 {diff}에 있습니다.",
            f"이 차별성은 단순 기능 비교가 아니라 고객 획득 비용, 재사용률, 데이터 축적, 운영 효율 측면의 경쟁우위로 연결됩니다.",
        ],
        "business_model": [
            f"수익모델은 {revenue}입니다.",
            f"초기 매출은 {sales}{object_josa(sales)} 기준으로 설계하고, 고객 확보는 {gtm}{object_josa(gtm)} 활용합니다.",
            f"지원사업 기간에는 무료 사용 또는 파일럿에 머무르지 않고, 지불 의사가 확인되는 고객군을 선별해 유료 전환 실험을 진행하겠습니다.",
        ],
        "growth": [
            f"현재 확보한 검증 지표는 {metrics}이며, 초기 고객·파트너는 {customers}입니다.",
            f"향후 추진 일정은 {milestones}입니다.",
            f"각 단계는 개발 산출물, 고객 반응, 매출 가능성이라는 세 가지 기준으로 점검해 다음 투자·지원 연계가 가능한 성과로 만들겠습니다.",
        ],
        "budget": [
            f"본 사업에 필요한 자금은 {sentence_clause(funding)}",
            f"지원금은 {use}에 우선 투입합니다.",
            f"예산은 고객 검증과 매출 발생에 직접 연결되는 항목 중심으로 집행하고, 집행 후에는 산출물·성과지표·증빙자료를 함께 관리하겠습니다.",
        ],
        "team": [
            f"대표자의 핵심 역량은 {sentence_clause(founder)}",
            f"팀 구성은 {members}이며, 부족한 역량은 채용·외부 전문가·파트너십으로 보완합니다.",
            f"팀의 강점은 아이템을 기획하는 데서 끝나지 않고 고객 인터뷰, 빠른 실행, 데이터 기반 개선까지 이어지는 실행력입니다.",
        ],
        "impact": [
            f"본 사업의 기대 효과는 매출 성장뿐 아니라 {social}로 확장됩니다.",
            f"고용 측면에서는 {job}{object_josa(job)} 계획합니다.",
            f"지원사업 성과는 고객 편익, 지역·산업 파급효과, 후속 투자와 고용 창출로 이어지도록 관리하겠습니다.",
        ],
        "risk": [
            f"주요 리스크는 고객 검증 지연, 경쟁 대안 대비 차별성 약화, 일정 지연입니다.",
            f"이에 대해 {milestones}{object_josa(milestones)} 기준으로 단계별 검증 지표를 설정하고, 고객 반응이 낮은 기능은 빠르게 축소하거나 대체안을 적용하겠습니다.",
            f"지원금 집행은 {use}와 연결해 리스크를 줄이는 실험 중심으로 운영하겠습니다.",
        ],
    }
    paragraphs = bodies.get(category, bodies["overview"])
    if length == "short":
        base = "\n\n".join(paragraphs[:2])
        return append_context(base, category, document_insights or {}, additional_notes, template_guidance or {}, planned_role)
    if length == "deep":
        base = "\n\n".join(
            paragraphs
            + [
                "심사 관점에서는 이 항목이 지원 필요성과 실행 가능성을 동시에 보여주는 부분이므로, 실제 수치와 증빙자료를 붙이면 완성도가 높아집니다.",
            ]
        )
        return append_context(base, category, document_insights or {}, additional_notes, template_guidance or {}, planned_role)
    return append_context("\n\n".join(paragraphs), category, document_insights or {}, additional_notes, template_guidance or {}, planned_role)


def append_context(
    base: str,
    category: str,
    document_insights: dict[str, Any],
    additional_notes: str,
    template_guidance: dict[str, Any],
    planned_role: str,
) -> str:
    context_lines = document_context_lines(category, document_insights)
    if context_lines:
        base += "\n\n업로드 문서 반영: " + " ".join(context_lines[:3])
    understanding_lines = business_understanding_context_lines(category, document_insights)
    if understanding_lines:
        base += "\n\n기존 사업계획서 심층 반영: " + " ".join(understanding_lines[:4])
    if planned_role:
        base += f"\n\n전체 구성 반영: 이 항목은 '{planned_role}' 역할을 하도록 작성합니다."
    if template_guidance.get("focusPoints") and category in {"overview", "problem", "solution", "market", "differentiation", "business_model"}:
        base += "\n\n중점 포인트: " + template_guidance["focusPoints"][:700]
    if additional_notes.strip() and category in {"overview", "solution", "business_model", "growth", "budget"}:
        base += "\n\n추가 의견 반영: " + clean_text(additional_notes)[:700]
    if template_guidance.get("formatRules") and category in {"overview", "budget", "growth"}:
        base += "\n\n형식 유의사항: " + template_guidance["formatRules"][:500]
    return base


def business_understanding_context_lines(category: str, document_insights: dict[str, Any]) -> list[str]:
    understanding = (document_insights or {}).get("businessUnderstanding") or {}
    knowledge = understanding.get("knowledge") or {}
    if not knowledge:
        return []
    area_ids = SECTION_UNDERSTANDING_MAP.get(category, ["overview", "problem", "solution"])
    lines: list[str] = []
    for area_id in area_ids:
        area = knowledge.get(area_id) or {}
        if area.get("status") == "missing":
            continue
        synthesized = clean_text(area.get("synthesized", ""))
        evidence = area.get("evidence") or []
        if synthesized:
            lines.append(f"{area.get('label', area_id)}는 기존 원문에서 {synthesized[:420]}")
            continue
        if evidence:
            top = evidence[0]
            lines.append(f"{area.get('label', area_id)} 근거: {clean_text(top.get('text', ''))[:420]}")
    return lines[:6]


def support_tokens(text: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z가-힣0-9][A-Za-z가-힣0-9\-\+\.]{1,}", clean_text(text).lower())
    stopwords = {
        "사업",
        "계획",
        "지원",
        "고객",
        "제품",
        "서비스",
        "시장",
        "기반",
        "진행",
        "추진",
        "개선",
        "운영",
        "활용",
        "통해",
        "위한",
        "대한",
    }
    return {token for token in tokens if len(token) >= 2 and token not in stopwords}


def support_numbers(text: str) -> set[str]:
    numbers = re.findall(r"\d[\d,]*(?:\.\d+)?\s*(?:%|명|건|개|원|만원|억원|회|월|년|주|점)?", clean_text(text))
    return {re.sub(r"\s+", "", number) for number in numbers if number.strip()}


def section_evidence_candidates(section: dict[str, Any], document_insights: dict[str, Any]) -> list[dict[str, Any]]:
    understanding = (document_insights or {}).get("businessUnderstanding") or {}
    knowledge = understanding.get("knowledge") or {}
    category = section.get("category") or "overview"
    area_ids = SECTION_UNDERSTANDING_MAP.get(category, ["overview", "problem", "solution"])
    candidates: list[dict[str, Any]] = []
    for area_id in area_ids:
        area = knowledge.get(area_id) or {}
        for evidence in area.get("evidence", []) or []:
            item = dict(evidence)
            item.setdefault("area", area_id)
            item.setdefault("areaLabel", area.get("label", area_id))
            candidates.append(item)
    for evidence in understanding.get("evidenceBank", []) or []:
        if evidence.get("area") in area_ids:
            candidates.append(dict(evidence))
    return dedupe_ranked_evidence(candidates, 12)


def evidence_match_score(section_text: str, evidence_text: str) -> int:
    section_tokens = support_tokens(section_text)
    evidence_tokens = support_tokens(evidence_text)
    overlap = section_tokens & evidence_tokens
    section_numbers = support_numbers(section_text)
    evidence_numbers = support_numbers(evidence_text)
    number_hits = section_numbers & evidence_numbers
    score = min(60, len(overlap) * 6) + min(40, len(number_hits) * 14)
    if clean_text(evidence_text)[:80] and clean_text(evidence_text)[:80] in section_text:
        score += 20
    return min(100, score)


def build_evidence_traceability(sections: list[dict[str, Any]], document_insights: dict[str, Any] | None) -> dict[str, Any]:
    document_insights = document_insights or {}
    section_reports: list[dict[str, Any]] = []
    for section in sections:
        candidates = section_evidence_candidates(section, document_insights)
        matches: list[dict[str, Any]] = []
        section_text = clean_text(section.get("content", ""))
        for candidate in candidates:
            text = clean_text(candidate.get("text", ""))
            score = evidence_match_score(section_text, text)
            if score >= 12:
                item = dict(candidate)
                item["matchScore"] = score
                matches.append(item)
        matches = sorted(matches, key=lambda item: item.get("matchScore", 0), reverse=True)[:5]
        support_score = round(sum(item.get("matchScore", 0) for item in matches[:3]) / max(1, min(3, len(matches)))) if matches else 0
        if support_score >= 45 or len(matches) >= 3:
            status = "grounded"
        elif matches:
            status = "partial"
        elif candidates:
            status = "needs_grounding"
        else:
            status = "no_source"
        section_reports.append(
            {
                "sectionId": section.get("id", ""),
                "heading": section.get("heading", ""),
                "category": section.get("category", ""),
                "status": status,
                "supportScore": support_score,
                "availableEvidence": len(candidates),
                "matchedEvidence": [
                    {
                        "area": item.get("area", ""),
                        "areaLabel": item.get("areaLabel", ""),
                        "source": item.get("source", ""),
                        "text": item.get("text", ""),
                        "matchScore": item.get("matchScore", 0),
                    }
                    for item in matches
                ],
                "suggestedEvidence": [
                    {
                        "area": item.get("area", ""),
                        "areaLabel": item.get("areaLabel", ""),
                        "source": item.get("source", ""),
                        "text": item.get("text", ""),
                    }
                    for item in candidates[:3]
                ],
            }
        )
    grounded = sum(1 for item in section_reports if item.get("status") == "grounded")
    partial = sum(1 for item in section_reports if item.get("status") == "partial")
    needs = sum(1 for item in section_reports if item.get("status") in {"needs_grounding", "no_source"})
    total = len(section_reports)
    average_score = round(sum(item.get("supportScore", 0) for item in section_reports) / total) if total else 0
    return {
        "status": "ok" if total and needs == 0 and average_score >= 35 else ("partial" if grounded or partial else "needs_work"),
        "totalSections": total,
        "groundedSections": grounded,
        "partialSections": partial,
        "needsGroundingSections": needs,
        "averageSupportScore": average_score,
        "sections": section_reports,
    }


RISKY_CLAIM_PHRASES = [
    "국내 최초",
    "세계 최초",
    "업계 최초",
    "유일",
    "최고",
    "최상",
    "압도적",
    "완벽",
    "100%",
    "반드시",
    "확실",
    "독보적",
]


def evidence_text_blob(document_insights: dict[str, Any] | None) -> str:
    document_insights = document_insights or {}
    parts = [document_insights.get("combinedText", "")]
    understanding = document_insights.get("businessUnderstanding") or {}
    for item in understanding.get("evidenceBank", []) or []:
        parts.append(item.get("text", ""))
    for area in (understanding.get("knowledge") or {}).values():
        parts.append(area.get("synthesized", ""))
        for evidence in area.get("evidence", []) or []:
            parts.append(evidence.get("text", ""))
    for doc in (document_insights.get("businessPlanCorpus") or {}).get("documents", []) or []:
        parts.append(doc.get("text", ""))
    return clean_text("\n".join(part for part in parts if part))


def sentence_candidates(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?。！？다])\s+", clean_text(text))
    return [sentence.strip() for sentence in sentences if 12 <= len(sentence.strip()) <= 320]


def audit_unsupported_claims(sections: list[dict[str, Any]], document_insights: dict[str, Any] | None) -> dict[str, Any]:
    source_blob = evidence_text_blob(document_insights)
    source_numbers = support_numbers(source_blob)
    claims: list[dict[str, Any]] = []
    for section in sections:
        content = clean_text(section.get("content", ""))
        for number in sorted(support_numbers(content)):
            if number and number not in source_numbers:
                sentence = next((item for item in sentence_candidates(content) if number in item.replace(" ", "")), number)
                claims.append(
                    {
                        "sectionId": section.get("id", ""),
                        "heading": section.get("heading", ""),
                        "claim": sentence[:260],
                        "reason": f"본문 숫자 '{number}'가 업로드 원문 근거은행에서 확인되지 않습니다.",
                        "severity": "high",
                    }
                )
        for phrase in RISKY_CLAIM_PHRASES:
            if phrase in content and phrase not in source_blob:
                sentence = next((item for item in sentence_candidates(content) if phrase in item), phrase)
                claims.append(
                    {
                        "sectionId": section.get("id", ""),
                        "heading": section.get("heading", ""),
                        "claim": sentence[:260],
                        "reason": f"'{phrase}' 표현은 심사에서 근거 요구 가능성이 높습니다.",
                        "severity": "medium",
                    }
                )
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for claim in claims:
        marker = (claim.get("sectionId", ""), claim.get("claim", ""), claim.get("reason", ""))
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(claim)
    high = sum(1 for item in deduped if item.get("severity") == "high")
    medium = sum(1 for item in deduped if item.get("severity") == "medium")
    return {
        "status": "ok" if not high and medium <= 2 else "needs_work",
        "totalClaims": len(deduped),
        "highRiskClaims": high,
        "mediumRiskClaims": medium,
        "claims": deduped[:20],
    }


def attach_grounding_audit(plan: dict[str, Any], document_insights: dict[str, Any] | None) -> dict[str, Any]:
    output = json.loads(json.dumps(plan, ensure_ascii=False))
    sections = output.get("sections") or []
    traceability = build_evidence_traceability(sections, document_insights)
    unsupported = audit_unsupported_claims(sections, document_insights)
    output["evidenceTraceability"] = traceability
    output["unsupportedClaimAudit"] = unsupported
    quality = [
        item
        for item in output.get("qualityChecks", [])
        if item.get("label") not in {"원문 근거 추적성", "근거 없는 주장 점검"}
    ]
    quality.append(
        {
            "label": "원문 근거 추적성",
            "status": "ok" if traceability.get("status") == "ok" else "needs_work",
            "message": (
                f"{traceability.get('groundedSections', 0)}개 문항은 원문 근거가 충분히 연결됐고 "
                f"{traceability.get('needsGroundingSections', 0)}개 문항은 추가 근거 반영이 필요합니다. "
                f"평균 근거점수 {traceability.get('averageSupportScore', 0)}점."
            ),
        }
    )
    quality.append(
        {
            "label": "근거 없는 주장 점검",
            "status": "ok" if unsupported.get("status") == "ok" else "needs_work",
            "message": (
                "원문 근거 없이 새로 등장한 고위험 숫자·과장 표현이 없습니다."
                if unsupported.get("status") == "ok"
                else f"고위험 {unsupported.get('highRiskClaims', 0)}건, 주의 {unsupported.get('mediumRiskClaims', 0)}건을 확인하세요."
            ),
        }
    )
    output["qualityChecks"] = quality
    return output


def document_context_lines(category: str, document_insights: dict[str, Any]) -> list[str]:
    if not document_insights:
        return []
    related = {
        "overview": {"business_registration", "corporate_registry", "existing_business_plan", "general"},
        "problem": {"existing_business_plan", "general"},
        "solution": {"existing_business_plan", "ip_certification", "general"},
        "market": {"existing_business_plan", "general"},
        "differentiation": {"existing_business_plan", "ip_certification", "general"},
        "business_model": {"existing_business_plan", "finance", "general"},
        "growth": {"existing_business_plan", "finance", "general"},
        "budget": {"finance", "existing_business_plan", "general"},
        "team": {"business_registration", "corporate_registry", "existing_business_plan", "general"},
        "impact": {"existing_business_plan", "general"},
        "risk": {"existing_business_plan", "finance", "general"},
    }.get(category, {"general"})
    lines: list[str] = []
    for doc in document_insights.get("documents", []):
        if doc.get("documentType") not in related:
            continue
        summary = doc.get("summary", "")
        if summary and "텍스트를 충분히" not in summary:
            lines.append(f"{doc.get('documentTypeLabel', '참고자료')}에서 확인된 내용은 {summary}입니다.")
    facts = document_insights.get("facts", [])
    if category in {"overview", "team"}:
        for fact in facts[:5]:
            lines.append(f"{fact.get('label')}: {fact.get('value')}.")
    return lines[:4]


def estimate_pages(sections: list[dict[str, Any]]) -> float:
    total_chars = sum(len(str(section.get("heading", ""))) + len(str(section.get("content", ""))) for section in sections)
    # Korean HWP business plans commonly land around 1,350-1,650 Korean chars per page
    # depending on tables and line spacing. Use a conservative middle estimate.
    return max(1.0, round(total_chars / 1500, 1))


def expand_sections_for_page_target(
    sections: list[dict[str, Any]],
    company: dict[str, Any],
    guidance: dict[str, Any],
    template: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    page_count = guidance.get("pageCount")
    if not page_count:
        return sections
    try:
        target_pages = float(page_count)
    except ValueError:
        return sections
    if target_pages <= 1 or not sections:
        return sections
    within_limit = has_page_limit_within(template or {}, guidance)
    target_multiplier = 0.86 if within_limit else 1.0
    target_chars = min(int(target_pages * 1500 * target_multiplier), 24000)
    current_chars = sum(len(section.get("content", "")) for section in sections)
    if current_chars >= target_chars * 0.75:
        return sections
    per_section_target = max(900, int(target_chars / len(sections)))
    expanded: list[dict[str, Any]] = []
    for section in sections:
        section = dict(section)
        additions = deepening_paragraphs(section.get("category", ""), company)
        content = section.get("content", "")
        addition_index = 0
        while len(content) < per_section_target and addition_index < len(additions):
            content += "\n\n" + additions[addition_index]
            addition_index += 1
        section["content"] = content
        expanded.append(section)
    return expanded


def deepening_paragraphs(category: str, company: dict[str, Any]) -> list[str]:
    name = value(company, "basic.name", "회사")
    target = value(company, "business.targetCustomer", "목표 고객")
    product = value(company, "business.product", "제품·서비스")
    differentiation = value(company, "business.differentiation", "차별화 요소")
    gtm = value(company, "market.goToMarket", "고객 확보 전략")
    metrics = value(company, "traction.metrics", "검증 지표")
    use = value(company, "finance.useOfFunds", "자금 사용 계획")
    milestones = value(company, "finance.milestones", "추진 일정")
    sales = value(company, "finance.salesPlan", "매출 계획")
    shared = [
        f"실행 측면에서 {name}은 지원기간 동안 핵심 가설을 작은 단위로 검증하고, 고객 반응이 확인된 기능과 채널에 자원을 집중하겠습니다. 이를 통해 단순한 계획이 아니라 제출 시점 이후 바로 실행 가능한 사업화 로드맵을 제시합니다.",
        f"성과 관리는 산출물 중심이 아니라 고객 반응, 재사용 의향, 유료 전환 가능성, 후속 파트너십 가능성을 함께 보겠습니다. 이 기준은 지원금 집행 결과가 실제 사업 성과로 연결되는지 판단하는 근거가 됩니다.",
        f"세부 실행은 담당 역할, 일정, 산출물, 확인 지표를 함께 정의해 운영합니다. {name}은 각 단계 종료 시점마다 고객 피드백과 내부 실행 결과를 비교해 다음 단계 투자 여부를 판단하고, 불확실성이 큰 영역부터 우선 검증하겠습니다.",
        "증빙자료는 계획서의 신뢰도를 높이는 핵심 요소로 관리합니다. 고객 인터뷰 기록, 파일럿 참여 의향, 견적서, 개발 산출물, 파트너 협의 내용, 매출 가정표 등을 항목별로 연결해 심사위원이 실행 가능성을 확인할 수 있게 하겠습니다.",
        "지원사업 기간 중에는 정량 지표와 정성 지표를 함께 추적합니다. 정량 지표는 고객 수, 전환율, 사용 빈도, 매출 가능성으로 두고, 정성 지표는 고객 불편의 강도, 도입 장애 요인, 구매 의사결정자의 반응으로 정리합니다.",
        "리스크 관리는 일정 지연, 고객 확보 지연, 개발 범위 확대, 경쟁 대안 출현을 중심으로 운영합니다. 각 리스크는 조기 경보 지표를 설정하고, 지표가 기준에 미달할 경우 기능 범위 조정, 채널 전환, 외부 협력 강화로 대응하겠습니다.",
        "지원금 사용은 사업 목표와 직접 연결되는 항목에 우선순위를 둡니다. 비용 집행 전에는 기대 산출물과 검증 지표를 설정하고, 집행 후에는 결과와 다음 의사결정 근거를 남겨 사업비 사용의 타당성을 확보하겠습니다.",
        "후속 성장 관점에서는 지원사업 종료 후에도 반복 가능한 매출 구조와 운영 체계를 남기는 것이 중요합니다. 따라서 단기 산출물뿐 아니라 고객 획득 프로세스, 데이터 축적 방식, 내부 업무 프로세스, 파트너십 확장 가능성을 함께 설계하겠습니다.",
        "운영 체계는 주간 단위 실행 점검과 월간 성과 리뷰로 나누어 관리합니다. 주간 점검에서는 진행률과 이슈를 확인하고, 월간 리뷰에서는 고객 반응, 비용 집행, 산출물 품질, 다음 달 우선순위를 결정해 계획과 실행의 간극을 줄이겠습니다.",
        "고객 검증은 단순 설문보다 실제 사용 또는 구매 의사 확인에 초점을 둡니다. 인터뷰, 데모, 파일럿, 견적 요청, 계약 논의 등 단계별 반응을 구분해 기록하고, 가장 강한 구매 신호가 나타나는 고객군을 우선 공략하겠습니다.",
        "사업계획서의 표현은 추상적인 가능성보다 실행 가능한 근거를 앞세우겠습니다. 각 주장에는 고객군, 문제, 해결 방식, 실행 일정, 증빙자료 중 하나 이상을 연결해 심사 과정에서 검토 가능한 문장으로 정리합니다.",
        "지원사업 이후에는 후속 지원사업, 민간 투자, 전략적 제휴, 유료 고객 확대 중 가장 가능성이 높은 경로를 선택할 수 있도록 데이터를 축적하겠습니다. 이 데이터는 제품 개선뿐 아니라 다음 성장 단계의 의사결정 근거가 됩니다.",
        "제출 형식 측면에서는 양식의 문항명과 순서를 유지하고, 사용자가 요구한 분량과 중점 포인트에 맞춰 문단별 역할을 분명히 하겠습니다. 표나 지정 항목이 있는 경우에는 해당 위치를 보존하고, 임의로 항목을 삭제하지 않는 방식으로 작성합니다.",
    ]
    by_category = {
        "overview": [
            f"{name}의 사업은 {target}{subject_josa(target)} 겪는 문제를 {product}{direction_josa(product)} 해결하는 구조입니다. 사업계획서 전체에서는 문제의 절박성, 해결책의 실행 가능성, 지원금 사용의 직접성을 일관되게 연결해 심사위원이 사업의 우선순위를 빠르게 이해하도록 구성합니다.",
            f"본 계획의 핵심 메시지는 지원사업을 통해 제품 완성도를 높이는 데 그치지 않고, 시장 검증과 초기 매출 가능성을 동시에 확보한다는 점입니다. 따라서 각 항목은 고객, 제품, 시장, 자금 사용, 기대효과가 서로 분리되지 않도록 작성합니다.",
        ],
        "problem": [
            f"목표 고객은 기존 대안으로 문제를 완전히 해결하지 못하고 있으며, 이로 인해 시간, 비용, 품질, 접근성 측면의 손실이 반복됩니다. 본 항목에서는 고객 인터뷰, 사용 행태, 대체재 한계를 근거로 문제의 중요도를 설명합니다.",
            "문제 정의는 넓은 시장을 과장하기보다 초기 고객군에서 가장 강하게 나타나는 불편을 중심으로 정리합니다. 이렇게 해야 이후 솔루션, 시장 진입, 매출 전략이 하나의 논리로 이어집니다.",
        ],
        "solution": [
            f"{product}{topic_josa(product)} 고객이 문제를 인식하고 해결 행동으로 이동하는 과정을 줄이는 데 초점을 둡니다. 핵심 기능은 고객의 반복 행동을 단순화하고, 운영자는 데이터를 통해 개선 우선순위를 판단할 수 있게 설계합니다.",
            f"차별성은 {differentiation}입니다. 이 강점은 기능 설명에서 끝나지 않고 고객 유지율, 전환율, 운영 효율, 파트너십 확장 가능성으로 연결되도록 검증하겠습니다.",
        ],
        "market": [
            f"초기 시장은 {target}{object_josa(target)} 중심으로 좁게 정의하고, 실제 구매 또는 도입 의사결정이 가능한 세그먼트부터 접근합니다. 이후 검증된 고객군의 공통 니즈를 기반으로 인접 시장으로 확장합니다.",
            f"고객 확보는 {gtm}{object_josa(gtm)} 기준으로 진행합니다. 첫 고객 확보 단계에서는 유입 채널, 상담 전환, 파일럿 참여, 유료 전환까지의 흐름을 지표화해 반복 가능한 영업 구조를 만들겠습니다.",
        ],
        "differentiation": [
            f"{name}의 경쟁우위는 {differentiation}에 있으며, 이는 단기 기능 차이보다 고객 데이터 축적, 운영 프로세스, 파트너십, 브랜드 신뢰의 누적으로 강화됩니다.",
            "경쟁 비교는 단순히 경쟁사가 부족하다는 방식이 아니라, 고객이 실제로 선택할 기준을 중심으로 작성합니다. 가격, 접근성, 성과 측정, 도입 편의성, 사후관리 항목에서 우위를 입증하겠습니다.",
        ],
        "business_model": [
            f"초기 매출 계획은 {sales}{object_josa(sales)} 기준으로 설정합니다. 지원기간에는 고객 확보 채널별 전환율을 비교하고, 반복 결제가 가능한 가격 구조와 계약 단위를 검증하겠습니다.",
            f"사업화 전략은 {gtm}에서 출발합니다. 고객 접점 확보 후에는 파일럿, 유료 전환, 추천 또는 확장 계약으로 이어지는 단계를 설계해 매출 발생 가능성을 높이겠습니다.",
        ],
        "growth": [
            f"추진 일정은 {milestones}{object_josa(milestones)} 기준으로 운영합니다. 각 단계에는 산출물, 담당자, 검증 지표, 의사결정 기준을 설정해 일정 지연과 성과 불확실성을 줄이겠습니다.",
            f"검증 지표는 {metrics}입니다. 정량 지표와 정성 피드백을 함께 수집해 제품 개선, 고객 세그먼트 조정, 수익모델 확정에 활용하겠습니다.",
        ],
        "budget": [
            f"지원금은 {use}에 집중 투입합니다. 각 예산 항목은 고객 검증, 제품 고도화, 시장 진입, 성과 측정과 직접 연결되도록 산출 근거를 제시하겠습니다.",
            "예산 집행은 단순 비용 사용이 아니라 리스크를 줄이는 실험 설계로 운영합니다. 집행 후에는 결과물, 고객 반응, 다음 단계 의사결정 근거를 함께 남겨 후속 지원과 투자 검토가 가능하게 하겠습니다.",
        ],
        "team": [
            f"{name}은 대표와 팀의 역할을 사업 성공요인에 맞춰 배치합니다. 내부 역량으로 해결하기 어려운 영역은 전문가 자문, 외주, 파트너십을 통해 보완하겠습니다.",
            "팀 역량은 이력 나열보다 문제 해결 경험, 실행 속도, 고객 이해도, 보완 계획을 중심으로 작성합니다. 심사위원이 실행 가능성을 판단할 수 있도록 역할과 책임을 구체화합니다.",
        ],
        "impact": [
            "기대효과는 매출 성장, 고객 편익, 고용 창출, 산업 또는 지역 파급효과로 나눠 제시합니다. 각 효과는 지원사업 종료 후에도 추적 가능한 지표로 관리하겠습니다.",
            f"{name}의 성과는 단기 산출물에서 끝나지 않고 후속 고객 확보, 파트너십, 반복 매출, 신규 채용 가능성으로 이어지는 구조를 목표로 합니다.",
        ],
        "risk": [
            "주요 리스크는 고객 검증 지연, 개발 일정 지연, 경쟁 대안 대비 차별성 약화입니다. 각 리스크는 조기 지표를 설정하고 대안 실험을 준비해 관리하겠습니다.",
            "리스크 대응은 문제가 발생한 뒤 조치하는 방식이 아니라, 지원기간 초반부터 검증 실험과 피드백 루프를 설계하는 방식으로 운영합니다.",
        ],
    }
    return by_category.get(category, shared) + shared


def validate_plan_format(sections: list[dict[str, Any]], template: dict[str, Any], guidance: dict[str, Any]) -> list[dict[str, str]]:
    questions = template.get("questions") or []
    validations: list[dict[str, str]] = []
    strict_format = bool(guidance.get("strictFormat"))
    if questions:
        same_count = len(sections) == len(questions)
        validations.append(
            {
                "label": "문항 개수 일치",
                "status": "ok" if same_count else "needs_work",
                "message": f"양식 문항 {len(questions)}개와 초안 섹션 {len(sections)}개를 비교했습니다.",
            }
        )
        heading_mismatches = []
        for index, question in enumerate(questions):
            if index >= len(sections):
                heading_mismatches.append(str(index + 1))
                continue
            prompt = normalize_prompt(question.get("prompt", ""))
            heading = normalize_prompt(sections[index].get("heading", ""))
            if prompt and prompt[:18] not in heading and heading[:18] not in prompt:
                heading_mismatches.append(str(index + 1))
        validations.append(
            {
                "label": "문항 순서·제목",
                "status": "ok" if not heading_mismatches else "needs_work",
                "message": "원문 양식의 문항 순서와 제목을 유지했습니다." if not heading_mismatches else f"{', '.join(heading_mismatches)}번 문항 제목 확인이 필요합니다.",
            }
        )
    else:
        validations.append(
            {
                "label": "양식 문항 감지",
                "status": "needs_work",
                "message": "업로드 양식에서 문항을 충분히 감지하지 못해 표준 구조를 사용했습니다.",
            }
        )

    validations.append(
        {
            "label": "양식 엄수 모드",
            "status": "ok" if strict_format and (questions or guidance.get("formatRules")) else "needs_work",
            "message": "양식 엄수 모드가 켜져 있고, 문항 또는 제출 규칙을 기준으로 초안을 검증합니다."
            if strict_format and (questions or guidance.get("formatRules"))
            else "양식 엄수 모드와 검증 기준이 함께 필요합니다. 공고문/양식 문항 또는 제출 규칙을 입력하세요.",
        }
    )

    empty_sections = [str(index + 1) for index, section in enumerate(sections) if len(clean_text(section.get("content", ""))) < 80]
    validations.append(
        {
            "label": "답변 누락",
            "status": "ok" if not empty_sections else "needs_work",
            "message": "모든 문항에 초안 본문이 있습니다." if not empty_sections else f"{', '.join(empty_sections)}번 문항 본문 보강이 필요합니다.",
        }
    )

    placeholder_terms = ["입력 필요", "추가 필요", "TBD", "미정", "TODO"]
    placeholder_sections = [
        str(index + 1)
        for index, section in enumerate(sections)
        if any(term.lower() in clean_text(section.get("content", "")).lower() for term in placeholder_terms)
    ]
    validations.append(
        {
            "label": "미완성 표현",
            "status": "ok" if not placeholder_sections else "needs_work",
            "message": "본문에 임시 입력 문구가 없습니다." if not placeholder_sections else f"{', '.join(placeholder_sections)}번 문항에 임시 표현이 남아 있습니다.",
        }
    )

    estimated = estimate_pages(sections)
    target_pages = guidance.get("pageCount")
    if target_pages:
        try:
            target = float(target_pages)
            within_limit = has_page_limit_within(template, guidance)
            if within_limit:
                lower = max(1.0, target * 0.65)
                status = "ok" if lower <= estimated <= target else "needs_work"
                message = f"{target_pages}페이지 이내 기준, 현재 본문은 약 {estimated}페이지로 추정됩니다."
            else:
                lower = max(1.0, target * 0.75)
                upper = target * 1.25
                status = "ok" if lower <= estimated <= upper else "needs_work"
                message = f"요청 {target_pages}페이지 기준, 현재 본문은 약 {estimated}페이지로 추정됩니다."
        except ValueError:
            status = "ok"
            message = f"분량 지시 '{target_pages}'를 초안 메타데이터에 반영했습니다. 현재 본문은 약 {estimated}페이지로 추정됩니다."
    else:
        status = "needs_work"
        message = f"목표 페이지 수가 입력되지 않았습니다. 현재 본문은 약 {estimated}페이지로 추정됩니다."
    validations.append({"label": "페이지 분량", "status": status, "message": message})

    structure_lines = guidance.get("structureLines") or []
    validations.append(
        {
            "label": "전체 구성 브리프",
            "status": "ok" if structure_lines else "needs_work",
            "message": f"구성 지시 {len(structure_lines)}개를 섹션 작성전략에 반영했습니다." if structure_lines else "지원사업 양식 페이지에서 전체 구성 지시를 입력하면 섹션별 역할이 더 명확해집니다.",
        }
    )

    if guidance.get("focusPoints"):
        validations.append(
            {
                "label": "중점 포인트",
                "status": "ok",
                "message": "사용자가 입력한 중점 포인트를 핵심 문항의 본문과 작성전략에 반영했습니다.",
            }
        )
    else:
        validations.append(
            {
                "label": "중점 포인트",
                "status": "needs_work",
                "message": "심사 포인트나 강조 메시지를 입력하면 초안의 설득 방향이 더 선명해집니다.",
            }
        )

    detected_requirements = template.get("requirements") or []
    manual_rules = guidance.get("formatRules")
    validations.append(
        {
            "label": "제출 형식 규칙",
            "status": "ok" if detected_requirements or manual_rules else "needs_work",
            "message": f"자동 감지 {len(detected_requirements)}개, 수동 입력 {'있음' if manual_rules else '없음'} 기준으로 점검했습니다." if detected_requirements or manual_rules else "분량, 글자 크기, 표 삭제 금지 등 제출 형식 규칙을 입력하거나 양식에 포함하세요.",
        }
    )

    rules_blob = " ".join(
        [
            str(manual_rules or ""),
            " ".join(str(item.get("value", "")) for item in detected_requirements),
        ]
    )
    font_rule = re.search(r"(\d{1,2})\s*(pt|포인트)", rules_blob, flags=re.I)
    if font_rule:
        validations.append(
            {
                "label": "글자 크기 규칙",
                "status": "ok",
                "message": f"양식에서 감지한 {font_rule.group(1)}pt 기준을 내보내기 검토 항목에 반영했습니다.",
            }
        )
    if any(keyword in rules_blob for keyword in ["표", "양식 유지", "삭제 금지", "항목명"]):
        validations.append(
            {
                "label": "표·항목 유지",
                "status": "ok" if questions else "needs_work",
                "message": "문항 제목과 순서를 보존해 표·항목 유지 규칙을 따르도록 구성했습니다."
                if questions
                else "표·항목 유지 규칙이 있으나 원문 문항 감지가 부족합니다. 양식 텍스트를 더 입력하세요.",
            }
        )

    return validations


def build_submission_format_manifest(
    sections: list[dict[str, Any]],
    template: dict[str, Any],
    guidance: dict[str, Any],
    format_validation: list[dict[str, str]],
    visual_assets: dict[str, Any],
) -> dict[str, Any]:
    failing = [item for item in format_validation if item.get("status") != "ok"]
    visual_assets = visual_assets or {}
    return {
        "documentFormat": "HWPX",
        "fontFamily": "Pretendard Variable",
        "pageSize": "A4",
        "estimatedPages": estimate_pages(sections),
        "targetPages": guidance.get("pageCount") or "",
        "strictFormat": bool(guidance.get("strictFormat")),
        "templateQuestionCount": len(template.get("questions") or []),
        "sectionCount": len(sections),
        "detectedRequirementCount": len(template.get("requirements") or []),
        "status": "ok" if not failing else "needs_work",
        "visualAssetCounts": {
            "tables": len(visual_assets.get("tables", [])),
            "infographics": len(visual_assets.get("infographics", [])),
            "imageBriefs": len(visual_assets.get("imageBriefs", [])),
        },
        "checklist": [
            "원문 문항 순서와 제목을 섹션 제목으로 보존",
            "제출 브리프의 페이지 수·구성·주안점·형식 규칙을 본문과 검증에 반영",
            "정확한 숫자가 필요한 표는 이미지가 아니라 구조화 표 데이터로 생성",
            "검토용 HTML과 HWPX에 Pretendard Variable 폰트 선언 적용",
            "제출 전 needs_work 항목을 우선 보완",
        ],
    }


def label_for_field(field: str) -> str:
    labels = {
        "business.oneLine": "한 줄 소개",
        "business.targetCustomer": "목표 고객",
        "business.product": "제품·서비스",
        "business.problem": "고객 문제",
        "business.solution": "해결 방식",
        "business.stage": "개발 단계",
        "business.differentiation": "차별성",
        "market.marketSize": "시장 규모",
        "market.trend": "시장 트렌드",
        "market.goToMarket": "고객 확보 전략",
        "market.competitors": "경쟁사",
        "business.revenueModel": "수익모델",
        "finance.salesPlan": "매출 계획",
        "finance.milestones": "추진 일정",
        "traction.metrics": "검증 지표",
        "finance.fundingNeed": "필요 자금",
        "finance.useOfFunds": "자금 사용 계획",
        "team.founder": "대표 역량",
        "team.members": "팀 구성",
        "impact.jobCreation": "고용 계획",
        "impact.socialValue": "사회적 가치",
    }
    return labels.get(field, field)


def evidence_needed(category: str) -> list[str]:
    evidence = {
        "overview": ["회사 소개서", "제품 화면 또는 서비스 플로우", "핵심 지표 요약"],
        "problem": ["고객 인터뷰", "설문 결과", "시장 리포트", "기존 대안 비교"],
        "solution": ["제품 캡처", "프로토타입 링크", "개발 로드맵", "고객 사용 시나리오"],
        "market": ["시장 규모 자료", "타깃 고객 정의", "초기 세그먼트 근거"],
        "differentiation": ["경쟁 비교표", "특허·노하우", "성능 또는 비용 비교"],
        "business_model": ["가격표", "매출 가정", "판매 파이프라인", "계약·LOI"],
        "growth": ["마일스톤표", "KPI 정의", "파일럿 결과", "파트너십 증빙"],
        "budget": ["견적서", "예산 산출 근거", "집행 일정"],
        "team": ["대표 이력", "팀원 역할표", "외부 전문가 협력 증빙"],
        "impact": ["고용 계획", "사회적 가치 지표", "지역 파급효과 근거"],
        "risk": ["리스크 매트릭스", "검증 실험 계획", "대응 시나리오"],
    }
    return evidence.get(category, ["정량 근거", "실행 계획", "증빙자료"])


def split_semantic_items(text: str, fallback: list[str], limit: int = 5) -> list[str]:
    cleaned = clean_text(text or "")
    if not cleaned:
        return fallback[:limit]
    parts = re.split(r"[\n,;·ㆍ/]|(?:\s-\s)|(?:\s>\s)", cleaned)
    items = [compact_value(part) for part in parts if compact_value(part)]
    if len(items) < 2:
        sentences = re.split(r"(?<=[.!?다요음])\s+", cleaned)
        items = [compact_value(sentence) for sentence in sentences if compact_value(sentence)]
    return (items or fallback)[:limit]


def build_visual_assets(
    company: dict[str, Any],
    sections: list[dict[str, Any]],
    guidance: dict[str, Any],
    scorecard: dict[str, Any],
) -> dict[str, Any]:
    name = value(company, "basic.name", "회사")
    problem = value(company, "business.problem", "핵심 고객 문제")
    solution = value(company, "business.solution", "해결 방식")
    product = value(company, "business.product", "제품·서비스")
    target = value(company, "business.targetCustomer", "목표 고객")
    differentiation = value(company, "business.differentiation", "차별화 요소")
    gtm = value(company, "market.goToMarket", "고객 확보 전략")
    metrics = value(company, "traction.metrics", "검증 지표")
    sales = value(company, "finance.salesPlan", "매출 계획")
    use_of_funds = value(company, "finance.useOfFunds", "제품 고도화, 고객 검증, 마케팅, 인증·자문")
    milestones = value(company, "finance.milestones", "요구사항 정리, MVP 고도화, 파일럿, 유료 전환 검증")
    job = value(company, "impact.jobCreation", "고용 창출 계획")
    social = value(company, "impact.socialValue", "고객 편익과 사회적 가치")

    budget_items = split_semantic_items(use_of_funds, ["제품 고도화", "고객 검증", "시장 진입", "전문가 자문"], 5)
    milestone_items = split_semantic_items(milestones, ["1단계 요구사항 확정", "2단계 MVP 고도화", "3단계 파일럿", "4단계 유료 전환 검증"], 5)
    kpi_items = split_semantic_items(metrics, ["고객 인터뷰 수", "파일럿 참여 수", "전환율", "재사용 의향"], 5)

    tables = [
        {
            "id": "budget_matrix",
            "title": "지원금 사용 및 산출물 매트릭스",
            "placement": "예산·집행계획 문항 직후",
            "columns": ["집행 항목", "사업 목표 연결", "관리 지표", "증빙자료"],
            "rows": [
                [
                    item,
                    f"{target} 검증과 {product} 완성도 개선",
                    kpi_items[index % len(kpi_items)],
                    "견적서, 계약서, 집행내역, 결과보고",
                ]
                for index, item in enumerate(budget_items)
            ],
        },
        {
            "id": "milestone_table",
            "title": "지원기간 실행 로드맵",
            "placement": "추진 일정 문항 본문",
            "columns": ["단계", "핵심 실행", "의사결정 기준", "제출 증빙"],
            "rows": [
                [
                    f"{index + 1}단계",
                    item,
                    "고객 반응과 산출물 품질 기준 통과",
                    "회의록, 산출물, 테스트 결과",
                ]
                for index, item in enumerate(milestone_items)
            ],
        },
        {
            "id": "kpi_matrix",
            "title": "성과지표·증빙 매트릭스",
            "placement": "기대효과 및 사업화 가능성 문항",
            "columns": ["성과 영역", "핵심 지표", "현재 근거", "보완 자료"],
            "rows": [
                ["시장 검증", kpi_items[0], metrics, "인터뷰·설문·파일럿 로그"],
                ["사업화", "유료 전환 및 매출 가능성", sales, "가격표, 매출 가정표, LOI"],
                ["고용·파급효과", "채용 및 사회적 가치", f"{job} / {social}", "채용계획, 수혜자 지표"],
            ],
        },
    ]

    infographics = [
        {
            "id": "logic_flow",
            "title": "심사 설득 흐름",
            "type": "flow",
            "placement": "사업 개요 첫 페이지",
            "nodes": [
                {"label": "고객 문제", "text": problem},
                {"label": "해결책", "text": solution},
                {"label": "제품·서비스", "text": product},
                {"label": "시장 진입", "text": gtm},
                {"label": "성과", "text": sales},
            ],
        },
        {
            "id": "positioning_map",
            "title": "차별화 포지셔닝",
            "type": "comparison",
            "placement": "경쟁우위 문항",
            "nodes": [
                {"label": "목표 고객", "text": target},
                {"label": "선택 기준", "text": "도입 편의성, 성과 측정, 지속 사용 가능성"},
                {"label": f"{name}의 우위", "text": differentiation},
            ],
        },
    ]

    if guidance.get("structureLines"):
        infographics.append(
            {
                "id": "page_architecture",
                "title": "페이지별 구성 아키텍처",
                "type": "outline",
                "placement": "제출 전 내부 검토용",
                "nodes": [
                    {"label": f"{index + 1}", "text": line}
                    for index, line in enumerate((guidance.get("structureLines") or [])[:8])
                ],
            }
        )

    weak_items = [item for item in scorecard.get("items", []) if item.get("status") != "strong"]
    if weak_items:
        tables.append(
            {
                "id": "review_gap_table",
                "title": "심사 관점 보완 우선순위",
                "placement": "제출 전 검토 페이지",
                "columns": ["심사 항목", "현재 점수", "보완 액션"],
                "rows": [
                    [item.get("label", ""), f"{item.get('score', 0)} / {item.get('weight', 0)}", item.get("action", "")]
                    for item in weak_items[:5]
                ],
            }
        )

    image_briefs = [
        {
            "id": "product_concept_image",
            "title": "제품·서비스 콘셉트 이미지",
            "placement": "제품 소개 문항",
            "model": AI_MODEL_ASSIGNMENTS["visualPlanning"]["imageModel"],
            "prompt": (
                f"Professional Korean government grant proposal visual for {name}. "
                f"Show {product} helping {target}. Dark consulting deck style, precise UI mockup, no fictional numbers, clean labels in Korean."
            ),
        },
        {
            "id": "customer_journey_image",
            "title": "고객 여정 인포그래픽 이미지",
            "placement": "문제·솔루션 연결 문항",
            "model": AI_MODEL_ASSIGNMENTS["visualPlanning"]["imageModel"],
            "prompt": (
                f"High-end consulting infographic showing customer journey from problem to solution for {target}. "
                f"Problem: {problem}. Solution: {solution}. Use restrained dark navy, graphite, gold accents, Korean labels."
            ),
        },
    ]

    return {
        "strategy": "정확한 숫자와 표는 구조화 데이터로 생성하고, 이미지 생성 모델은 제품 콘셉트와 고객 여정처럼 비데이터성 비주얼에만 사용합니다.",
        "tables": tables,
        "infographics": infographics,
        "imageBriefs": image_briefs,
    }


def quality_checks(
    company: dict[str, Any],
    sections: list[dict[str, Any]],
    document_insights: dict[str, Any] | None = None,
    format_validation: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    all_missing = sorted({field for section in sections for field in section.get("missingFields", [])})
    doc_count = len((document_insights or {}).get("documents", []))
    business_understanding = (document_insights or {}).get("businessUnderstanding") or {}
    understanding_coverage = business_understanding.get("coverage") or []
    understood_count = sum(1 for item in understanding_coverage if item.get("status") in {"strong", "partial"})
    blocked_extracts = (business_understanding.get("extractionCompleteness") or {}).get("blockedDocuments", 0)
    checks = [
        {
            "label": "회사 핵심 정보",
            "status": "ok" if value(company, "business.oneLine") and value(company, "business.product") else "needs_work",
            "message": "한 줄 소개와 제품·서비스가 명확하면 전체 문항의 일관성이 좋아집니다.",
        },
        {
            "label": "시장·경쟁 근거",
            "status": "ok" if value(company, "market.marketSize") and value(company, "market.competitors") else "needs_work",
            "message": "시장 규모, 경쟁사, 초기 고객군 근거를 추가하세요.",
        },
        {
            "label": "사업화 수치",
            "status": "ok" if value(company, "finance.salesPlan") and value(company, "traction.metrics") else "needs_work",
            "message": "매출 계획과 검증 지표가 있어야 심사위원이 실행 가능성을 판단할 수 있습니다.",
        },
        {
            "label": "업로드 문서 반영",
            "status": "ok" if doc_count else "needs_work",
            "message": f"업로드 문서 {doc_count}건을 초안 근거로 반영했습니다." if doc_count else "기존 사업계획서, 사업자등록증, 등기부등본 등을 올리면 사실 기반 초안이 됩니다.",
        },
        {
            "label": "법적 기본정보",
            "status": "ok" if value(company, "legal.businessNumber") or value(company, "legal.corporateNumber") else "needs_work",
            "message": "사업자등록번호 또는 법인등록번호가 확인되면 제출 서류와 계획서의 일관성이 좋아집니다.",
        },
    ]
    if all_missing:
        checks.append(
            {
                "label": "보완 필요 필드",
                "status": "needs_work",
                "message": ", ".join(label_for_field(field) for field in all_missing[:10]),
            }
        )
    if business_understanding:
        checks.append(
            {
                "label": "기존 사업계획서 심층 이해",
                "status": "ok" if understood_count >= 8 and not blocked_extracts else "needs_work",
                "message": (
                    f"사업 이해 항목 {understood_count}/{len(understanding_coverage)}개를 원문 근거로 구성했습니다. "
                    f"OCR/추출 보완 필요 문서 {blocked_extracts}건."
                ),
            }
        )
    if format_validation:
        failing = [item for item in format_validation if item.get("status") != "ok"]
        checks.append(
            {
                "label": "제출 형식 검증",
                "status": "ok" if not failing else "needs_work",
                "message": "양식 문항과 제출 브리프 기준 검증을 통과했습니다." if not failing else f"{len(failing)}개 형식 항목 확인이 필요합니다.",
            }
        )
    return checks


def evaluate_proposal_strength(
    company: dict[str, Any],
    sections: list[dict[str, Any]],
    document_insights: dict[str, Any] | None,
    format_validation: list[dict[str, str]],
) -> dict[str, Any]:
    def has_any_number(*texts: str) -> bool:
        return bool(re.search(r"\d", " ".join(texts)))

    doc_insights = document_insights or {}
    doc_count = len(doc_insights.get("documents", []) or [])
    fact_count = len(doc_insights.get("facts", []) or [])
    understanding = doc_insights.get("businessUnderstanding") or {}
    understanding_evidence_count = len(understanding.get("evidenceBank", []) or [])
    fact_count += min(10, understanding_evidence_count)
    validation_ok_ratio = (
        sum(1 for item in format_validation if item.get("status") == "ok") / len(format_validation)
        if format_validation
        else 0
    )
    categories = [
        (
            "문제·고객 선명도",
            12,
            [
                bool(value(company, "business.problem")),
                bool(value(company, "business.targetCustomer")),
                bool(value(company, "business.oneLine")),
                bool(value(company, "business.product")),
            ],
            "목표 고객, 반복 문제, 현재 대안의 한계, 제품·서비스 한 줄 정의를 더 구체화하세요.",
            "심사위원은 가장 먼저 '누구의 어떤 문제를 왜 지금 풀어야 하는가'를 확인합니다.",
        ),
        (
            "솔루션·차별성",
            14,
            [
                bool(value(company, "business.solution")),
                bool(value(company, "business.product")),
                bool(value(company, "business.differentiation")),
                bool(value(company, "market.competitors")),
                bool(value(company, "business.stage")),
            ],
            "해결 방식, 제품 구성, 경쟁 대안 대비 차별성, 현재 개발 단계를 연결하세요.",
            "좋은 아이템이라도 기존 대안 대비 왜 이 팀이 이길 수 있는지 보여야 합니다.",
        ),
        (
            "시장성·고객 확보",
            14,
            [
                bool(value(company, "market.marketSize")),
                bool(value(company, "market.trend")),
                bool(value(company, "market.competitors")),
                bool(value(company, "market.goToMarket")),
                bool(value(company, "traction.customers") or value(company, "traction.partnerships")),
            ],
            "시장 규모, 성장 근거, 경쟁 비교, 초기 고객 확보 채널과 파트너 후보를 보강하세요.",
            "지원사업은 기술 설명보다 시장 진입 가능성과 초기 고객 획득 경로를 강하게 봅니다.",
        ),
        (
            "사업화·수익성",
            14,
            [
                bool(value(company, "business.revenueModel")),
                bool(value(company, "finance.salesPlan")),
                bool(value(company, "traction.metrics")),
                has_any_number(value(company, "finance.salesPlan"), value(company, "traction.metrics")),
                bool(value(company, "market.goToMarket")),
            ],
            "수익모델, 가격/매출 가정, 유료 전환 지표, 고객 확보 비용 가정을 숫자로 보강하세요.",
            "매출 계획은 낙관적 문장보다 검증 가능한 전환 구조와 산출 근거가 중요합니다.",
        ),
        (
            "실행계획·예산 타당성",
            14,
            [
                bool(value(company, "finance.useOfFunds")),
                bool(value(company, "finance.milestones")),
                bool(value(company, "finance.fundingNeed")),
                bool(value(company, "finance.costPlan")),
                bool(value(company, "traction.metrics")),
            ],
            "지원금 사용처, 추진 일정, 필요 자금, 검증 지표를 연결하세요.",
            "지원금이 무엇을 바꾸고 어떤 산출물을 남기는지가 분명해야 예산 타당성이 생깁니다.",
        ),
        (
            "증빙자료와 정량 근거",
            12,
            [
                doc_count >= 1,
                fact_count >= 3,
                bool(value(company, "traction.metrics")),
                bool(value(company, "traction.customers") or value(company, "traction.pilotResults")),
                has_any_number(value(company, "traction.metrics"), value(company, "traction.pilotResults"), value(company, "finance.salesPlan")),
            ],
            "기존 사업계획서, 사업자등록증, 인터뷰, 파일럿, 고객·파트너 증빙을 업로드하세요.",
            "평가자는 주장보다 증빙을 신뢰합니다. 문서, 수치, 고객 반응을 본문 문장과 연결해야 합니다.",
        ),
        (
            "팀 역량과 신뢰도",
            10,
            [
                bool(value(company, "team.founder")),
                bool(value(company, "team.members")),
                bool(value(company, "team.advisors") or value(company, "team.hiringPlan")),
                bool(value(company, "legal.businessNumber") or value(company, "legal.corporateNumber")),
            ],
            "대표·팀 역량과 사업자/법인 기본정보를 보강하세요.",
            "팀 소개는 이력 나열보다 이 사업을 실제로 실행할 수 있는 역할·경험·보완계획이어야 합니다.",
        ),
        (
            "양식 준수와 제출 완성도",
            10,
            [
                validation_ok_ratio >= 0.8,
                any(item.get("label") == "문항 순서·제목" and item.get("status") == "ok" for item in format_validation),
                any(item.get("label") == "답변 누락" and item.get("status") == "ok" for item in format_validation),
                any(item.get("label") == "제출 형식 규칙" and item.get("status") == "ok" for item in format_validation),
            ],
            "문항 순서, 답변 누락, 페이지 분량, 제출 형식 규칙을 확인하세요.",
            "내용이 좋아도 양식 위반은 감점 또는 탈락 리스크가 되므로 마지막까지 별도 검증해야 합니다.",
        ),
    ]
    items: list[dict[str, Any]] = []
    total = 0
    for label, weight, signals, action, why_it_matters in categories:
        if not signals:
            ratio = 0
        else:
            ratio = sum(1 for signal in signals if signal) / len(signals)
        score = round(weight * ratio)
        total += score
        if ratio >= 0.85:
            status = "strong"
        elif ratio >= 0.55:
            status = "adequate"
        else:
            status = "needs_work"
        items.append(
            {
                "label": label,
                "score": score,
                "weight": weight,
                "status": status,
                "action": "현재 수준을 유지하고 실제 수치·증빙만 최종 확인하세요." if status == "strong" else action,
                "whyItMatters": why_it_matters,
                "signalsPassed": sum(1 for signal in signals if signal),
                "signalsTotal": len(signals),
            }
        )
    if total >= 85:
        readiness = "제출 준비도 높음"
    elif total >= 70:
        readiness = "제출 전 보완 권장"
    else:
        readiness = "핵심 보완 필요"
    priority_actions = [item["action"] for item in items if item["status"] != "strong"][:4]
    return {
        "score": total,
        "readiness": readiness,
        "items": items,
        "priorityActions": priority_actions,
        "criteriaVersion": "DSW-Grant-Readiness-2026.06",
        "message": "합격을 보장하는 점수는 아니지만, 심사위원 관점에서 시장성, 실행성, 증빙, 양식 준수 리스크를 빠르게 확인하기 위한 내부 점검표입니다.",
    }


def build_summary(
    company: dict[str, Any],
    grant_name: str,
    document_insights: dict[str, Any] | None = None,
    additional_notes: str = "",
    template_guidance: dict[str, Any] | None = None,
) -> str:
    name = value(company, "basic.name", "회사")
    one_line = value(company, "business.oneLine", "사업 아이템")
    target = value(company, "business.targetCustomer", "목표 고객")
    product = value(company, "business.product", "제품·서비스")
    use = value(company, "finance.useOfFunds", "지원금 사용 계획")
    summary = (
        f"{name}{topic_josa(name)} 핵심 고객을 다음과 같이 설정합니다: {target}. 이를 바탕으로 {one_line}{object_josa(one_line)} 추진합니다. "
        f"핵심 제품·서비스는 {product}입니다. 본 지원사업에서는 {sentence_text(use)}에 집중해 시장 검증과 사업화 성과를 만들겠습니다."
    )
    doc_count = len((document_insights or {}).get("documents", []))
    if doc_count:
        summary += f" 본 초안은 업로드된 회사 문서 {doc_count}건의 사실 정보와 기존 서술을 함께 반영했습니다."
    understanding = (document_insights or {}).get("businessUnderstanding") or {}
    covered = sum(1 for item in understanding.get("coverage", []) if item.get("status") in {"strong", "partial"})
    if covered:
        summary += f" 특히 기존 사업계획서 원문을 {covered}개 사업 이해 항목으로 재구성해 새 제출 양식의 문항별 근거로 연결했습니다."
    if additional_notes.strip():
        summary += " 사용자가 입력한 추가 의견도 이번 지원사업의 강조점으로 반영했습니다."
    template_guidance = template_guidance or {}
    if template_guidance.get("pageCount"):
        summary += f" 목표 분량은 {template_guidance['pageCount']}페이지 기준으로 설계했습니다."
    if template_guidance.get("focusPoints"):
        summary += " 중점 포인트는 작성전략과 핵심 문항 본문에 반영했습니다."
    return summary


def visual_assets_to_paragraphs(visual_assets: dict[str, Any]) -> list[tuple[str, str]]:
    paragraphs: list[tuple[str, str]] = []
    if not visual_assets:
        return paragraphs
    paragraphs.append(("heading", "표·인포그래픽 배치 설계"))
    if visual_assets.get("strategy"):
        paragraphs.append(("note", visual_assets["strategy"]))
    for table in visual_assets.get("tables", []):
        lines = [
            f"배치 위치: {table.get('placement', '')}",
            " | ".join(table.get("columns", [])),
        ]
        for row in table.get("rows", []):
            lines.append(" | ".join(str(cell) for cell in row))
        paragraphs.append(("heading", table.get("title", "표")))
        paragraphs.append(("note", "\n".join(lines)))
    for graphic in visual_assets.get("infographics", []):
        lines = [f"배치 위치: {graphic.get('placement', '')}", f"유형: {graphic.get('type', '')}"]
        for node in graphic.get("nodes", []):
            lines.append(f"{node.get('label', '')}: {node.get('text', '')}")
        paragraphs.append(("heading", graphic.get("title", "인포그래픽")))
        paragraphs.append(("note", "\n".join(lines)))
    for brief in visual_assets.get("imageBriefs", []):
        paragraphs.append(("heading", brief.get("title", "이미지 생성 브리프")))
        paragraphs.append(("note", f"배치 위치: {brief.get('placement', '')}\n모델: {brief.get('model', '')}\n프롬프트: {brief.get('prompt', '')}"))
    return paragraphs


def plan_to_paragraphs(plan: dict[str, Any]) -> list[tuple[str, str]]:
    paragraphs: list[tuple[str, str]] = [("title", plan.get("title", "사업계획서")), ("body", plan.get("summary", ""))]
    guidance = plan.get("templateGuidance") or {}
    brief_lines = []
    if guidance.get("pageCount"):
        brief_lines.append(f"목표 페이지 수: {guidance.get('pageCount')}")
    if guidance.get("structure"):
        brief_lines.append(f"전체 구성: {guidance.get('structure')}")
    if guidance.get("focusPoints"):
        brief_lines.append(f"주안점: {guidance.get('focusPoints')}")
    if guidance.get("formatRules"):
        brief_lines.append(f"제출 형식 규칙: {guidance.get('formatRules')}")
    if brief_lines:
        paragraphs.append(("heading", "작성 브리프"))
        paragraphs.append(("note", "\n".join(brief_lines)))
    manifest = plan.get("submissionFormatManifest") or {}
    if manifest:
        manifest_lines = [
            f"문서 형식: {manifest.get('documentFormat', '')}",
            f"기본 글꼴: {manifest.get('fontFamily', '')}",
            f"용지: {manifest.get('pageSize', '')}",
            f"목표/추정 페이지: {manifest.get('targetPages') or '미입력'} / 약 {manifest.get('estimatedPages', '')}p",
            f"양식 문항/초안 섹션: {manifest.get('templateQuestionCount', 0)} / {manifest.get('sectionCount', 0)}",
            f"검증 상태: {manifest.get('status', '')}",
        ]
        counts = manifest.get("visualAssetCounts") or {}
        if counts:
            manifest_lines.append(
                f"시각자료: 표 {counts.get('tables', 0)}개, 인포그래픽 {counts.get('infographics', 0)}개, 이미지 브리프 {counts.get('imageBriefs', 0)}개"
            )
        for checklist in manifest.get("checklist", []):
            manifest_lines.append(f"- {checklist}")
        paragraphs.append(("heading", "제출 양식 준수 매니페스트"))
        paragraphs.append(("note", "\n".join(manifest_lines)))
    paragraphs.extend(visual_assets_to_paragraphs(plan.get("visualAssets") or {}))
    for index, section in enumerate(plan.get("sections", []), start=1):
        paragraphs.append(("heading", f"{index}. {section.get('heading', '')}"))
        paragraphs.append(("body", section.get("content", "")))
        evidence = section.get("evidenceNeeded") or []
        if evidence:
            paragraphs.append(("note", "증빙자료: " + ", ".join(evidence)))
    validations = plan.get("formatValidation") or []
    if validations:
        paragraphs.append(("heading", "제출 형식 검증"))
        for item in validations:
            paragraphs.append(("note", f"{item.get('label')}: {item.get('message')}"))
    scorecard = plan.get("proposalScorecard") or {}
    if scorecard:
        paragraphs.append(("heading", "심사 준비도 점검"))
        paragraphs.append(("note", f"총점 {scorecard.get('score', 0)}점 / {scorecard.get('readiness', '')}\n{scorecard.get('message', '')}"))
        for item in scorecard.get("items", []):
            paragraphs.append(
                (
                    "note",
                    f"{item.get('label')}: {item.get('score')}/{item.get('weight')}점 - {item.get('action')}\n평가 관점: {item.get('whyItMatters', '')}",
                )
            )
    checks = plan.get("qualityChecks") or []
    if checks:
        paragraphs.append(("heading", "보완 체크리스트"))
        for check in checks:
            paragraphs.append(("note", f"{check.get('label')}: {check.get('message')}"))
    return [(kind, text) for kind, text in paragraphs if text and str(text).strip()]


def table_asset_html(table: dict[str, Any]) -> str:
    columns = table.get("columns", [])
    rows = table.get("rows", [])
    head = "".join(f"<th>{html.escape(str(column))}</th>" for column in columns)
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(cell))}</td>" for cell in row) + "</tr>"
        for row in rows
    )
    return (
        "<section class='visual-card'>"
        f"<h3>{html.escape(table.get('title','표'))}</h3>"
        f"<p class='caption'>배치 위치: {html.escape(table.get('placement',''))}</p>"
        f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
        "</section>"
    )


def infographic_asset_html(graphic: dict[str, Any]) -> str:
    nodes = graphic.get("nodes", [])
    node_html = "".join(
        f"<li><strong>{html.escape(str(node.get('label','')))}</strong><span>{html.escape(str(node.get('text','')))}</span></li>"
        for node in nodes
    )
    return (
        f"<section class='visual-card infographic {html.escape(graphic.get('type',''))}'>"
        f"<h3>{html.escape(graphic.get('title','인포그래픽'))}</h3>"
        f"<p class='caption'>배치 위치: {html.escape(graphic.get('placement',''))}</p>"
        f"<ol>{node_html}</ol>"
        "</section>"
    )


def image_brief_html(brief: dict[str, Any]) -> str:
    return (
        "<section class='visual-card image-brief'>"
        f"<h3>{html.escape(brief.get('title','이미지 생성 브리프'))}</h3>"
        f"<p class='caption'>배치 위치: {html.escape(brief.get('placement',''))} / 모델: {html.escape(brief.get('model',''))}</p>"
        f"<p>{html.escape(brief.get('prompt',''))}</p>"
        "</section>"
    )


def visual_assets_html(visual_assets: dict[str, Any]) -> str:
    if not visual_assets:
        return ""
    parts = ["<section class='visual-section'>"]
    if visual_assets.get("strategy"):
        parts.append(f"<p class='note'>{html.escape(visual_assets.get('strategy',''))}</p>")
    parts.extend(table_asset_html(table) for table in visual_assets.get("tables", []))
    parts.extend(infographic_asset_html(graphic) for graphic in visual_assets.get("infographics", []))
    parts.extend(image_brief_html(brief) for brief in visual_assets.get("imageBriefs", []))
    parts.append("</section>")
    return "\n".join(parts)


def create_html_export(plan: dict[str, Any], output_path: Path) -> None:
    body_parts = [
        "<!doctype html><html lang='ko'><head><meta charset='utf-8'>",
        "<title>사업계획서</title>",
        "<style>@font-face{font-family:'Pretendard Variable';src:url('/static/fonts/PretendardVariable.woff2') format('woff2');font-weight:45 920;font-style:normal;font-display:swap}body{font-family:'Pretendard Variable',Pretendard,'Apple SD Gothic Neo','Malgun Gothic',Arial,sans-serif;max-width:920px;margin:40px auto;line-height:1.72;color:#18212f}h1{font-size:28px}h2{font-size:20px;margin-top:30px}h3{margin:0 0 8px}p{white-space:pre-wrap}.note{color:#5b6472;background:#f4f7f9;padding:10px;border-left:4px solid #2f7d68}.visual-section{display:grid;gap:14px}.visual-card{border:1px solid #d9e0e7;border-radius:8px;padding:14px;background:#fbfcfd}.caption{margin:0 0 8px;color:#667085;font-size:12px}table{width:100%;border-collapse:collapse;font-size:13px}th,td{border:1px solid #d9e0e7;padding:8px;text-align:left;vertical-align:top}th{background:#eef3f5}.infographic ol{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:8px;padding:0;margin:0;list-style:none}.infographic li{border:1px solid #d9e0e7;border-radius:8px;padding:10px;background:#f6f8fa}.infographic strong{display:block;color:#173e35}.infographic span{display:block;color:#46515f;font-size:12px}</style>",
        "</head><body>",
        f"<h1>{html.escape(plan.get('title','사업계획서'))}</h1>",
        f"<p>{html.escape(plan.get('summary',''))}</p>",
    ]
    guidance = plan.get("templateGuidance") or {}
    if any(guidance.get(key) for key in ["pageCount", "structure", "focusPoints", "formatRules", "comments"]):
        body_parts.append("<h2>작성 브리프</h2>")
        brief = "\n".join(
            part
            for part in [
                f"목표 페이지 수: {guidance.get('pageCount')}" if guidance.get("pageCount") else "",
                f"전체 구성: {guidance.get('structure')}" if guidance.get("structure") else "",
                f"주안점: {guidance.get('focusPoints')}" if guidance.get("focusPoints") else "",
                f"제출 형식 규칙: {guidance.get('formatRules')}" if guidance.get("formatRules") else "",
                f"작성 코멘트: {guidance.get('comments')}" if guidance.get("comments") else "",
            ]
            if part
        )
        body_parts.append(f"<p class='note'>{html.escape(brief)}</p>")
    manifest = plan.get("submissionFormatManifest") or {}
    if manifest:
        counts = manifest.get("visualAssetCounts") or {}
        manifest_lines = [
            f"문서 형식: {manifest.get('documentFormat', '')}",
            f"기본 글꼴: {manifest.get('fontFamily', '')}",
            f"용지: {manifest.get('pageSize', '')}",
            f"목표/추정 페이지: {manifest.get('targetPages') or '미입력'} / 약 {manifest.get('estimatedPages', '')}p",
            f"양식 문항/초안 섹션: {manifest.get('templateQuestionCount', 0)} / {manifest.get('sectionCount', 0)}",
            f"시각자료: 표 {counts.get('tables', 0)}개, 인포그래픽 {counts.get('infographics', 0)}개, 이미지 브리프 {counts.get('imageBriefs', 0)}개",
            f"검증 상태: {manifest.get('status', '')}",
        ]
        manifest_lines.extend(f"- {item}" for item in manifest.get("checklist", []))
        body_parts.append("<h2>제출 양식 준수 매니페스트</h2>")
        body_parts.append(f"<p class='note'>{html.escape(chr(10).join(manifest_lines))}</p>")
    visual_html = visual_assets_html(plan.get("visualAssets") or {})
    if visual_html:
        body_parts.append("<h2>표·인포그래픽 배치 설계</h2>")
        body_parts.append(visual_html)
    for i, section in enumerate(plan.get("sections", []), start=1):
        body_parts.append(f"<h2>{i}. {html.escape(section.get('heading',''))}</h2>")
        body_parts.append(f"<p>{html.escape(section.get('content',''))}</p>")
        evidence = section.get("evidenceNeeded") or []
        if evidence:
            body_parts.append(f"<p class='note'>증빙자료: {html.escape(', '.join(evidence))}</p>")
    validations = plan.get("formatValidation") or []
    if validations:
        body_parts.append("<h2>제출 형식 검증</h2>")
        for item in validations:
            body_parts.append(f"<p class='note'>{html.escape(item.get('label',''))}: {html.escape(item.get('message',''))}</p>")
    scorecard = plan.get("proposalScorecard") or {}
    if scorecard:
        body_parts.append("<h2>심사 준비도 점검</h2>")
        body_parts.append(
            f"<p class='note'>총점 {html.escape(str(scorecard.get('score', 0)))}점 / {html.escape(scorecard.get('readiness',''))}<br>{html.escape(scorecard.get('message',''))}</p>"
        )
        for item in scorecard.get("items", []):
            body_parts.append(
                f"<p class='note'>{html.escape(item.get('label',''))}: {html.escape(str(item.get('score','')))} / {html.escape(str(item.get('weight','')))}점<br>{html.escape(item.get('action',''))}<br>평가 관점: {html.escape(item.get('whyItMatters',''))}</p>"
            )
    body_parts.append("</body></html>")
    output_path.write_text("\n".join(body_parts), encoding="utf-8")


def xml_escape(value: str) -> str:
    return html.escape(value, quote=True)


def paragraph_xml(text: str, style: str, pid: int) -> str:
    char_pr = {"title": 2, "heading": 1, "note": 3}.get(style, 0)
    para_pr = {"title": 1, "heading": 2, "note": 3}.get(style, 0)
    runs = []
    for line_index, line in enumerate(str(text).splitlines() or [""]):
        if line_index:
            runs.append('<hp:run charPrIDRef="%s"><hp:lineBreak/></hp:run>' % char_pr)
        runs.append(f'<hp:run charPrIDRef="{char_pr}"><hp:t>{xml_escape(line)}</hp:t></hp:run>')
    return (
        f'<hp:p id="{pid}" paraPrIDRef="{para_pr}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
        + "".join(runs)
        + '<hp:linesegarray><hp:lineseg textpos="0" vertpos="0" vertsize="1000" textheight="1000" baseline="850" spacing="600" horzpos="0" horzsize="42520" flags="393216"/></hp:linesegarray>'
        + "</hp:p>"
    )


def create_hwpx(plan: dict[str, Any], output_path: Path) -> None:
    paragraphs = plan_to_paragraphs(plan)
    section_body = "\n".join(paragraph_xml(text, kind, index) for index, (kind, text) in enumerate(paragraphs, start=1))
    section_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<hp:sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head">
  <hp:secPr id="0" textDirection="HORIZONTAL" spaceColumns="0" tabStop="8000">
    <hp:pagePr landscape="0" width="59528" height="84188" gutterType="LEFT_ONLY">
      <hp:margin header="4252" footer="4252" gutter="0" left="8504" right="8504" top="5668" bottom="4252"/>
    </hp:pagePr>
    <hp:footNotePr/>
    <hp:endNotePr/>
    <hp:pageBorderFill type="BOTH" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0"/>
  </hp:secPr>
  {section_body}
</hp:sec>
'''
    header_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core">
  <hh:beginNum page="1" footnote="1" endnote="1" pic="1" tbl="1" equation="1"/>
  <hh:refList>
    <hh:fontfaces itemCnt="1">
      <hh:fontface lang="KO" fontCnt="1"><hh:font id="0" type="TTF" face="Pretendard Variable"/></hh:fontface>
    </hh:fontfaces>
    <hh:borderFills itemCnt="1">
      <hh:borderFill id="1" threeD="0" shadow="0" centerLine="NONE">
        <hh:slash type="NONE" Crooked="0" isCounter="0"/>
        <hh:backSlash type="NONE" Crooked="0" isCounter="0"/>
        <hh:leftBorder type="NONE" width="0.1 mm" color="#000000"/>
        <hh:rightBorder type="NONE" width="0.1 mm" color="#000000"/>
        <hh:topBorder type="NONE" width="0.1 mm" color="#000000"/>
        <hh:bottomBorder type="NONE" width="0.1 mm" color="#000000"/>
        <hh:diagonal type="NONE" width="0.1 mm" color="#000000"/>
        <hh:fillBrush><hc:winBrush faceColor="#FFFFFF" hatchColor="#000000"/></hh:fillBrush>
      </hh:borderFill>
    </hh:borderFills>
    <hh:charProperties itemCnt="4">
      <hh:charPr id="0" height="1000" textColor="#202733"><hh:fontRef hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/></hh:charPr>
      <hh:charPr id="1" height="1250" bold="1" textColor="#173E35"><hh:fontRef hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/></hh:charPr>
      <hh:charPr id="2" height="1700" bold="1" textColor="#0D2330"><hh:fontRef hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/></hh:charPr>
      <hh:charPr id="3" height="900" textColor="#5A6372"><hh:fontRef hangul="0" latin="0" hanja="0" japanese="0" other="0" symbol="0" user="0"/></hh:charPr>
    </hh:charProperties>
    <hh:paraProperties itemCnt="4">
      <hh:paraPr id="0" lineSpacingType="PERCENT" lineSpacing="160" align="JUSTIFY"/>
      <hh:paraPr id="1" lineSpacingType="PERCENT" lineSpacing="150" align="CENTER"/>
      <hh:paraPr id="2" lineSpacingType="PERCENT" lineSpacing="150" align="LEFT"/>
      <hh:paraPr id="3" lineSpacingType="PERCENT" lineSpacing="140" align="LEFT"/>
    </hh:paraProperties>
    <hh:styles itemCnt="1"><hh:style id="0" type="PARA" name="바탕글" engName="Normal" paraPrIDRef="0" charPrIDRef="0" nextStyleIDRef="0" langID="1042" lockForm="0"/></hh:styles>
  </hh:refList>
  <hh:compatibleDocument targetProgram="HWP201X"/>
  <hh:docOption/>
</hh:head>
'''
    content_hpf = '''<?xml version="1.0" encoding="UTF-8"?>
<opf:package xmlns:opf="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
  <opf:metadata><opf:title>사업계획서</opf:title><opf:language>ko</opf:language></opf:metadata>
  <opf:manifest>
    <opf:item id="header" href="header.xml" media-type="application/xml"/>
    <opf:item id="section0" href="section0.xml" media-type="application/xml"/>
    <opf:item id="pretendard-variable" href="Fonts/PretendardVariable.woff2" media-type="font/woff2"/>
  </opf:manifest>
  <opf:spine><opf:itemref idref="section0"/></opf:spine>
</opf:package>
'''
    container_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/hwpml-package+xml"/></rootfiles>
</container>
'''
    version_xml = '''<?xml version="1.0" encoding="UTF-8"?><version app="David Strategy Works" hwpx="1.0"/>'''

    with zipfile.ZipFile(output_path, "w") as archive:
        archive.writestr("mimetype", "application/hwp+zip", compress_type=zipfile.ZIP_STORED)
        archive.writestr("version.xml", version_xml, compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr("META-INF/container.xml", container_xml, compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr("Contents/content.hpf", content_hpf, compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr("Contents/header.xml", header_xml, compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr("Contents/section0.xml", section_xml, compress_type=zipfile.ZIP_DEFLATED)
        font_path = STATIC_DIR / "fonts" / "PretendardVariable.woff2"
        if font_path.exists():
            archive.write(font_path, "Contents/Fonts/PretendardVariable.woff2", compress_type=zipfile.ZIP_DEFLATED)


def create_template_preservation_files(plan: dict[str, Any], base: str, generated_hwpx_path: Path) -> list[dict[str, str]]:
    source = plan.get("templateSource") or {}
    stored_name = source.get("storedName", "")
    if not stored_name:
        return []
    source_path = (TEMPLATE_DIR / stored_name).resolve()
    template_root = TEMPLATE_DIR.resolve()
    if template_root != source_path and template_root not in source_path.parents:
        return []
    if not source_path.exists() or not source_path.is_file():
        return []

    original_ext = source_path.suffix or ".bin"
    original_export_path = EXPORT_DIR / f"{base}-original-template{original_ext}"
    mapping_path = EXPORT_DIR / f"{base}-template-answer-map.json"
    package_path = EXPORT_DIR / f"{base}-template-preservation-package.zip"

    shutil.copy2(source_path, original_export_path)
    mapping = {
        "preservationMode": "original_template_attached_with_answer_mapping",
        "limitation": "1차 구현은 원본 양식을 변형하지 않고 보존하며, 생성 답변과 문항 매핑을 함께 제공합니다. 표 셀 단위 자동 삽입은 HWPX XML 구조별 추가 구현이 필요합니다.",
        "templateSource": source,
        "generatedHwpx": generated_hwpx_path.name,
        "answerMap": [
            {
                "sectionId": section.get("id", ""),
                "question": section.get("heading", ""),
                "category": section.get("category", ""),
                "evaluationFocus": section.get("evaluationFocus", ""),
                "answerPreview": clean_text(section.get("content", ""))[:500],
                "evidenceNeeded": section.get("evidenceNeeded", []),
            }
            for section in plan.get("sections", [])
        ],
        "createdAt": dt.datetime.now().isoformat(timespec="seconds"),
    }
    mapping_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(original_export_path, f"original/{original_export_path.name}")
        archive.write(generated_hwpx_path, f"generated/{generated_hwpx_path.name}")
        archive.write(mapping_path, f"mapping/{mapping_path.name}")
    return [
        {"label": "원본 제출양식", "url": f"/exports/{original_export_path.name}", "filename": original_export_path.name},
        {"label": "양식-답변 매핑 JSON", "url": f"/exports/{mapping_path.name}", "filename": mapping_path.name},
        {"label": "양식 보존 패키지 ZIP", "url": f"/exports/{package_path.name}", "filename": package_path.name},
    ]


def create_export(plan: dict[str, Any]) -> dict[str, Any]:
    ensure_dirs()
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    digest = hashlib.sha1(json.dumps(plan, ensure_ascii=False).encode("utf-8")).hexdigest()[:8]
    company_slug = re.sub(r"[^0-9A-Za-z가-힣_-]+", "-", plan.get("companyName", "company")).strip("-") or "company"
    base = f"{company_slug}-business-plan-{stamp}-{digest}"
    hwpx_path = EXPORT_DIR / f"{base}.hwpx"
    html_path = EXPORT_DIR / f"{base}.html"
    json_path = EXPORT_DIR / f"{base}.json"
    create_hwpx(plan, hwpx_path)
    create_html_export(plan, html_path)
    json_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    files = [
        {"label": "HWPX 사업계획서", "url": f"/exports/{hwpx_path.name}", "filename": hwpx_path.name},
        {"label": "검토용 HTML", "url": f"/exports/{html_path.name}", "filename": html_path.name},
        {"label": "초안 데이터 JSON", "url": f"/exports/{json_path.name}", "filename": json_path.name},
    ]
    files.extend(create_template_preservation_files(plan, base, hwpx_path))
    return {
        "files": files,
        "createdAt": dt.datetime.now().isoformat(timespec="seconds"),
    }


class BriwellHandler(SimpleHTTPRequestHandler):
    server_version = "DavidStrategyWorks/0.1"

    def log_message(self, format: str, *args: Any) -> None:
        log_line(format % args)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        try:
            if path == "/api/health":
                return self.send_json({"ok": True, "time": dt.datetime.now().isoformat(timespec="seconds")})
            if path == "/api/ai/settings":
                return self.send_json(ai_settings_payload())
            if path == "/api/grant-dataset":
                return self.send_json(read_grant_success_dataset())
            if path == "/api/versions":
                query = urllib.parse.parse_qs(parsed.query)
                profile_id = (query.get("profileId") or ["default-workspace"])[0]
                return self.send_json(list_draft_versions(profile_id))
            if path.startswith("/api/versions/"):
                parts = path[len("/api/versions/") :].split("/")
                if len(parts) == 3 and parts[2] == "export":
                    try:
                        return self.send_json(export_draft_version(parts[0], parts[1]))
                    except FileNotFoundError as exc:
                        return self.send_json({"error": str(exc)}, status=404)
                if len(parts) != 2:
                    return self.send_json({"error": "초안 버전 경로가 올바르지 않습니다."}, status=400)
                try:
                    return self.send_json(get_draft_version(parts[0], parts[1]))
                except FileNotFoundError as exc:
                    return self.send_json({"error": str(exc)}, status=404)
            if path == "/api/profiles":
                return self.send_json(list_profiles())
            if path.startswith("/api/profiles/"):
                profile_id = path[len("/api/profiles/") :]
                profile = get_profile(profile_id)
                if profile is None:
                    return self.send_json({"error": "프로필을 찾을 수 없습니다."}, status=404)
                return self.send_json(profile)
            if path == "/api/company":
                return self.send_json(read_active_company())
            if path.startswith("/exports/"):
                return self.serve_file(EXPORT_DIR, path[len("/exports/") :])
            if path.startswith("/static/"):
                return self.serve_file(STATIC_DIR, path[len("/static/") :])
            if path == "/" or path == "/index.html":
                return self.serve_file(STATIC_DIR, "index.html")
            self.send_error(404, "Not found")
        except Exception as exc:
            self.send_error_json(500, exc)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)
        try:
            payload = self.read_json()
            if path == "/api/company":
                company = write_company(payload)
                return self.send_json(company)
            if path == "/api/profiles":
                return self.send_json(save_profile(payload))
            if path == "/api/versions":
                return self.send_json(save_draft_version(payload))
            if path == "/api/versions/update":
                try:
                    return self.send_json(update_draft_version(payload))
                except FileNotFoundError as exc:
                    return self.send_json({"error": str(exc)}, status=404)
            if path == "/api/versions/revise":
                return self.send_json(revise_draft_version(payload))
            if path == "/api/analyze":
                filename = payload.get("filename", "")
                raw = base64.b64decode(payload.get("contentBase64", "") or b"")
                pasted = payload.get("text", "")
                template_source = store_template_source(filename, raw, pasted)
                text, notes = extract_text(filename, raw, pasted)
                return self.send_json(analyze_template(filename, text, notes, template_source))
            if path == "/api/documents/analyze":
                return self.send_json(analyze_documents(payload.get("documents") or [], payload.get("notes", "")))
            if path == "/api/generate":
                company = deep_merge(DEFAULT_COMPANY, payload.get("company") or read_active_company())
                template = payload.get("template") or {}
                options = payload.get("options") or {}
                if payload.get("documentInsights") is not None:
                    options["documentInsights"] = payload.get("documentInsights")
                if payload.get("additionalNotes") is not None:
                    options["additionalNotes"] = payload.get("additionalNotes")
                if payload.get("templateGuidance") is not None:
                    options["templateGuidance"] = payload.get("templateGuidance")
                return self.send_json(generate_plan(company, template, options))
            if path == "/api/export/hwpx":
                plan = payload.get("plan") or payload
                return self.send_json(create_export(plan))
            self.send_error(404, "Not found")
        except Exception as exc:
            self.send_error_json(500, exc)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        data = self.rfile.read(length)
        if not data:
            return {}
        return json.loads(decode_text(data))

    def send_json(self, payload: Any, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, status: int, exc: Exception) -> None:
        traceback.print_exc()
        self.send_json({"error": str(exc), "type": exc.__class__.__name__}, status=status)

    def serve_file(self, root: Path, relative: str) -> None:
        target = (root / relative).resolve()
        root_resolved = root.resolve()
        if root_resolved != target and root_resolved not in target.parents:
            self.send_error(403, "Forbidden")
            return
        if not target.exists() or not target.is_file():
            self.send_error(404, "Not found")
            return
        content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
        if target.suffix.lower() == ".hwpx":
            content_type = "application/hwp+zip"
        data = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        if target.parent == EXPORT_DIR:
            self.send_header("Content-Disposition", f'attachment; filename="{target.name}"')
        self.end_headers()
        self.wfile.write(data)


def main() -> None:
    load_env_file()
    parser = argparse.ArgumentParser(description="David Strategy Works local grant proposal writer")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8765")))
    args = parser.parse_args()
    ensure_dirs()
    server = ThreadingHTTPServer((args.host, args.port), BriwellHandler)
    log_line(f"David Strategy Works running at http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log_line("Stopping server")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
