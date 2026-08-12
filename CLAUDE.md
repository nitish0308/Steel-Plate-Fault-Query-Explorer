# CLAUDE.md — Steel Plate Fault Query Explorer

## Purpose

Build a small, production-style web application that demonstrates how SQL
queries are used inside a real Python backend. The dataset is the Kaggle
"Steel Plates Faults" dataset — chosen deliberately because it's real
manufacturing/quality-control data, connecting to the user's Tata Steel
manufacturing background.

The goal is **educational**: every scenario should map to a realistic
manufacturing/QC business question, and the code should be simple enough to
read end-to-end in one sitting, while still following real production
patterns (validation, layered architecture, parameterized queries).

---

## Dataset

- Source file: `C:\Users\Lenovo\New folder\Downloads\steel_kaggle_data\faults.csv`
- ~1,941 rows, 27 numeric feature columns + 7 one-hot fault-type columns.

**Key columns (standard Kaggle "Steel Plates Faults" schema):**

| Column | Meaning |
|---|---|
| X_Minimum, X_Maximum, Y_Minimum, Y_Maximum | Bounding box of the fault on the plate |
| Pixels_Areas | Size of the fault region |
| X_Perimeter, Y_Perimeter | Perimeter measurements |
| Sum_of_Luminosity, Minimum_of_Luminosity, Maximum_of_Luminosity | Luminosity stats of the fault region |
| Length_of_Conveyer | Conveyor length at time of scan |
| TypeOfSteel_A300, TypeOfSteel_A400 | One-hot steel type |
| Steel_Plate_Thickness | Plate thickness |
| Edges_Index, Empty_Index, Square_Index, Outside_X_Index, Edges_X_Index, Edges_Y_Index, Outside_Global_Index | Shape/geometry indices |
| LogOfAreas, Log_X_Index, Log_Y_Index | Log-transformed geometry features |
| Orientation_Index, Luminosity_Index, SigmoidOfAreas | Derived indices |
| Pastry, Z_Scratch, K_Scatch, Stains, Dirtiness, Bumps, Other_Faults | One-hot fault type (exactly one = 1 per row) |

**Important preprocessing step:** the 7 one-hot fault columns should be
collapsed into a single categorical column `fault_type` (text) when loading
into the database. This makes querying and the UI far more natural
(`WHERE fault_type = 'Bumps'` instead of `WHERE Bumps = 1`).

---

## Tech Stack

- **Backend:** FastAPI (Python 3.10+)
- **Database:** SQLite (file-based, zero setup, realistic enough for learning)
- **DB access:** raw SQL via `sqlite3`, NOT an ORM — the point of this
  project is to see actual SQL queries in the Python code, not have them
  hidden behind an ORM abstraction.
- **Validation:** Pydantic v2 models for all API request/response schemas
- **Frontend:** Single static HTML page with vanilla JS (fetch calls to the
  FastAPI backend). No frontend framework needed — keep it simple.
- **Server:** `uvicorn`

---

## Project Structure

```
steel_fault_explorer/
├── CLAUDE.md
├── requirements.txt
├── data/
│   └── faults.csv                  # copy of the source CSV
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app + route definitions
│   ├── database.py                 # DB connection + CSV-to-SQLite loader
│   ├── models.py                   # Pydantic request/response models
│   └── queries.py                  # All raw SQL query strings + functions
├── static/
│   ├── index.html                  # UI with 5 scenario buttons
│   └── app.js                      # fetch() calls to backend endpoints
└── steel_faults.db                 # generated SQLite file (gitignored)
```

---

## Database Setup

On first run, `database.py` should:
1. Check if `steel_faults.db` exists; if not, create it.
2. Load `data/faults.csv` with `pandas`.
3. Collapse the 7 one-hot fault columns into one `fault_type` column.
4. Write to a single table `plate_faults` using `pandas.to_sql`.
5. Add an index on `fault_type` since most queries filter by it:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_fault_type ON plate_faults(fault_type);
   ```

---

## The 5 Scenarios (UI Buttons → API Endpoints → SQL Queries)

Each button on the frontend calls a distinct API endpoint. Each endpoint
demonstrates a different SQL pattern commonly seen in production systems.

### 1. "Faults by Type" — simple `GROUP BY` + `COUNT`
**Business question:** "How many defects of each type have we seen? Which
fault is most common on the line?"
**Endpoint:** `GET /api/faults-by-type`
**SQL pattern:**
```sql
SELECT fault_type, COUNT(*) AS count
FROM plate_faults
GROUP BY fault_type
ORDER BY count DESC;
```

### 2. "Filter by Steel Type & Thickness Range" — parameterized `WHERE`
**Business question:** "Show me all defects found on A300 steel plates
thicker than X mm — are certain thicknesses more fault-prone?"
**Endpoint:** `GET /api/filter?steel_type=A300&min_thickness=40&max_thickness=100`
**Pydantic model:** validates `steel_type` is one of `A300`/`A400`,
`min_thickness`/`max_thickness` are positive floats, and `min <= max`.
**SQL pattern (parameterized — never string-interpolated):**
```sql
SELECT * FROM plate_faults
WHERE (TypeOfSteel_A300 = 1 AND ? = 'A300' OR TypeOfSteel_A400 = 1 AND ? = 'A400')
  AND Steel_Plate_Thickness BETWEEN ? AND ?
LIMIT 50;
```

### 3. "Largest Defects" — `ORDER BY` + `LIMIT` (Top-N)
**Business question:** "What are the 10 largest defects by area? These are
the ones most likely to cause a rejected plate."
**Endpoint:** `GET /api/top-defects?n=10`
**Pydantic model:** validates `n` is an int between 1 and 100.
**SQL pattern:**
```sql
SELECT fault_type, Pixels_Areas, X_Minimum, X_Maximum, Y_Minimum, Y_Maximum
FROM plate_faults
ORDER BY Pixels_Areas DESC
LIMIT ?;
```

### 4. "Luminosity Anomaly Check" — aggregate comparison across groups
**Business question:** "Do certain fault types tend to occur in
darker/brighter regions of the plate? Could help tune the optical
inspection camera thresholds."
**Endpoint:** `GET /api/luminosity-stats`
**SQL pattern:**
```sql
SELECT fault_type,
       ROUND(AVG(Minimum_of_Luminosity), 2) AS avg_min_luminosity,
       ROUND(AVG(Maximum_of_Luminosity), 2) AS avg_max_luminosity,
       ROUND(AVG(Sum_of_Luminosity), 2)     AS avg_total_luminosity
FROM plate_faults
GROUP BY fault_type
ORDER BY avg_total_luminosity DESC;
```

### 5. "Search by Fault Type + Minimum Area" — combined filter (multi-param)
**Business question:** "Show me all 'K_Scatch' defects above a certain
size — used to decide which past defects should be escalated for
inspection."
**Endpoint:** `GET /api/search?fault_type=K_Scatch&min_area=500`
**Pydantic model:** validates `fault_type` against the known list of 7 valid
types (enum), and `min_area` is a non-negative number.
**SQL pattern:**
```sql
SELECT * FROM plate_faults
WHERE fault_type = ? AND Pixels_Areas >= ?
ORDER BY Pixels_Areas DESC
LIMIT 50;
```

**(Optional 6th scenario, if time permits):** "Steel Type Distribution" —
a simple `CASE WHEN` query converting the one-hot steel columns into a
readable summary, showing a different core SQL construct (`CASE`).

---

## Mutation Endpoints (`PUT` / `DELETE`)

Individual fault records are identified by SQLite's implicit `rowid` (the
table has no explicit primary key column). These demonstrate `UPDATE` and
`DELETE` SQL patterns; both are still parameterized, and both 404 when
`rowid` doesn't match a row.

### "Correct Fault Classification" — `UPDATE`
**Business question:** "An inspector reviewed a defect and determined it
was misclassified — correct its fault type."
**Endpoint:** `PUT /api/faults/{rowid}` — body `{"fault_type": "K_Scatch"}`
**SQL pattern:**
```sql
UPDATE plate_faults SET fault_type = ? WHERE rowid = ?;
```

### "Discard Defect Record" — `DELETE`
**Business question:** "This defect record turned out to be a sensor
artifact or duplicate scan — remove it from the dataset."
**Endpoint:** `DELETE /api/faults/{rowid}`
**SQL pattern:**
```sql
DELETE FROM plate_faults WHERE rowid = ?;
```

---

## Pydantic Validation Requirements

- All query parameters must be validated by Pydantic models (or FastAPI's
  native `Query(...)` validators bound to Pydantic types) — never trust raw
  query strings.
- `fault_type` inputs must be constrained to a `Literal`/`Enum` of the 7
  known values, to prevent invalid values reaching the SQL layer.
- Numeric ranges (`min_thickness`, `max_thickness`, `min_area`, `n`) must
  have explicit bounds (`ge=`, `le=` in Pydantic/FastAPI) to prevent
  nonsensical or abusive queries (e.g. `n=999999`).
- Response models should also be defined with Pydantic, so FastAPI
  auto-generates OpenAPI docs (`/docs`) with correct schemas — this is a
  good teaching moment for how production APIs self-document.

---

## SQL Safety Requirement

**All queries must use parameterized placeholders (`?` in sqlite3), never
raw f-string/`.format()` interpolation of user input into SQL.** This is a
core production lesson: preventing SQL injection. Add a code comment next
to at least one query explicitly noting *why* this matters, e.g.:

```python
# NEVER do: f"SELECT * FROM plate_faults WHERE fault_type = '{fault_type}'"
# This would allow SQL injection. Always use parameterized queries:
cursor.execute("SELECT * FROM plate_faults WHERE fault_type = ?", (fault_type,))
```

---

## Frontend Requirements

- Single `index.html` with 5 (or 6) buttons, one per scenario.
- Clicking a button calls the relevant endpoint via `fetch()` and renders
  the JSON response as a simple HTML table below the buttons.
- For scenarios with parameters (2, 3, 5), show small input fields next to
  the button so the user can adjust values before triggering the query.
- Keep styling minimal (plain CSS, no framework) — the point is the
  data flow, not visual polish.

---

## Build Steps (for Claude Code to follow, in order)

1. Create the project folder structure above.
2. Copy `faults.csv` into `data/`.
3. Write `app/database.py`: CSV loader + one-hot-to-`fault_type` collapse
   logic + SQLite table creation + index.
4. Write `app/models.py`: Pydantic models for each of the 5 endpoints
   (request params where relevant, response schemas).
5. Write `app/queries.py`: one function per scenario, each executing a
   parameterized SQL query and returning rows as dicts.
6. Write `app/main.py`: FastAPI app, mount `static/`, define the 5 routes,
   call the corresponding function from `queries.py`, validate with
   Pydantic, return JSON.
7. Write `static/index.html` + `static/app.js`: buttons, input fields,
   fetch calls, table rendering.
8. Write `requirements.txt`: `fastapi`, `uvicorn`, `pandas`, `pydantic`.
9. Add a short `README.md` with setup + run instructions
   (`pip install -r requirements.txt`, `uvicorn app.main:app --reload`).
10. Test each of the 5 endpoints manually via `/docs` (FastAPI's
    auto-generated Swagger UI) before wiring up the frontend.

---

## Out of Scope (don't build these)

- User authentication/login
- Deployment/Docker config
- Frontend framework (React/Vue) — plain HTML/JS only

Note: this was originally scoped as read-only only; `PUT`/`DELETE` on
individual fault records were added later (see "Mutation Endpoints" below)
to demonstrate those SQL patterns too. Still out of scope: bulk
write/update/delete, and anything beyond single-row corrections.
