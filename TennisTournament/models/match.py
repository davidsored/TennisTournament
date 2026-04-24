"""Match, Set y Game: modelos persistentes con la lógica completa de puntuación de tenis.

State machine:
- Punto: 0 → 1 → 2 → 3 (visual 0/15/30/40).
- Deuce / Advantage: a partir de 40-40 se requiere diferencia de 2 puntos.
- Set: primer jugador a 6 juegos con diferencia de 2.
- Tie-break: 6-6 activa `is_tiebreak`; primer jugador a 7 puntos con diferencia de 2.
- Match: se cierra al alcanzar la mayoría de `config_sets` (p.ej. 2 de 3, 3 de 5).

Toda la lógica de "quién gana el punto" vive en `Match.add_point(player)`, de modo que el
State de Reflex solo necesita invocar `match.add_point(1)` o `match.add_point(2)`.
"""

from datetime import datetime, timezone
from typing import Optional

import reflex as rx
import sqlmodel


ESTADO_EN_CURSO = "En curso"
ESTADO_FINALIZADO = "Finalizado"

_PUNTOS_VISUALES = {0: "0", 1: "15", 2: "30", 3: "40"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Game(rx.Model, table=True):
    """Registro histórico de un juego ya cerrado."""

    __tablename__ = "games"

    set_id: Optional[int] = sqlmodel.Field(default=None, foreign_key="sets.id")
    winner: int  # 1 o 2
    was_tiebreak: bool = False
    tiebreak_points_j1: int = 0
    tiebreak_points_j2: int = 0
    created_at: datetime = sqlmodel.Field(default_factory=_utcnow)


class Set(rx.Model, table=True):
    """Registro histórico de un set ya cerrado."""

    __tablename__ = "sets"

    match_id: Optional[int] = sqlmodel.Field(default=None, foreign_key="matches.id")
    games_j1: int = 0
    games_j2: int = 0
    had_tiebreak: bool = False
    tiebreak_points_j1: int = 0
    tiebreak_points_j2: int = 0
    winner: int  # 1 o 2
    created_at: datetime = sqlmodel.Field(default_factory=_utcnow)


class Match(rx.Model, table=True):
    """Partido con estado en vivo y state machine de puntuación encapsulada."""

    __tablename__ = "matches"

    # Jugadores
    player_j1: str
    player_j2: str

    # Configuración
    config_sets: int = 3  # al mejor de 3 | 5 | N (impar recomendado)

    # Estado en vivo (enteros internos — el visual se calcula por propiedad)
    puntos_j1: int = 0
    puntos_j2: int = 0
    juegos_j1: int = 0
    juegos_j2: int = 0
    sets_j1: int = 0
    sets_j2: int = 0

    is_tiebreak: bool = False
    estado: str = ESTADO_EN_CURSO

    created_at: datetime = sqlmodel.Field(default_factory=_utcnow)
    finished_at: Optional[datetime] = None

    # ----------------------------- Helpers de lectura -----------------------------

    @property
    def sets_to_win(self) -> int:
        """Sets necesarios para ganar el partido dado `config_sets`."""
        return self.config_sets // 2 + 1

    @property
    def is_finished(self) -> bool:
        return self.estado == ESTADO_FINALIZADO

    @property
    def winner(self) -> Optional[int]:
        if not self.is_finished:
            return None
        return 1 if self.sets_j1 > self.sets_j2 else 2

    @property
    def score_visual_j1(self) -> str:
        return self._format_point(self.puntos_j1, self.puntos_j2)

    @property
    def score_visual_j2(self) -> str:
        return self._format_point(self.puntos_j2, self.puntos_j1)

    def _format_point(self, mine: int, opp: int) -> str:
        """Convierte el entero interno al string visible en el marcador."""
        if self.is_tiebreak:
            return str(mine)
        # Territorio de deuce/ventaja (ambos con al menos 3 puntos = 40)
        if mine >= 3 and opp >= 3:
            if mine == opp:
                return "40"          # Iguales (deuce)
            if mine == opp + 1:
                return "Adv"         # Ventaja propia
            return "40"              # Ventaja rival → yo sigo en 40
        return _PUNTOS_VISUALES.get(mine, "40")

    # --------------------------- State machine: puntuación ---------------------------

    def add_point(self, player: int) -> None:
        """Suma un punto al jugador indicado (1 o 2).

        No hace nada si el partido ya está finalizado. Lanza `ValueError` si el
        identificador no es 1 ni 2 (error de programación, no de usuario).
        """
        if self.is_finished:
            return
        if player not in (1, 2):
            raise ValueError("player debe ser 1 o 2")

        if self.is_tiebreak:
            self._add_tiebreak_point(player)
        else:
            self._add_game_point(player)

    # -- Juego normal --

    def _add_game_point(self, player: int) -> None:
        self._increment_points(player)
        p1, p2 = self.puntos_j1, self.puntos_j2
        # Cierre normal: mínimo 4 puntos y ventaja de 2
        if max(p1, p2) >= 4 and abs(p1 - p2) >= 2:
            self._award_game(1 if p1 > p2 else 2)

    def _award_game(self, player: int) -> None:
        self.puntos_j1 = 0
        self.puntos_j2 = 0
        if player == 1:
            self.juegos_j1 += 1
        else:
            self.juegos_j2 += 1

        g1, g2 = self.juegos_j1, self.juegos_j2
        # Set cerrado (6+ y diferencia de 2, p.ej. 6-4, 7-5)
        if max(g1, g2) >= 6 and abs(g1 - g2) >= 2:
            self._award_set(1 if g1 > g2 else 2)
        # 6-6 → entra tie-break
        elif g1 == 6 and g2 == 6:
            self.is_tiebreak = True

    # -- Tie-break --

    def _add_tiebreak_point(self, player: int) -> None:
        self._increment_points(player)
        p1, p2 = self.puntos_j1, self.puntos_j2
        # Tie-break: primero a 7 con diferencia de 2 (puede extenderse: 8-6, 10-8, ...)
        if max(p1, p2) >= 7 and abs(p1 - p2) >= 2:
            winner = 1 if p1 > p2 else 2
            # El ganador del tie-break se lleva también el juego 7º
            if winner == 1:
                self.juegos_j1 += 1
            else:
                self.juegos_j2 += 1
            self.is_tiebreak = False
            self._award_set(winner)

    # -- Set / Match --

    def _award_set(self, player: int) -> None:
        self.puntos_j1 = 0
        self.puntos_j2 = 0
        self.juegos_j1 = 0
        self.juegos_j2 = 0
        if player == 1:
            self.sets_j1 += 1
        else:
            self.sets_j2 += 1

        if self.sets_j1 >= self.sets_to_win or self.sets_j2 >= self.sets_to_win:
            self.estado = ESTADO_FINALIZADO
            self.finished_at = _utcnow()

    # -- Utilidades internas --

    def _increment_points(self, player: int) -> None:
        if player == 1:
            self.puntos_j1 += 1
        else:
            self.puntos_j2 += 1

    def reset(self) -> None:
        """Reinicia todo el estado en vivo del partido."""
        self.puntos_j1 = self.puntos_j2 = 0
        self.juegos_j1 = self.juegos_j2 = 0
        self.sets_j1 = self.sets_j2 = 0
        self.is_tiebreak = False
        self.estado = ESTADO_EN_CURSO
        self.finished_at = None
