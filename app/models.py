"""Pydantic request/response models for the Steel Plate Fault Query Explorer API."""

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class SteelType(str, Enum):
    A300 = "A300"
    A400 = "A400"


class FaultType(str, Enum):
    PASTRY = "Pastry"
    Z_SCRATCH = "Z_Scratch"
    K_SCATCH = "K_Scatch"
    STAINS = "Stains"
    DIRTINESS = "Dirtiness"
    BUMPS = "Bumps"
    OTHER_FAULTS = "Other_Faults"


# ---------------------------------------------------------------------------
# Scenario 1: Faults by Type
# ---------------------------------------------------------------------------


class FaultCount(BaseModel):
    fault_type: str
    count: int


# ---------------------------------------------------------------------------
# Scenario 2: Filter by Steel Type & Thickness Range
# ---------------------------------------------------------------------------


class SteelFilterParams(BaseModel):
    """Bound to the request as query params; FastAPI resolves each field
    from `?steel_type=...&min_thickness=...&max_thickness=...` when used
    as a `Depends()` dependency."""

    steel_type: SteelType
    min_thickness: float = Field(ge=0)
    max_thickness: float = Field(ge=0)

    @model_validator(mode="after")
    def check_range(self) -> "SteelFilterParams":
        if self.min_thickness > self.max_thickness:
            raise ValueError("min_thickness must be <= max_thickness")
        return self


class PlateFaultRow(BaseModel):
    X_Minimum: int
    X_Maximum: int
    Y_Minimum: int
    Y_Maximum: int
    Pixels_Areas: int
    X_Perimeter: int
    Y_Perimeter: int
    Sum_of_Luminosity: int
    Minimum_of_Luminosity: int
    Maximum_of_Luminosity: int
    Length_of_Conveyer: int
    TypeOfSteel_A300: int
    TypeOfSteel_A400: int
    Steel_Plate_Thickness: float
    Edges_Index: float
    Empty_Index: float
    Square_Index: float
    Outside_X_Index: float
    Edges_X_Index: float
    Edges_Y_Index: float
    Outside_Global_Index: float
    LogOfAreas: float
    Log_X_Index: float
    Log_Y_Index: float
    Orientation_Index: float
    Luminosity_Index: float
    SigmoidOfAreas: float
    fault_type: str


# ---------------------------------------------------------------------------
# Scenario 3: Largest Defects
# ---------------------------------------------------------------------------


class TopDefectRow(BaseModel):
    fault_type: str
    Pixels_Areas: int
    X_Minimum: int
    X_Maximum: int
    Y_Minimum: int
    Y_Maximum: int


# ---------------------------------------------------------------------------
# Scenario 4: Luminosity Anomaly Check
# ---------------------------------------------------------------------------


class LuminosityStats(BaseModel):
    fault_type: str
    avg_min_luminosity: float
    avg_max_luminosity: float
    avg_total_luminosity: float
