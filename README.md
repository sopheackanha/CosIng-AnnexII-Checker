# COSING Ingredient Checker

A Django-based tool to check cosmetic product ingredient lists against the EU Cosmetics Regulation (EC) 1223/2009 Annex II (prohibited substances). Supports text input and label image OCR, asynchronous processing, caching, and a clean UI for results and history.

## Features
- Ingredient compliance check against Annex II
- Text input and image OCR (Tesseract)
- Exact and fuzzy matching with normalization
- Summaries: Prohibited, Warnings, Safe
- CMR flagging with hover notes (e.g., "Reprotoxic Cat. 1B()")
- Async processing via Celery; live status polling
- Caching via Redis to avoid recomputation
- Analysis history with stats

## Architecture
- Django app (views, forms, templates)
- Services pipeline:
  - Parser/Normalizer → Matcher → Summary
  - OCR for images (Windows-friendly detection)
- Celery worker for background tasks
- Redis as Celery broker/result and application cache
- SQLite (dev) / PostgreSQL (prod) for persistence

### Matching Logic
- Exact match → `PROHIBITED` (with regulation, `is_cmr`, `cmr_note`)
- Fuzzy match ≥90% → `WARNING` (<98) or `PROHIBITED` (≥98)
- Safe override for common safe ingredients → `SAFE`

## Tech Stack
- Backend: Django 6, Celery 5.6
- Data/Cache: Redis (broker/result + cache), SQLite/PostgreSQL
- OCR: Tesseract via `pytesseract` and `Pillow`
- Matching: `rapidfuzz`
- UI: Bootstrap templates

## Setup (Windows)

### 1) Python environment
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Database
```powershell
python manage.py migrate
```

### 3) Load Annex II dataset
```powershell
python manage.py load_annex_ii datasets\COSING_Annex_II_v2.csv
```

### 4) Tesseract OCR
- Install Tesseract (e.g., from UB Mannheim builds)
- Ensure it’s in PATH or set `TESSERACT_CMD` env var to the full path

```powershell
$env:TESSERACT_CMD = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
```

### 5) Redis
- Redis is used for Celery broker/result and app cache
- Ensure a Redis server is running at `redis://localhost:6379`
- If binding errors occur, another Redis might already be running; either stop it or choose a different port

### 6) Start Celery worker
```powershell
celery -A cosing_checker worker --loglevel=info --pool=solo
```

### 7) Start Django
```powershell
python manage.py runserver
```

## Configuration
- Celery broker/result: `redis://localhost:6379/0`
- Django cache: `redis://localhost:6379/1` (can switch to LocMem in dev)
- Media: `MEDIA_ROOT`/`MEDIA_URL` for uploads
- OCR detection: `TESSERACT_CMD` or common Windows install paths

## Usage
- Navigate to the analyzer page (home)
- Use:
  - Text tab: paste ingredient list
  - Image tab: upload label image (OCR extracts text)
- Results page shows summary and detailed matches
- Hover over `CMR` badge to see the note
- See past runs in History

## API
- Check async status:
  - `GET /api/analysis-status/<id>/` → `{ complete: bool, status: 'safe'|'warning'|'prohibited', redirect_url?: string }`

## Caching: Why Redis?
- Redis acts as fast shared memory between web and worker processes
- Caches the Annex II list and per-ingredient results to avoid repeated DB reads and recomputation
- Keeps response times snappy for common lists and repeat submissions
- In dev, you can switch to Django’s `LocMemCache` if Redis is inconvenient

## Testing
```powershell
python manage.py test
```
- Service tests live under `analyzer/services/tests/`

## Troubleshooting
- OCR not available:
  - Install Tesseract; set `TESSERACT_CMD`; verify path
- Redis bind error:
  - Ensure only one Redis instance uses port 6379; change port if needed
- CMR tooltip not showing detailed note:
  - Create a new analysis after enabling `cmr_note` propagation; older analyses may lack the note in `result_json`
- Celery changes not reflected:
  - Restart the worker after code edits

## Roadmap
- Extend to Annex III/IV (restricted/allowed lists)
- Ingest CPSR Part A data; export assessor-ready evidence packs
- Batch portfolio scans, dashboards, and report exports
- Public/private APIs for PLM/LIMS integrations