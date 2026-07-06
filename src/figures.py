from __future__ import annotations

import base64
import io
from functools import lru_cache

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from wordcloud import WordCloud

from .config import CLUSTER_PALETTE, MAX_MAP_POINTS, RED_PALETTE


def _theme_colors(theme: str) -> tuple[str, str]:
    if theme == "dark":
        return "#E5E7EB", "rgba(255,255,255,0.12)"
    return "#1F2937", "rgba(15,23,42,0.08)"


def style_figure(fig: go.Figure, theme: str = "light") -> go.Figure:
    text_color, grid_color = _theme_colors(theme)
    fig.update_layout(
        autosize=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=text_color, size=10, family="Segoe UI"),
        margin=dict(l=8, r=8, t=12, b=8),
        title_font=dict(size=12, color="#FF8A80" if theme == "dark" else "#D32F2F"),
        legend=dict(font=dict(color=text_color)),
        hoverlabel=dict(
            bgcolor="#17171D" if theme == "dark" else "#FFFFFF",
            font_color="#FFFFFF" if theme == "dark" else "#111827",
            bordercolor="rgba(0,0,0,0)",
        ),
        transition=dict(duration=0),
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        showline=True,
        linecolor=grid_color,
        tickfont=dict(color=text_color),
        title_font=dict(color=text_color),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=grid_color,
        zeroline=False,
        tickfont=dict(color=text_color),
        title_font=dict(color=text_color),
    )
    return fig


def empty_figure(theme: str = "light") -> go.Figure:
    text_color, _ = _theme_colors(theme)
    fig = go.Figure()
    fig.add_annotation(
        text="Sin datos para los filtros seleccionados",
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(color=text_color, size=12),
    )
    return style_figure(fig, theme).update_layout(
        xaxis=dict(visible=False), yaxis=dict(visible=False)
    )


def _map_points(frame: pd.DataFrame) -> pd.DataFrame:
    points = frame.dropna(subset=["latitud", "longitud"]).copy()
    points = points[
        points["latitud"].between(14, 33)
        & points["longitud"].between(-119, -86)
        & ~((points["latitud"] == 0) & (points["longitud"] == 0))
    ]
    if len(points) > MAX_MAP_POINTS:
        points = points.sample(MAX_MAP_POINTS, random_state=42)
    return points


def _marker_sizes(series: pd.Series) -> np.ndarray:
    values = pd.to_numeric(series, errors="coerce").fillna(0).clip(lower=0)
    roots = np.sqrt(values.to_numpy(dtype=float))
    maximum = float(roots.max()) if len(roots) else 0.0
    if maximum <= 0:
        return np.full(len(values), 6.0)
    return 4.0 + (roots / maximum) * 15.0


def _map_style(theme: str) -> str:
    return "carto-darkmatter" if theme == "dark" else "open-street-map"


def map_figure(frame: pd.DataFrame, map_type: str, theme: str) -> go.Figure:
    points = _map_points(frame)
    center = {"lat": 23.6, "lon": -102.5}
    zoom = 4.1
    base_style = _map_style(theme)

    if not points.empty:
        center = {
            "lat": float(points["latitud"].mean()),
            "lon": float(points["longitud"].mean()),
        }
        zoom = 4.15 if points["Estado"].nunique() > 4 else 5.4

    if points.empty:
        fig = go.Figure()
    elif map_type == "calor":
        points["Peso_calor"] = 1.0 + np.log1p(points["Total_hectareas_num"].clip(lower=0))
        fig = px.density_map(
            points,
            lat="latitud",
            lon="longitud",
            z="Peso_calor",
            radius=18,
            center=center,
            zoom=zoom,
            map_style=base_style,
            color_continuous_scale=[
                [0.0, "rgba(255,235,59,0.08)"],
                [0.30, "#fbbf24"],
                [0.62, "#f97316"],
                [1.0, "#b91c1c"],
            ],
            hover_data={
                "Estado": True,
                "Municipio": True,
                "Causa": True,
                "Peso_calor": False,
                "Total_hectareas_num": ":,.2f",
            },
        )
        fig.update_layout(coloraxis_showscale=False)
    elif map_type == "cluster" and len(points) >= 3:
        cluster_count = min(5, len(points))
        coordinates = StandardScaler().fit_transform(points[["latitud", "longitud"]])
        model = KMeans(n_clusters=cluster_count, n_init=5, random_state=42)
        labels = model.fit_predict(coordinates)
        points["Cluster"] = pd.Categorical(
            [f"Grupo {label + 1}" for label in labels],
            categories=[f"Grupo {index + 1}" for index in range(cluster_count)],
            ordered=True,
        )
        fig = px.scatter_map(
            points,
            lat="latitud",
            lon="longitud",
            color="Cluster",
            size="Total_hectareas_num",
            size_max=22,
            center=center,
            zoom=zoom,
            map_style=base_style,
            opacity=0.78,
            color_discrete_sequence=CLUSTER_PALETTE,
            hover_data={
                "Estado": True,
                "Municipio": True,
                "Causa": True,
                "Cluster": True,
                "Total_hectareas_num": ":,.2f",
            },
        )
        fig.update_layout(
            legend=dict(
                title=None,
                orientation="h",
                x=0.5,
                xanchor="center",
                y=0.01,
                yanchor="bottom",
                bgcolor="rgba(17,24,39,0.72)" if theme == "dark" else "rgba(255,255,255,0.80)",
                font=dict(color="#f9fafb" if theme == "dark" else "#111827", size=9),
            )
        )
    else:
        custom_data = np.column_stack(
            [
                points["Estado"].astype(str),
                points["Municipio"].astype(str),
                points["Causa"].astype(str),
                points["Total_hectareas_num"].fillna(0).to_numpy(),
            ]
        )
        fig = go.Figure(
            go.Scattermap(
                lat=points["latitud"],
                lon=points["longitud"],
                mode="markers",
                customdata=custom_data,
                marker=go.scattermap.Marker(
                    size=_marker_sizes(points["Total_hectareas_num"]),
                    color="#C91F1F",
                    opacity=0.74,
                ),
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "Municipio: %{customdata[1]}<br>"
                    "Causa: %{customdata[2]}<br>"
                    "Hectáreas: %{customdata[3]:,.2f}<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        autosize=True,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=map_type == "cluster" and not points.empty,
        map=dict(
            style=base_style,
            center=center,
            zoom=zoom,
        ),
        uirevision=f"mapa-incendios-{map_type}",
        transition=dict(duration=0),
    )
    return fig


def cause_bar_figure(frame: pd.DataFrame, theme: str) -> go.Figure:
    if frame.empty:
        return empty_figure(theme)
    data = (
        frame["Causa"]
        .value_counts()
        .head(8)
        .rename_axis("Causa")
        .reset_index(name="Incendios")
    )
    fig = px.bar(
        data,
        x="Incendios",
        y="Causa",
        orientation="h",
        color="Causa",
        color_discrete_sequence=RED_PALETTE,
    )
    return style_figure(fig, theme).update_layout(
        yaxis=dict(autorange="reversed", title=None),
        xaxis=dict(title="Incendios"),
        showlegend=False,
        margin=dict(l=8, r=8, t=2, b=28),
    )


def hectares_pie_figure(frame: pd.DataFrame, theme: str) -> go.Figure:
    if frame.empty or frame["Total_hectareas_num"].sum() <= 0:
        return empty_figure(theme)
    data = (
        frame.groupby("Causa", as_index=False)["Total_hectareas_num"]
        .sum()
        .sort_values("Total_hectareas_num", ascending=False)
    )
    if len(data) > 5:
        others = data.iloc[5:]["Total_hectareas_num"].sum()
        data = data.head(5).copy()
        if others > 0:
            data.loc[len(data)] = ["Otros", others]
    fig = px.pie(
        data,
        names="Causa",
        values="Total_hectareas_num",
        hole=0.58,
        color_discrete_sequence=RED_PALETTE,
    )
    fig = style_figure(fig, theme).update_layout(
        showlegend=True,
        legend=dict(orientation="v", y=0.5, x=0.76, font=dict(size=9)),
        margin=dict(t=0, b=0, l=0, r=0),
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        textfont_size=9,
        domain=dict(x=[0.0, 0.70], y=[0.02, 0.98]),
    )
    return fig


def trend_figure(frame: pd.DataFrame, theme: str) -> go.Figure:
    if frame.empty:
        return empty_figure(theme)
    data = (
        frame.groupby("anio")
        .agg(Incendios=("Causa", "count"), Hectareas=("Total_hectareas_num", "sum"))
        .reset_index()
        .sort_values("anio")
    )
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=data["anio"].astype(int),
            y=data["Incendios"],
            name="Incendios",
            mode="lines+markers",
            line=dict(color="#2196F3", width=2.3),
            marker=dict(size=5),
            fill="tozeroy",
            fillcolor="rgba(33,150,243,0.18)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=data["anio"].astype(int),
            y=data["Hectareas"],
            name="Hectáreas",
            mode="lines+markers",
            line=dict(color="#FF3B3B", width=2.3),
            marker=dict(size=5),
            yaxis="y2",
        )
    )
    text, grid = _theme_colors(theme)
    fig.update_layout(
        autosize=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=text, size=8, family="Segoe UI"),
        margin=dict(l=4, r=5, t=18, b=18),
        yaxis=dict(
            title="Incendios",
            showgrid=True,
            gridcolor=grid,
            showline=False,
            tickfont=dict(color=text),
            title_font=dict(color=text),
        ),
        yaxis2=dict(
            title="Hectáreas",
            overlaying="y",
            side="right",
            showgrid=False,
            tickfont=dict(color=text),
            title_font=dict(color=text),
        ),
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor=grid,
            dtick=2,
            tickfont=dict(color=text),
        ),
        legend=dict(
            orientation="h", y=1.13, x=0.5, xanchor="center", font=dict(size=8, color=text)
        ),
        transition=dict(duration=0),
    )
    return fig


def regression_figure(frame: pd.DataFrame, theme: str) -> go.Figure:
    if frame.empty:
        return empty_figure(theme)
    data = (
        frame.groupby("anio", as_index=False)["Total_hectareas_num"]
        .sum()
        .sort_values("anio")
    )
    years = data["anio"].astype(int)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=years,
            y=data["Total_hectareas_num"],
            mode="markers",
            name="Real",
            marker=dict(color="#2196F3", size=6),
        )
    )
    if len(data) > 1:
        model = LinearRegression().fit(years.to_numpy().reshape(-1, 1), data["Total_hectareas_num"])
        fig.add_trace(
            go.Scatter(
                x=years,
                y=model.predict(years.to_numpy().reshape(-1, 1)),
                mode="lines",
                name="Tendencia",
                line=dict(color="#FF3B3B", width=2),
            )
        )
    return style_figure(fig, theme).update_layout(
        showlegend=False,
        margin=dict(l=4, r=5, t=4, b=18),
        xaxis=dict(dtick=2),
    )


def ranking_figure(frame: pd.DataFrame, column: str, theme: str, scale: str) -> go.Figure:
    if frame.empty or column not in frame.columns:
        return empty_figure(theme)
    data = (
        frame[column]
        .value_counts()
        .head(10)
        .rename_axis(column)
        .reset_index(name="Incendios")
    )
    fig = px.bar(
        data,
        x="Incendios",
        y=column,
        orientation="h",
        color="Incendios",
        color_continuous_scale=scale,
    )
    return style_figure(fig, theme).update_layout(
        yaxis=dict(autorange="reversed", title=None),
        xaxis=dict(title="Incendios"),
        coloraxis_showscale=False,
        margin=dict(l=8, r=8, t=2, b=28),
    )


def _wordcloud_counts(series: pd.Series) -> tuple[tuple[str, int], ...]:
    clean = series.dropna().astype(str)
    clean = clean[~clean.isin(["Desconocido", "Desconocidas", "No Aplica", "0", ""])]
    if clean.empty:
        return ()
    counts = clean.value_counts().head(140)
    return tuple((str(word), int(count)) for word, count in counts.items())


@lru_cache(maxsize=96)
def _cached_wordcloud(counts: tuple[tuple[str, int], ...], colormap: str) -> str:
    if not counts:
        return ""
    cloud = WordCloud(
        background_color=None,
        mode="RGBA",
        width=520,
        height=300,
        max_words=120,
        colormap=colormap,
        collocations=False,
        prefer_horizontal=0.9,
    ).generate_from_frequencies(dict(counts))
    buffer = io.BytesIO()
    cloud.to_image().save(buffer, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")


def wordcloud_data_uri(series: pd.Series, colormap: str) -> str:
    return _cached_wordcloud(_wordcloud_counts(series), colormap)
