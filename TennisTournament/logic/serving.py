"""Lógica pura del saque inicial de un partido.

La rotación de saque por juego vive en `ScoreboardState.sumar_punto`; aquí
solo se decide qué hacer al CARGAR un partido de competición: recuperar la
elección persistida, no preguntar si ya hay progreso, o mostrar el modal.
"""

from __future__ import annotations

STATUS_FINALIZADO = "Finalizado"


def resolve_initial_server(
    initial_server: int | None,
    status: str,
    sets_home: int,
    sets_away: int,
) -> tuple[int, bool]:
    """Decide el sacador al cargar un partido de competición.

    Devuelve `(server_id, server_chosen)`:
      - Elección persistida (1/2) → se recupera y no se vuelve a preguntar.
      - Partido finalizado o con sets acumulados → no preguntar (server_id
        por defecto 1; el desarrollo punto a punto no se persiste).
      - Partido virgen → preguntar (modal).
    """
    if initial_server in (1, 2):
        return initial_server, True
    if status == STATUS_FINALIZADO or (sets_home + sets_away) > 0:
        return 1, True
    return 1, False
