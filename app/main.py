"""FastAPI app for the Steel Plate Fault Query Explorer."""

from typing import Annotated
from fastapi.responses import JSONResponse
import time

import pydantic
from fastapi import Depends, FastAPI, Query, Request
from fastapi.staticfiles import StaticFiles

from app import queries
from app.database import init_db
from app.models import (
    FaultCount,
    FaultType,
    LuminosityStats,
    PlateFaultRow,
    SteelFilterParams,
    TopDefectRow,
)

app = FastAPI(title="Steel Plate Fault Query Explorer")

init_db()


@app.exception_handler(pydantic.ValidationError)
async def pydantic_validation_exception_handler(
    request: Request, exc: pydantic.ValidationError
) -> JSONResponse:
    """FastAPI only auto-converts validation errors for models bound directly
    to a request; a Pydantic model resolved via `Depends()` (scenario 2's
    cross-field min/max check) raises pydantic.ValidationError instead, which
    would otherwise surface as an unhandled 500."""
    errors = [{k: v for k, v in err.items() if k != "ctx"} for err in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": errors})


@app.get("/api/faults-by-type", response_model=list[FaultCount])
def get_faults_by_type() -> list[dict]:
    return queries.faults_by_type()


@app.get("/api/filter", response_model=list[PlateFaultRow])
def get_filter(params: Annotated[SteelFilterParams, Depends()]) -> list[dict]:
    return queries.filter_by_steel_and_thickness(
        params.steel_type.value, params.min_thickness, params.max_thickness
    )


@app.get("/api/top-defects", response_model=list[TopDefectRow])
def get_top_defects(n: Annotated[int, Query(ge=1, le=100)] = 10) -> list[dict]:
    return queries.top_defects(n)


@app.get("/api/luminosity-stats", response_model=list[LuminosityStats])
def get_luminosity_stats() -> list[dict]:
    return queries.luminosity_stats()


@app.get("/api/search", response_model=list[PlateFaultRow])
def get_search(
    fault_type: FaultType,
    min_area: Annotated[float, Query(ge=0)],
) -> list[dict]:
    return queries.search_by_fault_and_area(fault_type.value, min_area)


app.mount("/", StaticFiles(directory="static", html=True), name="static")
