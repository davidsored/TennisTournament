"""Validación pura de configuración de competiciones.

Estas reglas se aplican en dos capas: en `ConfigState.save_config` (para dar
feedback inmediato al usuario) y en los mutadores `LeagueState.setup_league` /
`setup_tournament` (defensa server-side: en Reflex cualquier handler público
es invocable desde el cliente, así que la UI no basta como barrera).
"""

from __future__ import annotations

from .tournament_engine import BYE, PLACEHOLDER_PREFIX

VALID_SETS = (1, 3, 5, 7, 9)
MIN_GAMES = 1
MAX_GAMES = 12


def validate_competition_config(
    name: str,
    players: list[str],
    sets_per_match: int,
    games_per_set: int,
) -> str | None:
    """Valida los datos de creación de una competición.

    Devuelve `None` si todo es válido, o un mensaje de error listo para
    mostrar en un toast.
    """
    if not name or not name.strip():
        return "Por favor, introduce un nombre para la competición"

    clean = [p.strip() for p in players if p.strip()]
    if len(clean) < 2:
        return "Añade al menos 2 jugadores para crear la competición"

    if sets_per_match not in VALID_SETS:
        return "El número de sets debe ser impar (1, 3, 5, 7 o 9)"

    if not MIN_GAMES <= games_per_set <= MAX_GAMES:
        return f"Los juegos por set deben estar entre {MIN_GAMES} y {MAX_GAMES}"

    return validate_player_names(clean)


def validate_player_names(players: list[str]) -> str | None:
    """Valida una lista de nombres ya limpios (sin vacíos).

    Rechaza duplicados (case-insensitive) y nombres reservados que romperían
    la semántica del bracket de torneo (BYE, "Ganador Partido N").
    """
    seen: set[str] = set()
    for p in players:
        key = p.casefold()
        if key in seen:
            return f'El nombre "{p}" está repetido'
        seen.add(key)

    for p in players:
        if err := validate_player_name(p):
            return err

    return None


def validate_player_name(name: str) -> str | None:
    """Valida un único nombre de jugador (ya con strip aplicado)."""
    if not name:
        return "El nombre no puede estar vacío"
    if name.casefold() == BYE.casefold():
        return f'"{BYE}" es un nombre reservado'
    if name.startswith(PLACEHOLDER_PREFIX):
        return f'Los nombres no pueden empezar por "{PLACEHOLDER_PREFIX}"'
    return None
