# Quality Upgrade Audit

Date: 2026-06-17

This audit looks at David Strategy Works as a proposal-quality operating system, not only as a working local app.

## Current Class

Current maturity: advanced local MVP / early production candidate.

Strong points:

- Multi-company workspace and version workflow are already in place.
- Uploaded business plans are analyzed into a structured business-understanding layer rather than only summarized.
- Evidence traceability, unsupported-claim audit, judge questions, rejection risks, and security reports are generated.
- HWPX, HTML, JSON, and original-template preservation packages are exported.
- Model routing is designed around Gemini for Korean drafting, GPT for final polish/format validation, and Claude Opus for final red-team review.

Main class gap:

The product can already create a strong strategic draft, but it does not yet guarantee exact insertion into every government HWPX table/cell layout, automated real-model benchmark quality, or generated visual assets embedded into the final HWPX.

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

- `tools/quality_smoke.py` provides a repeatable local regression test for document analysis, draft generation, revision, export, and HWPX package structure.
- Claude Opus 4.8 API ID is standardized to Anthropic's actual ID: `claude-opus-4-8`.

Run:

```powershell
python tools\quality_smoke.py
```

## Recommended Next Sequence

1. Implement HWPX table/cell parser and exact fill engine.
2. Add model health checks and real API integration tests.
3. Add token/cost ledger and provider fallback report.
4. Add visual asset rendering and HWPX asset insertion.
5. Build accepted/rejected proposal evaluation dataset.
6. Add consultant-grade final review mode.
7. Add workspace password/encryption and API transfer confirmation.
