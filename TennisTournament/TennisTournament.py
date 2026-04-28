"""Entrypoint de la app: registra páginas, carga Inter + Material Symbols y aplica el tema Advantage."""

import reflex as rx

from .pages.home import home
from .pages.league import league
from .pages.scoreboard import scoreboard
from .pages.tournament import tournament
from .pages.tournament_config import tournament_config
from .states.config_state import ConfigState


app = rx.App(
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
        "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap",
    ],
    style={
        "fontFamily": "Inter, ui-sans-serif, system-ui, sans-serif",
        "backgroundColor": "#f8f9fa",
        "color": "#191c1d",
    },
)
app.add_page(home, route="/", title="CourtManager")
app.add_page(scoreboard, route="/scoreboard", title="Marcador en vivo")
app.add_page(league, route="/league", title="Liga")
app.add_page(tournament, route="/tournament", title="Torneo")
app.add_page(
    tournament_config,
    route="/tournament-config",
    title="Configuración de Torneo",
    on_load=ConfigState.setup_page,
)
