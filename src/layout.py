from __future__ import annotations

import pandas as pd
from dash import dcc, html
import dash_bootstrap_components as dbc

from .data import available_values, build_geo_options, dropdown_options, filter_dataframe
from .figures import (
    cause_bar_figure,
    hectares_pie_figure,
    map_figure,
    ranking_figure,
    regression_figure,
    trend_figure,
)

GRAPH_CONFIG = {
    "displayModeBar": False,
    "displaylogo": False,
    "responsive": True,
}

MAP_CONFIG = {
    "scrollZoom": True,
    "displayModeBar": False,
    "displaylogo": False,
    "responsive": True,
}


def _dropdown(component_id: str, options: list[dict], value: object) -> html.Div:
    return html.Div(
        className="dropdown-shell",
        children=dcc.Dropdown(
            id=component_id,
            options=options,
            value=value,
            clearable=False,
            searchable=True,
            className="custom-dropdown",
            style={"width": "100%", "height": "44px"},
        ),
    )


def _filter_control(label: str, dropdown: html.Div) -> html.Div:
    return html.Div(
        className="filter-wrapper",
        children=[html.Span(label, className="filter-label-text"), dropdown],
    )


def _sidebar(initial_year_frame: pd.DataFrame) -> html.Div:
    return html.Div(
        className="sidebar",
        children=[
            html.Div(html.I(className="fas fa-bars"), className="menu-icon-box sidebar-main-icon"),
            html.Div(
                className="menu-icon-box",
                children=[
                    html.I(className="fas fa-chart-pie"),
                    html.Div(
                        className="hover-popup",
                        children=[
                            html.H5("Top Estados", className="popup-title"),
                            dcc.Graph(
                                id="hover_graph_1",
                                figure=ranking_figure(initial_year_frame, "Estado", "light", "Oranges"),
                                className="popup-graph",
                                config=GRAPH_CONFIG,
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="menu-icon-box",
                children=[
                    html.I(className="fas fa-fire-alt"),
                    html.Div(
                        className="hover-popup",
                        children=[
                            html.H5("Top Causas", className="popup-title"),
                            dcc.Graph(
                                id="hover_graph_2",
                                figure=ranking_figure(initial_year_frame, "Causa", "light", "Reds"),
                                className="popup-graph",
                                config=GRAPH_CONFIG,
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="menu-icon-box",
                children=[
                    html.I(className="fas fa-comment-dots"),
                    html.Div(
                        className="hover-popup wordcloud-popup",
                        children=[
                            html.H5("Nube de palabras", className="popup-title"),
                            html.Img(id="wc_causa_img", className="wordcloud-image"),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="menu-icon-box",
                children=[
                    html.I(className="fas fa-leaf"),
                    html.Div(
                        className="hover-popup wordcloud-popup",
                        children=[
                            html.H5("Vegetación", className="popup-title"),
                            html.Img(id="wc_veg_img", className="wordcloud-image"),
                        ],
                    ),
                ],
            ),
            html.Div(
                className="sidebar-footer",
                children=[
                    html.Div("© JAOC", className="author-label"),
                    html.Div(
                        className="theme-control",
                        title="Cambiar tema",
                        children=[
                            html.I(className="fas fa-gear theme-gear"),
                            dbc.Switch(id="theme-switch", value=False, className="theme-switch"),
                        ],
                    ),
                ],
            ),
        ],
    )


def _header() -> html.Div:
    return html.Div(
        className="row-header",
        children=[
            html.Div(
                className="glass-box header-title-card",
                children=[
                    html.H1("Dashboard analítico de incendios forestales en México"),
                    html.P("Registros históricos 2015-2024"),
                ],
            ),
            html.Div(
                className="glass-box kpi-card",
                children=[
                    html.Span("INCENDIOS TOTALES", className="kpi-label"),
                    html.H3(id="kpi_incendios", className="kpi-val"),
                ],
            ),
            html.Div(
                className="glass-box kpi-card",
                children=[
                    html.Span("HECTÁREAS QUEMADAS", className="kpi-label"),
                    html.H3(id="kpi_hectareas", className="kpi-val"),
                ],
            ),
            html.Div(
                className="glass-box kpi-card",
                children=[
                    html.Span("ENTIDADES", className="kpi-label"),
                    html.H3(id="kpi_entidades", className="kpi-val"),
                ],
            ),
            html.Div(
                className="header-actions-card",
                children=[
                    html.Button(
                        [html.I(className="fas fa-rotate-left"), html.Span("Limpiar")],
                        id="btn_clear",
                        className="dashboard-button clear-button",
                    ),
                    html.Button(
                        [html.I(className="fas fa-download"), html.Span("Descargar CSV")],
                        id="btn_download",
                        className="dashboard-button download-button",
                    ),
                    dcc.Download(id="download_csv"),
                ],
            ),
        ],
    )


def _filters(frame: pd.DataFrame, latest_year: int) -> html.Div:
    years = sorted(int(year) for year in frame["anio"].dropna().unique())
    initial_frame = filter_dataframe(frame, year=latest_year)
    causes = available_values(initial_frame, "Causa", exclude_unknown=False)
    sizes = available_values(frame, "Tamano")
    year_options = [{"label": "Todos", "value": "Todos"}] + [
        {"label": str(year), "value": year} for year in years
    ]

    return html.Div(
        className="row-filters",
        children=[
            html.Div(
                className="glass-box filters-box filter-card-a",
                children=[
                    _filter_control("AÑO", _dropdown("f_anio", year_options, latest_year)),
                    _filter_control(
                        "ESTADO / REGIÓN",
                        _dropdown("f_geo", build_geo_options(frame), "Todos"),
                    ),
                ],
            ),
            html.Div(
                className="glass-box filters-box filter-card-b",
                children=[
                    _filter_control(
                        "MUNICIPIO",
                        _dropdown("f_municipio", [{"label": "Todos", "value": "Todos"}], "Todos"),
                    ),
                    _filter_control("CAUSA", _dropdown("f_causa", dropdown_options(causes), "Todos")),
                ],
            ),
            html.Div(
                className="glass-box filters-box filter-card-c",
                children=[
                    _filter_control(
                        "TAMAÑO DE INCENDIO",
                        _dropdown("f_tamano", dropdown_options(sizes), "Todos"),
                    ),
                    _filter_control(
                        "TIPO DE MAPA",
                        _dropdown(
                            "f_mapa",
                            [
                                {"label": "Normal", "value": "normal"},
                                {"label": "Mapa de calor", "value": "calor"},
                                {"label": "Cluster (K-means)", "value": "cluster"},
                            ],
                            "normal",
                        ),
                    ),
                ],
            ),
        ],
    )


def _middle(initial_year_frame: pd.DataFrame) -> html.Div:
    return html.Div(
        className="row-middle",
        children=[
            html.Div(
                className="glass-box map-card",
                children=[
                    html.Div("DISTRIBUCIÓN GEOGRÁFICA", className="map-title-float"),
                    dcc.Graph(
                        id="main_map",
                        figure=map_figure(initial_year_frame, "normal", "light"),
                        className="full-graph",
                        config=MAP_CONFIG,
                    ),
                ],
            ),
            html.Div(
                className="glass-box causes-panel",
                children=[
                    html.Label(
                        id="label_causas_titulo",
                        children="PRINCIPALES CAUSAS",
                        className="section-title",
                    ),
                    html.Div(id="grid_causas_container", className="causes-grid"),
                ],
            ),
        ],
    )


def _bottom(initial_year_frame: pd.DataFrame, full_frame: pd.DataFrame) -> html.Div:
    return html.Div(
        className="row-bottom",
        children=[
            html.Div(
                className="glass-box chart-card",
                children=[
                    html.Label(id="label_barras_titulo", children="CAUSAS", className="section-title"),
                    dcc.Graph(
                        id="graph_barras",
                        figure=cause_bar_figure(initial_year_frame, "light"),
                        className="chart-graph",
                        config=GRAPH_CONFIG,
                    ),
                ],
            ),
            html.Div(
                className="glass-box chart-card",
                children=[
                    html.Label(id="label_pastel_titulo", children="HECTÁREAS", className="section-title"),
                    dcc.Graph(
                        id="graph_pastel",
                        figure=hectares_pie_figure(initial_year_frame, "light"),
                        className="chart-graph",
                        config=GRAPH_CONFIG,
                    ),
                ],
            ),
            html.Div(
                className="glass-box trends-card",
                children=[
                    html.Div(
                        className="trends-column",
                        children=[
                            html.Div(
                                className="trend-block",
                                children=[
                                    html.Label("TENDENCIA ANUAL", className="section-title mini-title"),
                                    dcc.Graph(
                                        id="graph_linea",
                                        figure=trend_figure(full_frame, "light"),
                                        className="trend-graph",
                                        config=GRAPH_CONFIG,
                                    ),
                                ],
                            ),
                            html.Div(
                                className="trend-block",
                                children=[
                                    html.Label("PREDICCIÓN (REGRESIÓN)", className="section-title mini-title"),
                                    dcc.Graph(
                                        id="graph_scatter",
                                        figure=regression_figure(full_frame, "light"),
                                        className="trend-graph",
                                        config=GRAPH_CONFIG,
                                    ),
                                ],
                            ),
                        ],
                    )
                ],
            ),
        ],
    )


def build_layout(frame: pd.DataFrame) -> html.Div:
    latest_year = int(frame["anio"].dropna().max())
    initial_year_frame = filter_dataframe(frame, year=latest_year)
    return html.Div(
        id="main-container",
        className="main-layout",
        **{"data-theme": "light"},
        children=[
            _sidebar(initial_year_frame),
            html.Div(
                className="content-area",
                children=[
                    _header(),
                    _filters(frame, latest_year),
                    _middle(initial_year_frame),
                    _bottom(initial_year_frame, frame),
                ],
            ),
        ],
    )
