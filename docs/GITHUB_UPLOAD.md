# GitHub Upload Guide

## Recommended Repository Scope

Upload the `outputs/briwell-plan-writer` folder as the repository root.

Do commit:

- `server.py`
- `static/`
- `docs/`
- `README.md`
- `.env.example`
- `.gitignore`

Do not commit:

- `.env`
- `data/`
- `exports/`
- actual 사업자등록증, 등기부등본, 재무자료, 개인정보 포함 문서

## First Push Example

```powershell
cd outputs\briwell-plan-writer
git init
git add .
git commit -m "Initial David Strategy Works MVP"
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_REPO.git
git push -u origin main
```

If commit fails because Git identity is missing:

```powershell
git config user.name "Your Name"
git config user.email "you@example.com"
```

## For Claude Code / Codex Handoff

Ask the next agent to read:

1. `docs/HANDOFF.md`
2. `docs/ARCHITECTURE.md`
3. `docs/ROADMAP.md`

Then run:

```powershell
python server.py --port 8765
```

