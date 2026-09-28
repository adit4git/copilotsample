# Atlas Advisor Console — rebuild from scratch

Everything here is plain text. No patches, no baseline, no earlier version needed.

## What you need
- Python 3.11+ and `pip`
- `pdftotext` (from poppler-utils)
- The strategy catalog PDF (June 2026 edition)

## Four steps

```bash
# 1. Check every file arrived intact (optional but recommended)
python3 check_files.py

# 2. Copy the code into a new, empty folder
mkdir ~/atlas && cp -r code/* ~/atlas/

# 3. Build the data files and the three PDF factsheets
pdftotext -layout <strategy-catalog>.pdf catalog.txt
python3 build_data.py ~/atlas catalog.txt
pip install reportlab matplotlib      # only needed for the PDF step
python3 make_pdfs.py ~/atlas

# 4. Install, test, run
cd ~/atlas
pip install -r requirements.txt
python3 -m pytest tests/ -q          # expect: 38 passed
uvicorn app.main:app --reload        # open http://localhost:8000
```

`build_data.py` prints a line per file and stops with a clear message if anything is off
(for example, a different catalog edition).

## What's in the kit

| Path | What it is |
|---|---|
| `code/` | The complete app source, exactly as it runs today: `app/*.py`, `app/static/` (HTML, CSS, JS), `tests/`, `requirements.txt`, `pyproject.toml` |
| `data/*.csv` | Households, holdings, enrollments, facts and the rule store as tables (one row per item) |
| `data/*.json` | Three small hand-authored files: advisor profiles and minimums, research models, content catalog |
| `build_data.py` | Builds all six files in `app/data/` from `data/` plus the catalog PDF text |
| `make_pdfs.py` | Regenerates the three client factsheet PDFs used by the "Preview PDF" popup |
| `check_files.py`, `MANIFEST.txt` | Checksums for every file in the kit |

## How this was verified
Starting from an empty folder with only this kit: all 21 app and test files came out identical to the running
app (JSON compared by content, everything else byte for byte), 38/38 tests passed, the regenerated PDFs have
the same text as the originals, and a browser check of the book, DCA workbench, product shelf, PDF popup and
dark mode showed no errors.

## Not included
Deployment files (Dockerfile, railway.json) and project docs. Ask if you need them.
