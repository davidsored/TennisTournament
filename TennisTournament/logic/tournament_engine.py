"""Lógica pura para construir y avanzar cuadros eliminatorios.

Sin dependencias de Reflex ni de la DB. Se opera sobre dataclasses con datos
primitivos. La capa de persistencia (LeagueState.setup_tournament) consume
estos resultados y mapea cada `BracketSlot` a una fila `LeagueMatch` en
Postgres.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


# Constantes de dominio
BYE = "BYE"
STATUS_PENDIENTE = "Pendiente"
STATUS_FINALIZADO = "Finalizado"
PLACEHOLDER_PREFIX = "Ganador Partido"


@dataclass
class BracketSlot:
    """Una posición del cuadro antes de persistir.

    Contiene todo lo que la capa DB necesita para crear un `LeagueMatch`,
    más el `local_index` que se usa SOLO para etiquetar visualmente las
    rondas avanzadas (independiente del id global de Postgres).
    """

    round_num: int
    bracket_position: int
    local_index: int  # 1..N; reset a 1 por torneo nuevo
    home: str = ""
    away: str = ""
    status: str = STATUS_PENDIENTE
    sets_home: int = 0
    sets_away: int = 0
    is_placeholder: bool = False


@dataclass
class AdvanceTarget:
    """Resultado puro de aplicar un avance al match destino."""

    home: str
    away: str
    is_placeholder: bool


# ---------------------------------------------------------------------------
# Cálculos puros
# ---------------------------------------------------------------------------


def compute_bracket_size(n_players: int) -> int:
    """Siguiente potencia de 2 ≥ n_players. Devuelve 0 si n_players < 2."""
    if n_players < 2:
        return 0
    size = 1
    while size < n_players:
        size *= 2
    return size


def distribute_byes(real_players: list[str], bracket_size: int) -> list[str]:
    """Inserta BYEs entre jugadores reales para que cada BYE quede emparejado
    con un real (nunca BYE vs BYE). Asume que `real_players` ya viene shuffled
    si se quiere sorteo aleatorio.
    """
    n_real = len(real_players)
    if bracket_size < n_real:
        raise ValueError("bracket_size < número de jugadores reales")
    n_byes = bracket_size - n_real
    seeding: list[str] = []
    for i in range(n_byes):
        seeding.append(real_players[i])
        seeding.append(BYE)
    for i in range(n_byes, n_real):
        seeding.append(real_players[i])
    return seeding


def winner_advance_side(bracket_position: int) -> str:
    """`'home'` si la posición del partido origen es par; `'away'` si es impar."""
    return "home" if bracket_position % 2 == 0 else "away"


def next_position(
    round_num: int, bracket_position: int, total_rounds: int
) -> Optional[tuple[int, int]]:
    """Devuelve (round_num+1, bracket_position//2) o None si es la final."""
    if round_num >= total_rounds:
        return None
    return (round_num + 1, bracket_position // 2)


def decide_winner(
    home: str, away: str, sets_home: int, sets_away: int
) -> Optional[str]:
    """Devuelve el nombre del ganador, o None si empate / partido no resuelto."""
    if sets_home == sets_away:
        return None
    return home if sets_home > sets_away else away


def plan_bracket(seeding: list[str], sets_per_match: int) -> list[BracketSlot]:
    """Construye TODOS los slots del cuadro a partir de un seeding ya con BYEs.

    Aplica:
      1. Generación de slots por ronda (ronda 1 → final) con índice local 1..N.
      2. Población de Ronda 1 con seeding y auto-finalización de BYEs.
      3. Propagación de ganadores BYE a Ronda 2.
      4. Etiquetado de slots vacíos en rondas avanzadas con
         "Ganador Partido <local_index>" (basado SIEMPRE en el índice local).

    No persiste nada — la capa DB toma esta lista y crea los `LeagueMatch`
    correspondientes.
    """
    bracket_size = len(seeding)
    if bracket_size < 2 or (bracket_size & (bracket_size - 1)) != 0:
        raise ValueError("seeding debe tener tamaño potencia de 2 ≥ 2")

    total_rounds = int(math.log2(bracket_size))
    winner_set_count = sets_per_match // 2 + 1

    # Fase 1: crear slots por ronda con índice local incremental.
    slots_by_round: list[list[BracketSlot]] = []
    local_counter = 0
    for r in range(total_rounds):
        n_in_round = bracket_size // (2 ** (r + 1))
        round_slots: list[BracketSlot] = []
        for p in range(n_in_round):
            local_counter += 1
            round_slots.append(
                BracketSlot(
                    round_num=r + 1,
                    bracket_position=p,
                    local_index=local_counter,
                    is_placeholder=(r > 0),
                )
            )
        slots_by_round.append(round_slots)

    # Fase 2: poblar Ronda 1 con seeding (auto-finalizando BYEs).
    for p, s in enumerate(slots_by_round[0]):
        s.home = seeding[p * 2]
        s.away = seeding[p * 2 + 1]
        s.is_placeholder = False
        if s.home == BYE and s.away != BYE:
            s.status = STATUS_FINALIZADO
            s.sets_home = 0
            s.sets_away = winner_set_count
        elif s.away == BYE and s.home != BYE:
            s.status = STATUS_FINALIZADO
            s.sets_home = winner_set_count
            s.sets_away = 0

    # Fase 3: propagar ganadores BYE de Ronda 1 a Ronda 2.
    if total_rounds >= 2:
        for s in slots_by_round[0]:
            if s.status != STATUS_FINALIZADO:
                continue
            winner = decide_winner(s.home, s.away, s.sets_home, s.sets_away)
            if not winner or winner == BYE:
                continue
            target_pos = s.bracket_position // 2
            target = slots_by_round[1][target_pos]
            side = winner_advance_side(s.bracket_position)
            if side == "home":
                target.home = winner
            else:
                target.away = winner
            if target.home and target.away:
                target.is_placeholder = False

    # Fase 4: rellenar slots vacíos con etiquetas basadas en local_index.
    for r in range(1, total_rounds):
        for p, s in enumerate(slots_by_round[r]):
            prev_a = slots_by_round[r - 1][p * 2]
            prev_b = slots_by_round[r - 1][p * 2 + 1]
            if not s.home:
                s.home = f"{PLACEHOLDER_PREFIX} {prev_a.local_index}"
            if not s.away:
                s.away = f"{PLACEHOLDER_PREFIX} {prev_b.local_index}"

    # Aplanar (los slots están en orden de creación = orden de inserción DB).
    return [s for round_slots in slots_by_round for s in round_slots]


def propagate_winner(
    source_bracket_position: int,
    winner_name: str,
    target_home: str,
    target_away: str,
    target_is_placeholder: bool,
) -> AdvanceTarget:
    """Aplica el avance de un ganador al match siguiente.

    Función pura: recibe el estado del target, devuelve el nuevo estado.
    No muta la entrada. Útil para `LeagueState.record_result` y para tests
    aislados de la lógica de progresión.
    """
    side = winner_advance_side(source_bracket_position)
    new_home = winner_name if side == "home" else target_home
    new_away = winner_name if side == "away" else target_away
    new_placeholder = target_is_placeholder
    if (
        new_home
        and new_away
        and not new_home.startswith(PLACEHOLDER_PREFIX)
        and not new_away.startswith(PLACEHOLDER_PREFIX)
    ):
        new_placeholder = False
    return AdvanceTarget(
        home=new_home, away=new_away, is_placeholder=new_placeholder
    )
