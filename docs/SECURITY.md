# Security And Privacy

David Strategy Works is designed as a local-first workspace. Company documents, draft versions, generated exports, and API keys should stay outside the public repository.

## Local Data

- `data/` stores company profiles, uploaded template copies, and draft versions.
- `exports/` stores generated HWPX, HTML, JSON, and template preservation packages.
- `.env` stores API keys and local OCR command settings.
- These paths are ignored by `.gitignore` and should not be committed.

## Sensitive Documents

Business registrations, corporate registry extracts, financial documents, IDs, contracts, LOIs, and customer interview material may contain sensitive information. The document analyzer marks likely restricted documents and surfaces a security report in the draft/export screens.

## API Transmission Policy

When Gemini, OpenAI, or Anthropic keys are connected, review restricted documents before sending content to external APIs. For highly sensitive projects, paste only the minimum required excerpts or run the local fallback mode.

## Recommended Operating Rules

1. Keep `data/`, `exports/`, and `.env` local or transfer them through a private channel.
2. Do not upload real company documents to a public GitHub repository.
3. Delete unneeded exports after submission.
4. Use separate company profiles for separate clients.
5. Before outsourcing, provide sample/redacted data unless the contractor has permission to access real documents.
