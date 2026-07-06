from __future__ import annotations

import unicodedata
from pathlib import Path

import pandas as pd

TEXT_COLUMNS = [
    "Causa",
    "Causa_especifica",
    "Tipo_Vegetacion",
    "Tipo_impacto",
    "Predio",
    "Estado",
    "Entidad",
    "Municipio",
    "Region",
    "Tamano",
    "Tipo_de_incendio",
]

CAUSE_LABELS = {
    "actividades ilicitas": "Actividades ilícitas",
    "actividades agropecuarias": "Actividades agropecuarias",
    "actividades agricolas": "Actividades agrícolas",
    "actividades pecuarias": "Actividades pecuarias",
    "cazadores": "Cazadores",
    "cultivos ilicitos": "Cultivos ilícitos",
    "desconocido": "Desconocidas",
    "desconocidas": "Desconocidas",
    "festividades y rituales": "Festividades y rituales",
    "fogatas": "Fogatas",
    "fumadores": "Fumadores",
    "intencional": "Intencional",
    "limpias de derecho de via": "Limpias de derecho de vía",
    "naturales": "Naturales",
    "ninguna / no aplica": "Desconocidas",
    "otras actividades productivas": "Otras actividades productivas",
    "otras causas": "Otras causas",
    "quema de basureros": "Quema de basureros",
    "residuos de aprovechamiento forestal": "Residuos de aprovechamiento forestal",
    "transportes": "Transportes",
}

INVALID_FILTER_VALUES = {"", "0", "Desconocido", "Ninguna / No aplica"}


def _fix_mojibake(value: object) -> object:
    if not isinstance(value, str):
        return value
    try:
        fixed = value.encode("latin-1").decode("utf-8")
        return fixed if fixed != value else value
    except (UnicodeEncodeError, UnicodeDecodeError):
        return unicodedata.normalize("NFKC", value)


def _clean_text(series: pd.Series) -> pd.Series:
    return (
        series.fillna("Desconocido")
        .astype(str)
        .map(_fix_mojibake)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .replace({"": "Desconocido", "0": "Desconocido", "nan": "Desconocido"})
    )


def _canonicalize(series: pd.Series, replacements: dict[str, str]) -> pd.Series:
    lookup = {key.casefold(): value for key, value in replacements.items()}
    return series.map(lambda value: lookup.get(str(value).casefold(), value))


def _fold_text(value: object) -> str:
    normalized = unicodedata.normalize("NFKD", str(value).strip())
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(without_accents.casefold().split())


def _canonicalize_causes(series: pd.Series) -> pd.Series:
    return series.map(lambda value: CAUSE_LABELS.get(_fold_text(value), str(value).strip()))


def load_data(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    try:
        frame = pd.read_csv(path, encoding="utf-8", low_memory=False)
    except UnicodeDecodeError:
        frame = pd.read_csv(path, encoding="latin-1", low_memory=False)

    frame.columns = [column.strip().replace(" ", "_") for column in frame.columns]

    for column in ("Fecha_Inicio", "Fecha_Termino"):
        if column in frame.columns:
            frame[column] = pd.to_datetime(frame[column], errors="coerce", dayfirst=True)

    for column in (
        "anio",
        "latitud",
        "longitud",
        "Total_hectareas",
        "Duracion_dias",
    ):
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    if "anio" in frame.columns:
        frame["anio"] = frame["anio"].astype("Int64")

    if "Total_hectareas" in frame.columns:
        frame["Total_hectareas_num"] = frame["Total_hectareas"].fillna(0).clip(lower=0)
    else:
        frame["Total_hectareas_num"] = 0.0

    for column in TEXT_COLUMNS:
        if column in frame.columns:
            frame[column] = _clean_text(frame[column])

    if "Estado" in frame.columns:
        frame["Estado"] = _canonicalize(
            frame["Estado"],
            {
                "Ciudad De México": "Ciudad de México",
                "México, D.F.": "Ciudad de México",
                "Mexico, D.F.": "Ciudad de México",
                "Distrito Federal": "Ciudad de México",
            },
        )

    if "Region" in frame.columns:
        frame["Region"] = frame["Region"].str.title()

    if "Causa" in frame.columns:
        frame["Causa"] = _canonicalize_causes(frame["Causa"])

    if "Tipo_de_incendio" in frame.columns:
        frame["Tipo_de_incendio"] = frame["Tipo_de_incendio"].str.capitalize()

    return frame


def filter_dataframe(
    frame: pd.DataFrame,
    year: int | str | None = None,
    geo: str | None = "Todos",
    municipality: str | None = "Todos",
    cause: str | None = "Todos",
    fire_size: str | None = "Todos",
) -> pd.DataFrame:
    filtered = frame

    if year not in (None, "Todos"):
        filtered = filtered[filtered["anio"] == int(year)]

    if geo and geo != "Todos":
        kind, _, value = geo.partition("::")
        if kind == "region" and "Region" in filtered.columns:
            filtered = filtered[filtered["Region"] == value]
        elif kind == "estado" and "Estado" in filtered.columns:
            filtered = filtered[filtered["Estado"] == value]

    if municipality and municipality != "Todos" and "Municipio" in filtered.columns:
        filtered = filtered[filtered["Municipio"] == municipality]

    if cause and cause != "Todos" and "Causa" in filtered.columns:
        filtered = filtered[filtered["Causa"] == cause]

    if fire_size and fire_size != "Todos" and "Tamano" in filtered.columns:
        filtered = filtered[filtered["Tamano"] == fire_size]

    return filtered.copy()


def available_values(
    frame: pd.DataFrame,
    column: str,
    *,
    exclude_unknown: bool = True,
) -> list[str]:
    if frame.empty or column not in frame.columns:
        return []

    counts = frame[column].dropna().astype(str).value_counts()
    values: list[str] = []
    for value, count in counts.items():
        if count <= 0:
            continue
        if exclude_unknown and value in INVALID_FILTER_VALUES:
            continue
        values.append(value)
    return sorted(values, key=lambda value: _fold_text(value))


def dropdown_options(values: list[object], include_all: bool = True) -> list[dict[str, object]]:
    options: list[dict[str, object]] = []
    if include_all:
        options.append({"label": "Todos", "value": "Todos"})
    options.extend({"label": value, "value": value} for value in values)
    return options


def build_geo_options(frame: pd.DataFrame) -> list[dict[str, str]]:
    options = [{"label": "Todos", "value": "Todos"}]
    regions = sorted(frame.get("Region", pd.Series(dtype=str)).dropna().unique())
    states = sorted(frame.get("Estado", pd.Series(dtype=str)).dropna().unique())
    options.extend(
        {"label": f"Región · {region}", "value": f"region::{region}"}
        for region in regions
        if region not in {"Desconocido", "Desconocidas"}
    )
    options.extend(
        {"label": f"Estado · {state}", "value": f"estado::{state}"}
        for state in states
        if state not in {"Desconocido", "Desconocidas"}
    )
    return options


def geo_label(value: str | None) -> str:
    if not value or value == "Todos":
        return "Todos"
    _, _, label = value.partition("::")
    return label or value
