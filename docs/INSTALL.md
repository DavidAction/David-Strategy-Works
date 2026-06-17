# Install And Use On Another Computer

## Option A: Use GitHub Clone

Install these first:

- Python 3.11 or newer
- Git

Then run:

```powershell
git clone https://github.com/DavidAction/David-Strategy-Works.git
cd David-Strategy-Works
.\start-dsw.ps1
```

The app opens at:

```text
http://127.0.0.1:8765/
```

On Windows, you can also double-click `start-dsw.bat`.

On macOS or Linux:

```bash
git clone https://github.com/DavidAction/David-Strategy-Works.git
cd David-Strategy-Works
sh start-dsw.sh
```

## Option B: Download ZIP

1. Go to `https://github.com/DavidAction/David-Strategy-Works`.
2. Click `Code` > `Download ZIP`.
3. Extract the ZIP.
4. Run `start-dsw.bat` on Windows, or `sh start-dsw.sh` on macOS/Linux.

This option works without Git, but updates are easier with Git.

## Move Existing Work Data To Another PC

GitHub does not include local work data because it can contain sensitive company documents.

To move your existing profiles, uploaded templates, saved versions, and generated exports:

1. On the old PC, open the project folder.
2. Copy these folders/files if they exist:
   - `data/`
   - `exports/`
   - `.env`
3. Paste them into the same project folder on the new PC.

What each item contains:

- `data/profiles.json`: company profiles and workspaces
- `data/templates/`: uploaded grant templates
- `data/versions/`: draft and revision versions
- `data/datasets/`: grant success criteria
- `exports/`: generated HWPX/HTML/JSON files
- `.env`: API keys and local settings

Do not upload `data/`, `exports/`, or `.env` to a public GitHub repository.

## API Keys

The first run creates `.env` from `.env.example`.

Open `.env` and fill only what you use:

```text
GEMINI_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

Without API keys, the app still runs in local rule-based mode.

## Update On Another PC

If the folder was cloned with Git:

```powershell
.\update-dsw.ps1
```

Or:

```powershell
git pull --ff-only
```

Then restart the app.

## Troubleshooting

- If the browser does not open, manually go to `http://127.0.0.1:8765/`.
- If port `8765` is already used, edit `.env` and change `PORT=8766`, then restart.
- If OCR is needed, open PowerShell as Administrator, run `.\tools\install_ocr_windows.ps1`, then run `python tools\ocr_check.py --require-ocr`.
- If the app will be accessed from another device on your network, set `DSW_WORKSPACE_PASSWORD` in `.env`.
- If you want export to fail closed when evidence gaps remain, set `DSW_BLOCK_UNSAFE_EXPORT=true`.
- Generated exports are retained locally. Run `python tools\export_retention.py` to inspect cleanup candidates and `python tools\export_retention.py --delete --confirm DELETE_EXPORTS` only after submission is complete.
- If Windows blocks PowerShell scripts, run `start-dsw.bat` instead.
