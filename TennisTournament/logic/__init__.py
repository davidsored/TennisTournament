"""Lógica de negocio pura — sin dependencias de Reflex/SQLModel/DB.

Estos módulos contienen el "engine" del producto: matemáticas de tenis,
algoritmos de emparejamiento, planificación de cuadros, cálculo de
clasificación y agrupación de fixtures. Son funciones deterministas con
firmas explícitas y tipos primitivos / dataclasses, así que se prueban
unitariamente sin necesidad de instanciar State o levantar Postgres.
"""

from .fixtures import (
    FixtureLeg,
    FixtureMatch,
    FixturePairView,
    RoundFixtures,
    group_fixtures,
)
from .players import plan_rename
from .serving import resolve_initial_server
from .standings import MatchResult, StandingsRow, compute_standings
from .validation import (
    validate_competition_config,
    validate_player_name,
    validate_player_names,
)
from .tournament_engine import (
    BYE,
    PLACEHOLDER_PREFIX,
    AdvanceTarget,
    BracketSlot,
    compute_bracket_size,
    decide_winner,
    distribute_byes,
    next_position,
    plan_bracket,
    propagate_winner,
    winner_advance_side,
)

__all__ = [
    # Tournament engine
    "BYE",
    "PLACEHOLDER_PREFIX",
    "AdvanceTarget",
    "BracketSlot",
    "compute_bracket_size",
    "decide_winner",
    "distribute_byes",
    "next_position",
    "plan_bracket",
    "propagate_winner",
    "winner_advance_side",
    # Standings
    "MatchResult",
    "StandingsRow",
    "compute_standings",
    # Fixtures
    "FixtureLeg",
    "FixtureMatch",
    "FixturePairView",
    "RoundFixtures",
    "group_fixtures",
    # Players
    "plan_rename",
    # Serving
    "resolve_initial_server",
    # Validation
    "validate_competition_config",
    "validate_player_name",
    "validate_player_names",
]
