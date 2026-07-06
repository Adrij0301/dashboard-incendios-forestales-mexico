from dash import Dash
import dash_bootstrap_components as dbc

from src.callbacks import register_callbacks
from src.config import APP_TITLE, DATA_PATH, OUTPUTS_DIR
from src.data import load_data
from src.layout import build_layout

OUTPUTS_DIR.mkdir(exist_ok=True)
DATA = load_data(DATA_PATH)

app = Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
    ],
    suppress_callback_exceptions=True,
)
app.title = APP_TITLE
app.layout = build_layout(DATA)
register_callbacks(app, DATA)

server = app.server

if __name__ == "__main__":
    app.run(debug=False)
