import pytest
from app.queries import filter_by_steel_and_thickness

def test_filter_by_steel_and_thickness():
    with pytest.raises(ValueError):
        filter_by_steel_and_thickness("A500", 0.5, 1.0)

    results = filter_by_steel_and_thickness("A300", 0.5, 1.0)
    assert len(results) == 50


def top_defects():
    results = filter_by_steel_and_thickness("A300", 0.5, 1.0)
    assert len(results) == 50

    results = filter_by_steel_and_thickness("A400", 0.5, 1.0)
    assert len(results) == 50   

    results = filter_by_steel_and_thickness("A300", 0.5, 1.0)
    assert len(results) == 50