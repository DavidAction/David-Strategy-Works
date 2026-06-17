# Architecture

## Runtime

- Python standard library HTTP server
- Static HTML/CSS/JS frontend
- No build step required
- Local file persistence under `data/` and `exports/`

## Data Flow

1. Company profile is edited in the browser.
2. User uploads company evidence documents.
3. Server extracts text and facts, then proposes company profile patches.
4. User uploads grant template or notice.
5. Server extracts template questions, requirements, and template source metadata.
6. User enters submission brief: page count, structure, focus points, format rules, comments.
7. Server generates a local draft, then optionally routes through Gemini, GPT, and Claude if API keys exist.
8. Server exports HWPX, review HTML, JSON data, and template-preservation artifacts.

## Core Server Functions

- `extract_text`: file text extraction and OCR hints
- `analyze_documents`: company evidence analysis
- `analyze_template`: grant form/question analysis
- `generate_plan`: business plan generation orchestrator
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
