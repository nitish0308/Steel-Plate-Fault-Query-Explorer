# Steel Plate Fault Query Explorer

A small FastAPI + SQLite app demonstrating raw parameterized SQL queries against
the Kaggle "Steel Plates Faults" dataset, with a plain HTML/JS frontend.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/ for the UI, or http://127.0.0.1:8000/docs
for the auto-generated Swagger API docs.

On first run, `app/database.py` builds `steel_faults.db` from `data/faults.csv`,
collapsing the 7 one-hot fault columns into a single `fault_type` column.

## Endpoints

| Endpoint | Business question |
|---|---|
| `GET /api/faults-by-type` | How many defects of each type have we seen? |
| `GET /api/filter?steel_type=&min_thickness=&max_thickness=` | Defects on a steel type within a thickness range |
| `GET /api/top-defects?n=` | The N largest defects by area |
| `GET /api/luminosity-stats` | Average luminosity per fault type |
| `GET /api/search?fault_type=&min_area=` | Defects of a type above a minimum area |
