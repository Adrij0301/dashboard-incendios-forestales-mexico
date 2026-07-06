from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = BASE_DIR / "data" / "estadisticasincendiosforestales2015-2024.csv"
OUTPUTS_DIR = BASE_DIR / "outputs"

APP_TITLE = "Dashboard analítico de incendios forestales en México"
DEFAULT_MAP_TYPE = "normal"

MAX_MAP_POINTS = 3_500

CLUSTER_PALETTE = [
    "#dc2626",
    "#f97316",
    "#eab308",
    "#0ea5e9",
    "#8b5cf6",
]

RED_PALETTE = [
    "#7f1d1d",
    "#991b1b",
    "#b91c1c",
    "#dc2626",
    "#ef4444",
    "#f87171",
    "#fca5a5",
]

CAUSE_EMOJIS = {
    "Desconocidas": "❓",
    "Intencional": "🧯",
    "Fumadores": "🚬",
    "Quema de basureros": "🗑️",
    "Fogatas": "🔥",
    "Actividades agrícolas": "🚜",
    "Actividades agropecuarias": "🚜",
    "Actividades pecuarias": "🐄",
    "Naturales": "⚡",
    "Cazadores": "🎯",
    "Otras actividades productivas": "🏭",
    "Transportes": "🚗",
    "Cultivos ilícitos": "🌿",
    "Actividades ilícitas": "🚫",
    "Otras causas": "🔥",
    "Residuos de aprovechamiento forestal": "🪵",
    "Festividades y rituales": "🎆",
    "Limpias de derecho de vía": "🛣️",
}
