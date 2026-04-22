# Coaching Notes — Dutch Data Pipeline

A living reference of everything covered in sessions. Commands include explanations so you can recall the *why*, not just the *what*.

---

## Git

Git tracks changes to your code over time and lets you sync with GitHub (the remote).

```bash
git init
# Turns the current folder into a git repository.
# Creates a hidden .git/ folder that stores all version history locally.

git remote add origin <url>
# Connects your local repo to a remote repo on GitHub.
# "origin" is just a nickname for that URL — convention, not magic.
# After this, git knows where to push/pull.

git status
# Shows what files have changed, what's staged, what's untracked.
# Run this constantly — it's your compass.

git add <file>
# Stages a file — tells git "include this in the next commit."
# git add . stages everything in the current folder.

git commit -m "message"
# Saves a snapshot of all staged changes.
# The message should describe *what changed and why* in one line.

git push -u origin main
# Uploads your commits to GitHub.
# -u sets "origin main" as the default, so next time just: git push
```

---

## Project Structure

```
dutch-data-pipeline/
├── data/           # raw and processed data files (gitignored if large)
├── ingestion/      # scripts that fetch data from APIs/sources
├── sql/            # SQL exercises and queries
├── dbt/            # dbt project (added in Weeks 3-4)
├── airflow/        # DAG definitions (added in Weeks 5-6)
├── tools/          # utility scripts (job_analyzer.py lives here)
├── coaching_notes.md
├── progress.json
└── README.md
```

---

## Python — Data Ingestion

### Finding APIs for a dataset

When you encounter a new data source, don't just download manually — look for an API:
1. Search `"<dataset name> API"` or `"<dataset name> open data API"`
2. Find the docs page — look for parameter reference, auth requirements, rate limits
3. Government/research datasets (KNMI, CBS, RDW) almost always have open APIs

**KNMI resources:**
- API background: https://www.knmi.nl/kennis-en-datacentrum/achtergrond/data-ophalen-vanuit-het-klimatologie-loket
- Parameter reference (variables like TG, RH, FG): https://www.daggegevens.knmi.nl/klimatologie/daggegevens

### knmi_ingest.py — explained

```python
import requests   # makes HTTP calls to APIs
import csv        # reads/writes CSV files
import os         # handles file paths (OS-agnostic)
from datetime import datetime  # timestamps your data

# Constants at the top — engineering convention, not beginner habit
STATION_ID = "260"      # De Bilt — main KNMI reference station in NL
START_DATE = "20240101"
END_DATE = "20241231"
OUTPUT_DIR = "data"

def fetch_knmi_data(station_id, start_date, end_date):
    url = "https://www.daggegevens.knmi.nl/klimatologie/daggegevens"
    params = {
        "stns": station_id,
        "start": start_date,
        "end": end_date,
        "vars": "TG:RH:FG",  # mean temp : rainfall : mean wind speed
    }
    response = requests.get(url, params=params)
    response.raise_for_status()  # fail loudly on API errors — engineering habit
    return response.text          # KNMI returns plain text, not JSON
```

**`raise_for_status()`** — if the API returns HTTP 404/500/etc, this throws an exception immediately. Never silently accept a bad response.

**`params` dict** — `requests` appends these as query string: `?stns=260&start=20240101&...`. You never build URLs by hand.

---

## SQL — Window Functions

Window functions add a calculated column **without collapsing rows** (unlike GROUP BY).

```sql
-- GROUP BY: loses individual rows
SELECT station_id, AVG(temperature) FROM daily_weather GROUP BY station_id

-- WINDOW: keeps all rows, adds average alongside
SELECT *, AVG(temperature) OVER () FROM daily_weather
```

### OVER() syntax

```sql
OVER ()                                          -- entire table as one window
OVER (PARTITION BY station_id)                   -- reset window per station
OVER (PARTITION BY station_id ORDER BY date)     -- ordered window per station
```

- `PARTITION BY` — splits into groups (keeps all rows, resets calculation per group)
- `ORDER BY` — required for functions that depend on row order (ROW_NUMBER, LAG, LEAD)
- No comma between PARTITION BY and ORDER BY — they are separate clauses

### Key functions

```sql
-- ROW_NUMBER: numbers rows within each partition (needs ORDER BY)
ROW_NUMBER() OVER (PARTITION BY station_id ORDER BY date)

-- LAG: fetches value from N rows back (default 1). Needs ORDER BY.
LAG(temperature) OVER (PARTITION BY station_id ORDER BY date)
-- Always partition by the same group as your analysis — otherwise LAG bleeds across groups

-- AVG/SUM/MIN/MAX: aggregate over the window (ORDER BY optional)
AVG(temperature) OVER (PARTITION BY station_id)
```

### Pattern: CTE for derived columns

You can't reference a window function alias in the same SELECT. Use a CTE:

```sql
WITH cte AS (
    SELECT *, LAG(temperature) OVER (PARTITION BY station_id ORDER BY date) AS pre_temp
    FROM daily_weather
)
SELECT *, temperature - pre_temp AS temp_change
FROM cte
```

### Window frames — ROWS BETWEEN

Defines exactly which rows the window covers. Used for rolling calculations:

```sql
-- 7-day rolling average
AVG(TG) OVER (
    PARTITION BY station_id
    ORDER BY date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
)
```

**`ROWS BETWEEN` always requires `ORDER BY`** — without it, "6 preceding rows" is in undefined order. The result is meaningless and some engines will error. Always pair them.

### Rule of thumb
- Needs ORDER BY: `ROW_NUMBER`, `RANK`, `LAG`, `LEAD`, any `ROWS BETWEEN` — they care about sequence
- ORDER BY optional: `AVG`, `SUM`, `MIN`, `MAX`, `COUNT` without a frame — they just aggregate
