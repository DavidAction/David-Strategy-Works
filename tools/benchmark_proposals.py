from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import server  # noqa: E402


def load_cases(paths: list[Path]) -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            cases.extend(data)
        else:
            cases.append(data)
    return cases


def evaluate_case(case: dict[str, object]) -> dict[str, object]:
    company = case.get("company") or {}
    template = case.get("template") or {}
    options = case.get("options") or {}
    expected = case.get("expected") or {}
    plan = server.generate_plan(company, template, options)
    scorecard = plan.get("proposalScorecard") or {}
    evidence_lock = plan.get("evidenceLockReport") or {}
    unsupported = plan.get("unsupportedClaimAudit") or {}
    total_score = int(scorecard.get("score") or scorecard.get("totalScore") or 0)
    min_score = int(expected.get("minScore") or 0)
    max_high_risk_claims = int(expected.get("maxHighRiskClaims", 0))
    required_lock_status = str(expected.get("requiredEvidenceLockStatus", "locked"))
    required_phrases = [str(item) for item in expected.get("requiredPhrases", [])]
    body = "\n".join(section.get("content", "") for section in plan.get("sections", []))
    searchable = body + "\n" + json.dumps(company, ensure_ascii=False) + "\n" + json.dumps(plan, ensure_ascii=False)[:20000]
    missing_phrases = [phrase for phrase in required_phrases if phrase and phrase not in searchable]
    high_risk_claims = int(unsupported.get("highRiskClaims", 0) or 0)
    lock_status = str(evidence_lock.get("status", ""))
    score_ok = total_score >= min_score
    lock_ok = not required_lock_status or lock_status == required_lock_status
    risk_ok = high_risk_claims <= max_high_risk_claims
    passed = score_ok and lock_ok and risk_ok and not missing_phrases
    return {
        "name": case.get("name", "unnamed"),
        "passed": passed,
        "totalScore": total_score,
        "minScore": min_score,
        "sectionCount": len(plan.get("sections", [])),
        "evidenceLockStatus": lock_status,
        "requiredEvidenceLockStatus": required_lock_status,
        "lockOk": lock_ok,
        "highRiskClaims": high_risk_claims,
        "maxHighRiskClaims": max_high_risk_claims,
        "riskOk": risk_ok,
        "missingPhrases": missing_phrases,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic proposal-quality benchmark cases.")
    parser.add_argument("cases", nargs="*", help="Case JSON files. Defaults to benchmarks/proposals/*.json.")
    args = parser.parse_args()

    server.load_env_file()
    paths = [Path(item).expanduser().resolve() for item in args.cases]
    if not paths:
        paths = sorted((ROOT / "benchmarks" / "proposals").glob("*.json"))
    cases = load_cases(paths) if paths else []
    results = [evaluate_case(case) for case in cases]
    summary = {
        "caseCount": len(results),
        "passed": sum(1 for item in results if item["passed"]),
        "failed": sum(1 for item in results if not item["passed"]),
        "results": results,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
