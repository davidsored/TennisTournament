"""Entrypoint de la app: registra páginas, carga Inter y aplica el tema Advantage."""

import reflex as rx

from .pages.home import home
from .pages.league import league
from .pages.scoreboard import scoreboard
from .pages.tournament import tournament


app = rx.App(
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
    ],
    style={
        "fontFamily": "Inter, ui-sans-serif, system-ui, sans-serif",
        "backgroundColor": "#f8f9fa",
        "color": "#191c1d",
    },
)
app.add_page(home, route="/", title="Tennis Tournament")
app.add_page(scoreboard, route="/scoreboard", title="Marcador en vivo")
app.add_page(league, route="/league", title="Liga")
app.add_page(tournament, route="/tournament", title="Torneo")
