# HWPX Template Benchmarks

Put redacted government grant HWPX forms in the private runtime folder with:

```powershell
python tools\import_hwpx_samples.py C:\path\to\grant-template.hwpx
```

The files are copied under `data/templates/real_samples/`, which is intentionally ignored by Git because real forms may contain notice metadata or client edits.

For repeatable public tests, use `tools\quality_smoke.py`; it creates an in-memory HWPX fixture with answer placeholders and verifies the fill pipeline.
