"""Entrypoint de la app: registra páginas, carga Inter + Material Symbols y aplica el tema Advantage."""

import reflex as rx

# Import explícito de modelos rx.Model para que Alembic los detecte al
# generar/aplicar migraciones (`reflex db makemigrations`).
from .models import (  # noqa: F401  - sólo registro de SQLModel metadata
    Game,
    League,
    LeagueMatch,
    Match,
    Set,
    Tournament,
)
from .pages.casual_match import casual_match
from .pages.home import home
from .pages.league import league
from .pages.league_dashboard import league_dashboard
from .pages.scoreboard import scoreboard
from .pages.tournament import tournament
from .pages.tournament_config import tournament_config
from .pages.tournament_dashboard import tournament_dashboard
from .states.admin_state import AdminState
from .states.casual_match_state import CasualMatchState
from .states.config_state import ConfigState
from .states.home_state import HomeState
from .states.league_state import LeagueState
from .states.scoreboard_state import ScoreboardState
from .states.tournament_state import TournamentState


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
app.add_page(
    home,
    route="/",
    title="CourtManager",
    on_load=HomeState.setup_home,
)
app.add_page(
    scoreboard,
    route="/scoreboard",
    title="Marcador en vivo",
    on_load=ScoreboardState.setup_scoreboard,
)
app.add_page(league, route="/league", title="Liga")
app.add_page(tournament, route="/tournament", title="Torneo")
app.add_page(
    tournament_config,
    route="/tournament-config",
    title="Configuración",
    on_load=ConfigState.setup_page,
)
app.add_page(
    league_dashboard,
    route="/league-dashboard",
    title="Liga · Dashboard",
    on_load=LeagueState.setup_dashboard,
)
app.add_page(
    tournament_dashboard,
    route="/tournament-dashboard",
    title="Torneo · Cuadro",
    on_load=TournamentState.setup_view,
)
app.add_page(
    casual_match,
    route="/casual-match",
    title="Partido Amistoso",
    on_load=CasualMatchState.setup_page,
)
