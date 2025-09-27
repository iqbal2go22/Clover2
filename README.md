## Footballguys Stats Scraper (GUI + CLI)

This tool logs into Footballguys, scrapes weekly historical player stats for QB/FLEX/DEF, and upserts them into SQL Server via ODBC. It provides a Tkinter GUI when a display is available, and a CLI fallback for headless servers.

### Features
- GUI with week/year/table selection and live logs
- CLI flags and `.env` support
- Selenium + Chrome with multiple login and data-page variants
- Robust DB upsert via `MERGE` into a user-specified table

### Requirements
- Python 3.10+
- Google Chrome installed
- SQL Server reachable and ODBC Driver 17+ for SQL Server
- Network access to footballguys.com

### Install
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # then edit .env with your credentials
```

### Configure
Edit `.env` (or set environment variables):
- `FBG_EMAIL` / `FBG_PASSWORD`: Footballguys credentials
- `DB_CONN_STR`: Optional custom SQL Server connection string
- `WEEK`, `YEAR`, `TABLE_NAME`: Defaults for convenience
- `HEADLESS`: Set `true` for headless Chrome
- `USE_GUI`: Set `false` to force CLI even with a display
- `CHROME_BINARY`: Path to Chrome if not in default location
- `OUT_CSV`: Optional path to write scraped rows as CSV

Default DB connection if `DB_CONN_STR` is not set:
```
DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=TonyDB;Trusted_Connection=yes;Connection Timeout=5;
```

### Run (GUI)
```bash
python fbg_scraper.py
```
If GUI cannot start (e.g., no DISPLAY), it automatically falls back to the CLI.

### Run (CLI)
```bash
python fbg_scraper.py --week 1 --year 2025 --table FootballStats --headless \
  --email "$FBG_EMAIL" --password "$FBG_PASSWORD" \
  --db-conn-str "$DB_CONN_STR" --out-csv output.csv
```
All flags are optional if provided in `.env`.

### Windows notes
- Install Microsoft ODBC Driver 17+ for SQL Server.
- Ensure Chrome is installed. If portable or nonstandard, set `CHROME_BINARY`.

### Linux notes
- Ensure Chrome is installed (e.g., `google-chrome-stable`).
- On headless servers, use `--headless` and set `USE_GUI=false`.
- You may need `unixodbc` and MS ODBC 17+ packages installed for `pyodbc` to connect.

### Troubleshooting
- Login failures: Verify credentials and that FBG login page layout has not changed.
- DB connection: Test `DB_CONN_STR` using `isql`/`sqlcmd` or another SQL client.
- Chrome/driver mismatch: `webdriver-manager` auto-installs a compatible driver; ensure Chrome is up to date.

### Safety & Credentials
Credentials are read from environment variables. Avoid committing `.env` to source control. 