"""Page Objects para tests E2E."""

from .base_page import BasePage
from .casual_page import CasualPage
from .config_page import ConfigPage
from .home_page import HomePage
from .league_page import LeaguePage
from .scoreboard_page import ScoreboardPage
from .tournament_page import TournamentPage

__all__ = [
    "BasePage",
    "CasualPage",
    "ConfigPage",
    "HomePage",
    "LeaguePage",
    "ScoreboardPage",
    "TournamentPage",
]
