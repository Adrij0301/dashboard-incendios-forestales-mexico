from src.config import DATA_PATH
from src.data import filter_dataframe, load_data
from src.figures import map_figure


def test_all_map_modes_render_in_light_and_dark():
    frame = filter_dataframe(load_data(DATA_PATH), year=2024)

    for map_type in ("normal", "calor", "cluster"):
        light = map_figure(frame, map_type, "light")
        dark = map_figure(frame, map_type, "dark")

        assert light.data
        assert dark.data
        assert light.layout.map.style == "open-street-map"
        assert dark.layout.map.style == "carto-darkmatter"

    assert len(map_figure(frame, "cluster", "light").data) >= 2
