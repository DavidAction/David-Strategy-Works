# Quality Upgrade Audit

Date: 2026-06-17

This audit looks at David Strategy Works as a proposal-quality operating system, not only as a working local app.

## Current Class

Current maturity: advanced local MVP / production-hardening candidate.

Strong points:

- Multi-company workspace and version workflow are already in place.
- Uploaded business plans are analyzed into a structured business-understanding layer rather than only summarized.
- Evidence traceability, unsupported-claim audit, judge questions, rejection risks, and security reports are generated.
- HWPX, HTML, JSON, deterministic visual assets, and original-template preservation packages are exported.
- Proposal benchmarks now require strong score, evidence-lock status, required phrases, and zero high-risk unsupported numeric claims.
- Export safety gates, retention reporting, and guarded cleanup are available for local operations.
- Model routing is designed around Gemini for Korean drafting, GPT for final polish/format validation, and Claude Opus for final red-team review.

Main class gap:

The product can already create a strong strategic draft with evidence gates and repeatable local benchmarks. The remaining class gap is exact visible insertion into every government HWPX table/cell layout, real accepted/rejected proposal evaluation data, and live-provider QA with production API keys.

## Highest-Impact Upgrades

1. Submission Fidelity Engine

Build true HWPX XML table/cell mapping for uploaded government forms.

Why it matters:
Government forms often fail on format fidelity before content is even judged. Exact cell-level insertion is the biggest difference between a useful draft tool and a submission-grade system.

Acceptance criteria:

- Parse uploaded HWPX package structure.
- Detect sections, tables, cells, placeholders, and fixed labels.
- Map each generated answer to a specific cell or paragraph node.
- Preserve original styles, margins, captions, and table widths.
- Export a filled HWPX that opens cleanly in Hancom Office.

2. Evidence-Locked Drafting

Move from evidence-aware drafting to evidence-locked drafting.

Why it matters:
The current system flags unsupported claims after generation. The next level is to force every important claim to come from an evidence object before the sentence is written.

Acceptance criteria:

- Every section gets a required evidence plan before drafting.
- Quantitative claims require a source fact or are marked as assumptions.
- Generated sections include hidden or sidecar source anchors.
- Unsupported high-impact claims are blocked before export unless approved.

3. Accepted/Rejected Proposal Benchmark

Create a small evaluation dataset with accepted and rejected proposal examples.

Why it matters:
The only objective way to improve selection probability is to compare generated drafts against actual selection patterns.

Acceptance criteria:

- At least 20 accepted and 20 rejected/redacted samples.
- Rubric labels for problem clarity, feasibility, market evidence, budget logic, team fit, impact, and format compliance.
- Automated scoring before and after each model/prompt change.
- Regression threshold that blocks weaker generation prompts.

4. Visual Asset Production Pipeline

Turn visual briefs into actual proposal-ready tables, infographics, and images.

Why it matters:
Government proposals often benefit from simple, evidence-based diagrams: market entry flow, milestone roadmap, budget allocation, customer validation funnel, and impact logic.

Acceptance criteria:

- Generate chart/table specs from plan data.
- Render PNG/SVG assets with deterministic local code for charts.
- Use image models only where a generated visual is truly helpful.
- Insert visual assets into HTML and HWPX exports with captions and source notes.

5. Real AI Orchestration QA

Run real API-key integration tests across Gemini, OpenAI, and Anthropic.

Why it matters:
The routing strategy is correct only if the actual API responses preserve JSON structure, Korean quality, cost limits, and latency targets.

Acceptance criteria:

- Health check endpoint for each provider and configured model.
- Per-stage timeout, retry, fallback, and structured-output validation.
- Token/cost ledger per generated draft.
- Red-team review always uses Anthropic `claude-opus-4-8`.

6. Consultant-Grade Review Mode

Add a final review workspace that behaves like a senior consultant reviewing before submission.

Why it matters:
Users do not only need a draft. They need to know what will make the draft lose and what must be fixed first.

Acceptance criteria:

- One-page readiness dashboard.
- Top 10 fix list by expected selection impact.
- Reviewer comments by section.
- Before/after revision diff with reason codes.
- Final submission checklist.

7. Security And Workspace Hardening

Move from local-first safety guidance to enforceable workspace controls.

Why it matters:
Business registrations, registry extracts, financials, contracts, and LOIs are sensitive. A professional consulting system needs stronger default protections.

Acceptance criteria:

- Optional local workspace password.
- Encrypted local data folder option.
- Sensitive document confirmation before external AI transfer.
- Export cleanup and retention policy.
- Separate client/workspace boundaries.

## Immediate Standards Now Added

- `tools/quality_smoke.py` provides a repeatable local regression test for document analysis, draft generation, revision, export, unsafe-export blocking, HWPX package structure, visual media manifest attachment, and placeholder-based HWPX filling.
- `tools/benchmark_proposals.py` now validates deterministic proposal quality across healthcare, manufacturing, and content-export cases. Each case must meet score thresholds, required phrases, locked evidence status, and zero high-risk unsupported numeric claims.
- Claude Opus 4.8 API ID is standardized to Anthropic's actual ID: `claude-opus-4-8`.
- Submission fidelity reporting now analyzes uploaded HWPX packages and exports a fidelity JSON report.
- Export now creates deterministic SVG files for tables and infographics and attaches package-level SVG media plus a visual-assets manifest inside generated HWPX files.
- Drafts now include evidence-lock, consultant-review, estimated AI-cost, and secure-transfer policy reports.
- `/api/ai/health` reports configured AI provider/model readiness, with optional live checks through `?live=1`.
- `tools/ocr_check.py` and `tools/install_ocr_windows.ps1` provide OCR readiness checks and Windows installation guidance for Tesseract/Poppler.
- `tools/import_hwpx_samples.py` creates a private real-template probe library under ignored `data/templates/real_samples/`.
- `tools/export_retention.py` and `/api/exports/retention` report export cleanup candidates; deletion requires an explicit confirmation token.

## Remaining Advanced Work

The current HWPX fill engine creates a review-grade filled-template attempt when a source HWPX is available. True production-grade government-form filling still requires per-template table/cell anchoring, style-preserving insertion, and Hancom Office visual QA for each form family.

Run:

```powershell
python tools\quality_smoke.py
python tools\benchmark_proposals.py
python tools\export_retention.py
```

## Recommended Next Sequence

1. Collect redacted real government HWPX templates and run `tools/import_hwpx_samples.py` against each one.
2. Implement semantic HWPX table/cell anchoring for forms without explicit placeholders.
3. Run live Gemini/GPT/Claude integration tests once production API keys are available.
4. Build accepted/rejected proposal evaluation dataset with at least 20 accepted and 20 rejected cases.
5. Add visible HWPX drawing-object insertion QA across Hancom Office versions.
6. Add encrypted local data storage for sensitive client workspaces.
