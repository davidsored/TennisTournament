"""Lógica pura de gestión de participantes (renombrado).

El plan de renombrado se calcula aquí (validaciones + nueva lista) y la
persistencia transaccional vive en `LeagueState.rename_player`. Los nombres
de jugador están desnormalizados: aparecen en `players_json` de la
competición Y en `home`/`away` de cada `league_matches`, por lo que el
renombrado debe aplicarse en ambos sitios por igualdad exacta.
"""

from __future__ import annotations

from .validation import validate_player_name


def plan_rename(
    players: list[str],
    old_name: str,
    new_name: str,
) -> tuple[list[str] | None, str | None]:
    """Valida un renombrado y devuelve la nueva lista de jugadores.

    Devuelve `(nueva_lista, None)` si es válido o `(None, mensaje_error)`
    si no. Preserva el orden original de la lista.
    """
    new_clean = new_name.strip()

    if err := validate_player_name(new_clean):
        return None, err

    if old_name not in players:
        return None, f'"{old_name}" no está en la lista de participantes'

    if new_clean == old_name:
        return None, "El nombre no ha cambiado"

    # Duplicado case-insensitive contra el resto de participantes.
    others = {p.casefold() for p in players if p != old_name}
    if new_clean.casefold() in others:
        return None, f'Ya existe un participante llamado "{new_clean}"'

    return [new_clean if p == old_name else p for p in players], None
