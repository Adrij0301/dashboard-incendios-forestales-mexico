from src.config import DATA_PATH
from src.data import filter_dataframe, load_data


def test_dataset_loads():
    frame = load_data(DATA_PATH)
    assert not frame.empty
    assert {"anio", "Estado", "Municipio", "Causa", "Total_hectareas_num"}.issubset(frame.columns)


def test_filters_return_expected_year():
    frame = load_data(DATA_PATH)
    filtered = filter_dataframe(frame, year=2024)
    assert not filtered.empty
    assert filtered["anio"].dropna().eq(2024).all()


def test_cause_labels_are_canonical_and_valid_for_latest_year():
    frame = load_data(DATA_PATH)
    causes = set(frame["Causa"].dropna())

    assert "Actividades Ilícitas" not in causes
    assert "actividades ilícitas" not in causes
    assert "Quema de Basureros" not in causes
    assert "intencional" not in causes

    latest_year = int(frame["anio"].dropna().max())
    latest = filter_dataframe(frame, year=latest_year)
    for cause in latest["Causa"].dropna().unique():
        assert not filter_dataframe(frame, year=latest_year, cause=cause).empty
