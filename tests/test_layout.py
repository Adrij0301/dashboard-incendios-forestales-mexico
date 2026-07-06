from dashboard import app


def _components_by_id(layout):
    found = {}
    stack = [layout]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            props = node.get("props", {})
            component_id = props.get("id")
            if component_id:
                found[component_id] = props
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)
    return found


def test_initial_graphs_have_figures():
    response = app.server.test_client().get("/_dash-layout")
    assert response.status_code == 200
    components = _components_by_id(response.get_json())

    for component_id in (
        "main_map",
        "graph_barras",
        "graph_pastel",
        "graph_linea",
        "graph_scatter",
    ):
        figure = components[component_id]["figure"]
        assert figure["data"], component_id


def test_dropdowns_use_full_width_shells():
    response = app.server.test_client().get("/_dash-layout")
    text = response.get_data(as_text=True)
    assert text.count('"dropdown-shell"') == 6


def test_map_type_options_are_present():
    response = app.server.test_client().get("/_dash-layout")
    components = _components_by_id(response.get_json())
    values = {option["value"] for option in components["f_mapa"]["options"]}
    assert values == {"normal", "calor", "cluster"}
