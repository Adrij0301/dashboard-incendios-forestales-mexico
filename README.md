# Dashboard analítico de incendios forestales en México

Proyecto de la materia **Ciencia de Datos** para analizar los registros históricos de incendios forestales en México entre 2015 y 2024.

## Funcionalidades

- Indicadores de incendios, hectáreas quemadas y entidades.
- Filtros por año, estado o región, municipio, causa y tamaño del incendio.
- Mapa normal, mapa de calor y agrupamiento K-Means.
- Principales causas, distribución de hectáreas, tendencia anual y regresión lineal.
- Top de estados y causas.
- Nubes de palabras de causas y vegetación.
- Descarga de los datos filtrados en CSV.
- Tema claro y oscuro.
- Interfaz de una sola pantalla sin desplazamiento.

## Tecnologías

Python, Dash, Dash Bootstrap Components, Pandas, Plotly, Scikit-learn y WordCloud.

## Estructura

```text
DASHBOARD_JAOC_CD/
├── assets/
│   ├── styles.css
│   └── resize.js
├── data/
│   └── estadisticasincendiosforestales2015-2024.csv
├── outputs/
├── src/
│   ├── callbacks.py
│   ├── config.py
│   ├── data.py
│   ├── figures.py
│   └── layout.py
├── dashboard.py
├── requirements.txt
└── README.md
```

## Ejecución

```powershell
py -m pip install --upgrade -r requirements.txt
py dashboard.py
```

Después abre `http://127.0.0.1:8050` en el navegador.

## Datos

El archivo CSV contiene los registros históricos de incendios forestales en México de 2015 a 2024 e incluye año, entidad, municipio, región, causa, vegetación, coordenadas y superficie afectada.
