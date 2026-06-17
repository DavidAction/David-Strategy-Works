# Architecture

## Runtime

- Python standard library HTTP server
- Static HTML/CSS/JS frontend
- No build step required
- Local file persistence under `data/` and `exports/`

## Data Flow

1. Company profile is edited in the browser.
2. User uploads company evidence documents.
3. Server extracts text and facts, preserves existing business-plan source text, builds a structured business-understanding model, then proposes company profile patches.
4. User uploads grant template or notice.
5. Server extracts template questions, requirements, and template source metadata.
6. User enters submission brief: page count, structure, focus points, format rules, comments.
7. Server generates a local draft, then optionally routes through Gemini, GPT, and Claude if API keys exist.
8. Server attaches section-level source traceability and unsupported-claim audit results.
9. Server attaches evidence-lock, consultant-review, AI-cost, secure-transfer, and submission-fidelity reports.
10. The generated draft is auto-saved as a version.
11. User can add revision comments against the current draft or a selected version.
12. Server creates a new revised plan version from those comments.
13. Each version can be opened for editing, updated, and exported separately.
14. Server exports HWPX, review HTML, JSON data, SVG visual assets, and template-preservation artifacts.

## Core Server Functions

- `extract_text`: file text extraction and OCR hints
- `analyze_documents`: company evidence analysis
- `build_document_library_summary`: multi-document evidence scoring, coverage, duplicate detection, and extraction quality summary
- `build_business_understanding`: reconstructs uploaded business plans into problem, customer, solution, market, traction, business model, budget, team, roadmap, impact, and risk evidence banks
- `build_business_plan_corpus`: retains extracted source text for AI drafting context while tracking truncation and extraction completeness
- `analyze_template`: grant form/question analysis
- `generate_plan`: business plan generation orchestrator
- `attach_grounding_audit`: adds source-evidence traceability and unsupported-claim checks after local or AI drafting
- `build_evidence_lock_report`: converts traceability and unsupported-claim checks into a submission gate
- `build_consultant_review`: creates a senior-review style readiness dashboard and fix list
- `build_submission_fidelity_report`: analyzes uploaded HWPX source package readiness for form filling
- `create_visual_asset_files`: renders proposal tables and infographics as deterministic SVG assets
- `ai_provider_health`: reports configured AI provider/model readiness
- `revise_plan_with_comments`: comment-driven revision generator
- `save_draft_version` / `update_draft_version` / `export_draft_version`: version lifecycle APIs
- `validate_plan_format`: submission format checks
- `evaluate_proposal_strength`: grant-readiness scorecard
- `create_export`: output package generation

## Persistence

- `data/profiles.json`: company workspaces
- `data/company.json`: active company compatibility cache
- `data/templates/`: uploaded original grant templates
- `data/datasets/`: grant success criteria dataset
- `data/versions/`: draft edit/version snapshots
- `exports/`: generated deliverables

## Extension Points

- Add true cell-level HWPX form filling in `create_template_preservation_files`.
- Add OCR engines in `extract_text` and `ocr_image_bytes`.
- Add authenticated multi-user persistence later.
- Replace local JSON storage with database when productized.
