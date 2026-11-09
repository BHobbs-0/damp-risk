"""Unit tests for the EPC free-text parsers (real examples from the register)."""

import pytest

from src.features.epc import (
    parse_age_band,
    parse_floor_level,
    parse_floor_type,
    parse_glazing,
    parse_heating,
    parse_roof,
    parse_walls,
)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("England and Wales: before 1900", "pre1919"),
        ("England and Wales: 1900-1929", "pre1919"),  # midpoint 1914.5
        ("England and Wales: 1930-1949", "1919-1944"),
        ("England and Wales: 1950-1966", "1945-1964"),
        ("England and Wales: 1967-1975", "1965-1980"),
        ("England and Wales: 1976-1982", "1965-1980"),
        ("England and Wales: 1983-1990", "1981-1990"),
        ("England and Wales: 2012 onwards", "post1990"),
        ("2018", "post1990"),
        ("NO DATA!", None),
        ("INVALID!", None),
        (None, None),
    ],
)
def test_parse_age_band(raw, expected):
    assert parse_age_band(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Cavity wall, filled cavity", ("cavity", "insulated")),
        ("Cavity wall, as built, no insulation (assumed)", ("cavity", "none")),
        ("Cavity wall, as built, partial insulation (assumed)", ("cavity", "partial")),
        ("Solid brick, as built, no insulation (assumed)", ("solid", "none")),
        ("Solid brick, with external insulation", ("solid", "insulated")),
        ("Sandstone or limestone, as built, no insulation (assumed)", ("solid", "none")),
        ("System built, with external insulation", ("system", "insulated")),
        ("Timber frame, as built, insulated (assumed)", ("timber", "insulated")),
        ("Average thermal transmittance 0.19 W/m²K", ("other", "insulated")),
        ("Average thermal transmittance 1.50 W/m²K", ("other", "none")),
        (None, (None, None)),
    ],
)
def test_parse_walls(raw, expected):
    assert parse_walls(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Boiler and radiators, mains gas", "gas"),
        ("Community scheme", "community"),
        ("Electric storage heaters", "electric_storage"),
        ("Electric storage heaters, Room heaters, electric", "electric_storage"),
        ("Air source heat pump, radiators, electric", "heat_pump"),
        ("Room heaters, electric", "electric_direct"),
        ("No system present: electric heaters assumed", "electric_direct"),
        ("Boiler and radiators, oil", "other_fuel"),
        ("Boiler and radiators, dual fuel (mineral and wood)", "other_fuel"),
        (None, None),
    ],
)
def test_parse_heating(raw, expected):
    assert parse_heating(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("(another dwelling above)", ("dwelling_above", None)),
        ("Pitched, 270 mm loft insulation", ("pitched", "good")),
        ("Pitched, 200 mm loft insulation", ("pitched", "moderate")),
        ("Pitched, 100 mm loft insulation", ("pitched", "limited")),
        ("Pitched, 400+ mm loft insulation", ("pitched", "good")),
        ("Pitched, no insulation (assumed)", ("pitched", "none")),
        ("Pitched, insulated (assumed)", ("pitched", "moderate")),
        ("Flat, limited insulation (assumed)", ("flat", "limited")),
        ("Roof room(s), insulated (assumed)", ("roof_rooms", "moderate")),
        ("Average thermal transmittance 0.15 W/m²K", ("other", "good")),
    ],
)
def test_parse_roof(raw, expected):
    assert parse_roof(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Solid, no insulation (assumed)", "solid"),
        ("Suspended, no insulation (assumed)", "suspended"),
        ("(another dwelling below)", "dwelling_below"),
        ("(other premises below)", "dwelling_below"),
        ("To unheated space, no insulation (assumed)", "exposed"),
    ],
)
def test_parse_floor_type(raw, expected):
    assert parse_floor_type(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Fully double glazed", "full"),
        ("High performance glazing", "full"),
        ("Single glazed", "single"),
        ("Partial double glazing", "partial"),
        ("Some double glazing", "partial"),
        ("Mostly double glazing", "partial"),
    ],
)
def test_parse_glazing(raw, expected):
    assert parse_glazing(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Ground", 0),
        ("ground floor", 0),
        ("Basement", -1),
        ("3rd", 3),
        ("21st or above", 21),
        ("mid floor", None),
        (None, None),
    ],
)
def test_parse_floor_level(raw, expected):
    assert parse_floor_level(raw) == expected
