# Test Plan

Use this checklist before relying on a generated proposal for submission.

## Automated Smoke Test

Run this first after every meaningful code change:

```powershell
python tools\quality_smoke.py
```

The smoke test checks document analysis, grant template analysis, draft generation, comment revision, export files, and HWPX package structure.

## Document Extraction

1. Upload an existing business plan and confirm the business-understanding report covers at least problem, customer, solution, market, traction, budget, team, and roadmap.
2. Upload business registration and corporate registry documents and confirm legal identifiers are extracted when present.
3. Upload a text PDF and confirm paragraphs and tables are extracted.
4. Upload a scanned PDF or image after installing Tesseract/Poppler and confirm OCR notes are shown.
5. Confirm each document shows remediation actions when extraction is weak.

## Draft Generation

1. Upload a grant template and confirm question count/order validation.
2. Fill page count, structure, focus points, and format rules.
3. Generate a draft and confirm HWPX fill mapping is present.
4. Confirm source traceability marks most sections as grounded or partial.
5. Confirm unsupported claim audit reports no invented numbers or exaggerated claims.

## Revision Workflow

1. Save the first draft version.
2. Add revision comments and create a new version.
3. Confirm `revisionDiff` records changed sections.
4. Restore an older version and export it independently.

## Export

1. Export HWPX, HTML, and JSON.
2. Open the HTML review file and verify visual assets, judge questions, security report, and format checks.
3. Open the HWPX in Hancom Office or compatible viewer.
4. If an original template was uploaded, confirm the template preservation package includes the original file and mapping JSON.

## Handoff

1. Clone the GitHub repo on another PC.
2. Copy `.env`, `data/`, and `exports/` privately if needed.
3. Run `start-dsw.ps1` or `python server.py --port 8765`.
4. Confirm `http://127.0.0.1:8765/api/health` returns `ok`.
