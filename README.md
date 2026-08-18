# Steel Plate Fault Query Explorer

A FastAPI application to generate raw parameterized SQL queries against
the "Steel Plates Faults" dataset.

## Setup

```bash
pip install -r requirements.txt
```

A Redis server must also be running (used to cache expensive aggregate
queries — see "Caching" below). Default connection is `redis://localhost:6379/0`;
override with the `REDIS_URL` environment variable. Easiest local option:

```bash
docker run -p 6379:6379 redis
```

## Run

```bash
uvicorn app.main:app --reload
```

Then open http://127.0.0.1:8000/ for the UI, or http://127.0.0.1:8000/docs
for the auto-generated Swagger API docs.

On first run, `app/database.py` builds `steel_faults.db` from `data/faults.csv`,
collapsing the 7 one-hot fault columns into a single `fault_type` column.

## Run with Docker

```bash
docker compose up --build
```

This starts the app (built from the `Dockerfile`) and a Redis container
together, wired via `REDIS_URL`. Open http://127.0.0.1:8000/ as above.
`steel_faults.db` isn't persisted across container restarts — it's rebuilt
from `data/faults.csv` each time the container starts, same as a fresh
local checkout.

## Caching

`GET /api/faults-by-type` and `GET /api/top-defects` aggregate/scan the
whole table on every call, so their results are cached in Redis
(`app/cache.py`) with a 60s TTL — a "cache-aside" pattern: check Redis
first, fall back to SQLite on a miss, then populate the cache. Since
`PUT /api/faults/{rowid}` and `DELETE /api/faults/{rowid}` can change those
aggregates (a reclassified or discarded defect changes counts/rankings),
both cached keys are explicitly invalidated on a successful write.

## Endpoints

| Endpoint | Business question |
|---|---|
| `GET /api/faults-by-type` | How many defects of each type have we seen? |
| `GET /api/filter?steel_type=&min_thickness=&max_thickness=` | Defects on a steel type within a thickness range |
| `GET /api/top-defects?n=` | The N largest defects by area |
| `GET /api/luminosity-stats` | Average luminosity per fault type |
| `GET /api/search?fault_type=&min_area=` | Defects of a type above a minimum area |
