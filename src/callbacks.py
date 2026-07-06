from __future__ import annotations

import pandas as pd
from dash import Input, Output, State, ctx, dcc, html

from .config import CAUSE_EMOJIS, DEFAULT_MAP_TYPE
from .data import available_values, dropdown_options, filter_dataframe, geo_label
from .figures import (
    cause_bar_figure,
    hectares_pie_figure,
    map_figure,
    ranking_figure,
    regression_figure,
    trend_figure,
    wordcloud_data_uri,
)


def _cause_cards(frame: pd.DataFrame) -> list[html.Div]:
    if frame.empty:
        return [
            html.Div("Sin datos", className="cause-card-mini empty-cause-card")
            for _ in range(6)
        ]

    stats = (
        frame.groupby("Causa")
        .agg(Incendios=("Causa", "count"), Hectareas=("Total_hectareas_num", "sum"))
        .sort_values("Incendios", ascending=False)
        .head(6)
    )
    cards: list[html.Div] = []
    for cause, row in stats.iterrows():
        cards.append(
            html.Div(
                className="cause-card-mini",
                children=[
                    html.Div(
                        className="card-header-row",
                        children=[
                            html.Span(CAUSE_EMOJIS.get(cause, "🔥"), className="card-emoji"),
                            html.Span(cause, className="card-title-text", title=cause),
                        ],
                    ),
                    html.Div(f"{int(row['Incendios']):,} inc.", className="card-stat-row"),
                    html.Div(f"{row['Hectareas']:,.0f} ha", className="card-stat-row"),
                ],
            )
        )
    while len(cards) < 6:
        cards.append(html.Div("—", className="cause-card-mini empty-cause-card"))
    return cards


def register_callbacks(app, frame: pd.DataFrame) -> None:
    years = sorted(int(year) for year in frame["anio"].dropna().unique())
    latest_year = years[-1]

    app.clientside_callback(
        """
        function(darkMode) {
            const dark = Boolean(darkMode);
            const theme = dark ? "dark" : "light";
            const text = dark ? "#E5E7EB" : "#1F2937";
            const grid = dark ? "rgba(255,255,255,0.12)" : "rgba(15,23,42,0.08)";
            const mapStyle = dark ? "carto-darkmatter" : "open-street-map";
            const plotIds = [
                "graph_barras", "graph_pastel", "graph_linea", "graph_scatter",
                "hover_graph_1", "hover_graph_2"
            ];

            document.documentElement.setAttribute("data-theme", theme);
            document.body.setAttribute("data-theme", theme);

            window.requestAnimationFrame(function() {
                if (!window.Plotly) return;
                plotIds.forEach(function(id) {
                    const host = document.getElementById(id);
                    if (!host) return;
                    const plot = host.querySelector(".js-plotly-plot");
                    if (!plot || !plot.data) return;
                    window.Plotly.relayout(plot, {
                        "font.color": text,
                        "legend.font.color": text,
                        "xaxis.tickfont.color": text,
                        "xaxis.title.font.color": text,
                        "xaxis.linecolor": grid,
                        "xaxis.gridcolor": grid,
                        "yaxis.tickfont.color": text,
                        "yaxis.title.font.color": text,
                        "yaxis.gridcolor": grid,
                        "yaxis2.tickfont.color": text,
                        "yaxis2.title.font.color": text,
                        "paper_bgcolor": "rgba(0,0,0,0)",
                        "plot_bgcolor": "rgba(0,0,0,0)"
                    });
                });

                const mapHost = document.getElementById("main_map");
                const mapPlot = mapHost ? mapHost.querySelector(".js-plotly-plot") : null;
                if (mapPlot && mapPlot.data) {
                    window.Plotly.relayout(mapPlot, {"map.style": mapStyle});
                }
            });
            return theme;
        }
        """,
        Output("main-container", "data-theme"),
        Input("theme-switch", "value"),
    )

    @app.callback(
        Output("f_municipio", "options"),
        Output("f_municipio", "value"),
        Input("f_anio", "value"),
        Input("f_geo", "value"),
        Input("btn_clear", "n_clicks"),
        State("f_municipio", "value"),
    )
    def update_municipalities(year, geo, clear_clicks, current_value):
        del clear_clicks
        base = filter_dataframe(frame, year=year, geo=geo)
        values = available_values(base, "Municipio")
        options = dropdown_options(values)
        valid_values = {option["value"] for option in options}
        if ctx.triggered_id in {"btn_clear", "f_geo", "f_anio"} or current_value not in valid_values:
            current_value = "Todos"
        return options, current_value or "Todos"

    @app.callback(
        Output("f_causa", "options"),
        Output("f_causa", "value"),
        Input("f_anio", "value"),
        Input("f_geo", "value"),
        Input("f_municipio", "value"),
        Input("f_tamano", "value"),
        Input("btn_clear", "n_clicks"),
        State("f_causa", "value"),
    )
    def update_causes(year, geo, municipality, fire_size, clear_clicks, current_value):
        del clear_clicks
        base = filter_dataframe(
            frame,
            year=year,
            geo=geo,
            municipality=municipality,
            cause="Todos",
            fire_size=fire_size,
        )
        options = dropdown_options(available_values(base, "Causa", exclude_unknown=False))
        valid_values = {option["value"] for option in options}
        if ctx.triggered_id == "btn_clear" or current_value not in valid_values:
            current_value = "Todos"
        return options, current_value or "Todos"

    @app.callback(
        Output("f_anio", "value"),
        Output("f_geo", "value"),
        Output("f_tamano", "value"),
        Output("f_mapa", "value"),
        Input("btn_clear", "n_clicks"),
        prevent_initial_call=True,
    )
    def clear_filters(_):
        return latest_year, "Todos", "Todos", DEFAULT_MAP_TYPE

    @app.callback(
        Output("download_csv", "data"),
        Input("btn_download", "n_clicks"),
        State("f_anio", "value"),
        State("f_geo", "value"),
        State("f_municipio", "value"),
        State("f_causa", "value"),
        State("f_tamano", "value"),
        prevent_initial_call=True,
    )
    def download_filtered_csv(_, year, geo, municipality, cause, fire_size):
        filtered = filter_dataframe(frame, year, geo, municipality, cause, fire_size)
        year_label = year if year != "Todos" else "2015-2024"
        return dcc.send_data_frame(
            filtered.to_csv,
            f"incendios_forestales_{year_label}.csv",
            index=False,
            encoding="utf-8-sig",
        )

    @app.callback(
        Output("main_map", "figure"),
        Input("f_anio", "value"),
        Input("f_geo", "value"),
        Input("f_municipio", "value"),
        Input("f_causa", "value"),
        Input("f_tamano", "value"),
        Input("f_mapa", "value"),
        State("theme-switch", "value"),
    )
    def update_map(year, geo, municipality, cause, fire_size, map_type, dark_mode):
        filtered = filter_dataframe(frame, year, geo, municipality, cause, fire_size)
        theme = "dark" if dark_mode else "light"
        return map_figure(filtered, map_type, theme)

    @app.callback(
        Output("kpi_incendios", "children"),
        Output("kpi_hectareas", "children"),
        Output("kpi_entidades", "children"),
        Output("label_causas_titulo", "children"),
        Output("grid_causas_container", "children"),
        Output("label_barras_titulo", "children"),
        Output("graph_barras", "figure"),
        Output("label_pastel_titulo", "children"),
        Output("graph_pastel", "figure"),
        Output("graph_linea", "figure"),
        Output("graph_scatter", "figure"),
        Output("hover_graph_1", "figure"),
        Output("hover_graph_2", "figure"),
        Input("f_anio", "value"),
        Input("f_geo", "value"),
        Input("f_municipio", "value"),
        Input("f_causa", "value"),
        Input("f_tamano", "value"),
        State("theme-switch", "value"),
    )
    def update_charts(year, geo, municipality, cause, fire_size, dark_mode):
        theme = "dark" if dark_mode else "light"
        filtered = filter_dataframe(frame, year, geo, municipality, cause, fire_size)
        location = geo_label(geo)
        year_label = year if year != "Todos" else "2015-2024"

        trend_base = filter_dataframe(
            frame,
            year="Todos",
            geo=geo,
            municipality=municipality,
            cause=cause,
            fire_size=fire_size,
        )
        yearly_base = filter_dataframe(frame, year=year)

        return (
            f"{len(filtered):,}",
            f"{filtered['Total_hectareas_num'].sum():,.0f}",
            f"{filtered['Estado'].nunique():,}",
            f"PRINCIPALES CAUSAS ({year_label})",
            _cause_cards(filtered),
            f"CAUSAS ({location})",
            cause_bar_figure(filtered, theme),
            f"HECTÁREAS ({location})",
            hectares_pie_figure(filtered, theme),
            trend_figure(trend_base, theme),
            regression_figure(trend_base, theme),
            ranking_figure(yearly_base, "Estado", theme, "Oranges"),
            ranking_figure(yearly_base, "Causa", theme, "Reds"),
        )

    @app.callback(
        Output("wc_causa_img", "src"),
        Output("wc_veg_img", "src"),
        Input("f_anio", "value"),
        Input("f_geo", "value"),
        Input("f_municipio", "value"),
        Input("f_causa", "value"),
        Input("f_tamano", "value"),
    )
    def update_wordclouds(year, geo, municipality, cause, fire_size):
        filtered = filter_dataframe(frame, year, geo, municipality, cause, fire_size)
        return (
            wordcloud_data_uri(filtered.get("Causa", pd.Series(dtype=str)), "magma"),
            wordcloud_data_uri(filtered.get("Tipo_Vegetacion", pd.Series(dtype=str)), "viridis"),
        )
