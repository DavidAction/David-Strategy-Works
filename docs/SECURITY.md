# Security And Privacy

David Strategy Works is designed as a local-first workspace. Company documents, draft versions, generated exports, and API keys should stay outside the public repository.

## Local Data

- `data/` stores company profiles, uploaded template copies, and draft versions.
- `exports/` stores generated HWPX, HTML, JSON, and template preservation packages.
- `.env` stores API keys, optional workspace password, export gate settings, and local OCR command settings.
- `data/ai_usage.jsonl` stores actual AI token/cost usage records when provider responses include token usage.
- These paths are ignored by `.gitignore` and should not be committed.

## Sensitive Documents

Business registrations, corporate registry extracts, financial documents, IDs, contracts, LOIs, and customer interview material may contain sensitive information. The document analyzer marks likely restricted documents and surfaces a security report in the draft/export screens.

## API Transmission Policy

When Gemini, OpenAI, or Anthropic keys are connected, review restricted documents before sending content to external APIs. For highly sensitive projects, paste only the minimum required excerpts or run the local fallback mode.

Set `DSW_BLOCK_UNSAFE_EXPORT=true` to block export when unresolved evidence gaps, high-risk unsupported claims, or restricted-document AI-transfer confirmation gaps remain. Set `DSW_WORKSPACE_PASSWORD` before exposing the local server beyond your own machine.

## Recommended Operating Rules

1. Keep `data/`, `exports/`, and `.env` local or transfer them through a private channel.
2. Do not upload real company documents to a public GitHub repository.
3. Delete unneeded exports after submission.
4. Use separate company profiles for separate clients.
5. Before outsourcing, provide sample/redacted data unless the contractor has permission to access real documents.
6. If sharing the app on a local network, require `DSW_WORKSPACE_PASSWORD` and avoid committing `data/ai_usage.jsonl`.
