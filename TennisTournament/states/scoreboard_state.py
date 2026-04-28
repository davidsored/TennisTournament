"""Estado del marcador en vivo.

La lógica de puntuación vive en `models/match.py` (clase `Match`). Aquí mantenemos
un espejo reactivo de sus campos para que Reflex pueda renderizar cambios; cada
acción reconstruye una instancia transitoria de `Match`, delega en `add_point()`
y vuelca el resultado al state. Así el state nunca duplica reglas.
"""

from __future__ import annotations

import json

import reflex as rx

from ..models.match import ESTADO_EN_CURSO, ESTADO_FINALIZADO, Match


class ScoreboardState(rx.State):
    """Marcador en vivo. Espejo reactivo del modelo `Match`."""

    # ---- Identidad y contexto del partido ----
    player_j1: str = ""
    player_j2: str = ""
    config_sets: int = 3

    match_title: str = "Nuevo partido"
    match_subtitle: str = "Pista Central • 1h 45m"

    # ---- Estado en vivo (espejo de Match) ----
    puntos_j1: int = 0
    puntos_j2: int = 0
    juegos_j1: int = 0
    juegos_j2: int = 0
    sets_j1: int = 0
    sets_j2: int = 0
    is_tiebreak: bool = False
    estado: str = ESTADO_EN_CURSO

    # Histórico de sets cerrados [[j1, j2], ...] para columnas S1/S2/...
    set_history: list[list[int]] = []

    # Servidor activo (1 ó 2). Rota tras cada juego cerrado.
    server_id: int = 1

    # Pila de snapshots (JSON) para soportar deshacer la última acción.
    history: list[str] = []

    # ---------------- Helpers internos ----------------

    def _snapshot(self) -> str:
        """Serializa el estado completo en una cadena JSON (entra a la pila de undo)."""
        return json.dumps(
            {
                "puntos_j1": self.puntos_j1,
                "puntos_j2": self.puntos_j2,
                "juegos_j1": self.juegos_j1,
                "juegos_j2": self.juegos_j2,
                "sets_j1": self.sets_j1,
                "sets_j2": self.sets_j2,
                "is_tiebreak": self.is_tiebreak,
                "estado": self.estado,
                "set_history": [list(s) for s in self.set_history],
                "server_id": self.server_id,
            }
        )

    def _restore(self, snap_json: str) -> None:
        snap = json.loads(snap_json)
        self.puntos_j1 = snap["puntos_j1"]
        self.puntos_j2 = snap["puntos_j2"]
        self.juegos_j1 = snap["juegos_j1"]
        self.juegos_j2 = snap["juegos_j2"]
        self.sets_j1 = snap["sets_j1"]
        self.sets_j2 = snap["sets_j2"]
        self.is_tiebreak = snap["is_tiebreak"]
        self.estado = snap["estado"]
        self.set_history = [list(s) for s in snap["set_history"]]
        self.server_id = snap["server_id"]

    def _build_match(self) -> Match:
        """Reconstruye una instancia transitoria de `Match` con el estado actual."""
        m = Match(
            player_j1=self.player_j1,
            player_j2=self.player_j2,
            config_sets=self.config_sets,
        )
        m.puntos_j1 = self.puntos_j1
        m.puntos_j2 = self.puntos_j2
        m.juegos_j1 = self.juegos_j1
        m.juegos_j2 = self.juegos_j2
        m.sets_j1 = self.sets_j1
        m.sets_j2 = self.sets_j2
        m.is_tiebreak = self.is_tiebreak
        m.estado = self.estado
        return m

    def _sync_from(self, m: Match) -> None:
        self.puntos_j1 = m.puntos_j1
        self.puntos_j2 = m.puntos_j2
        self.juegos_j1 = m.juegos_j1
        self.juegos_j2 = m.juegos_j2
        self.sets_j1 = m.sets_j1
        self.sets_j2 = m.sets_j2
        self.is_tiebreak = m.is_tiebreak
        self.estado = m.estado

    # ---------------- Computed vars (UI) ----------------

    @rx.var
    def score_visual_j1(self) -> str:
        return self._build_match().score_visual_j1

    @rx.var
    def score_visual_j2(self) -> str:
        return self._build_match().score_visual_j2

    @rx.var
    def estado_label(self) -> str:
        return "Finalizado" if self.estado == ESTADO_FINALIZADO else "En Juego"

    @rx.var
    def current_set_label(self) -> str:
        return f"Set {self.sets_j1 + self.sets_j2 + 1}"

    @rx.var
    def set_labels(self) -> list[str]:
        return [f"S{i + 1}" for i in range(len(self.set_history))]

    @rx.var
    def sets_view_j1(self) -> list[dict[str, int]]:
        return [{"mine": s[0], "opp": s[1]} for s in self.set_history]

    @rx.var
    def sets_view_j2(self) -> list[dict[str, int]]:
        return [{"mine": s[1], "opp": s[0]} for s in self.set_history]

    @rx.var
    def is_server_j1(self) -> bool:
        return self.server_id == 1

    @rx.var
    def is_server_j2(self) -> bool:
        return self.server_id == 2

    @rx.var
    def is_finished(self) -> bool:
        return self.estado == ESTADO_FINALIZADO

    # ---------------- Event handlers ----------------

    def sumar_punto(self, player_id: int) -> None:
        """Suma un punto delegando en `Match.add_point` (lógica encapsulada).

        Antes de ejecutar la acción guarda un snapshot completo del estado para
        poder deshacerla con `undo_point`. Tras el punto, si se ha cerrado un
        juego (incluido el cierre de set o tie-break) rota el servidor.
        """
        if self.estado == ESTADO_FINALIZADO:
            return

        # 1) Empuja snapshot a la pila de undo ANTES de mutar el estado.
        self.history.append(self._snapshot())

        m = self._build_match()

        sets_before = (m.sets_j1, m.sets_j2)
        games_before = (m.juegos_j1, m.juegos_j2)
        games_total_before = games_before[0] + games_before[1]
        was_tiebreak = m.is_tiebreak

        m.add_point(player_id)

        set_closed = (m.sets_j1, m.sets_j2) != sets_before
        games_total_after = m.juegos_j1 + m.juegos_j2

        # 2) Cierre de set → registrar marcador final en el histórico.
        if set_closed:
            winner = 1 if m.sets_j1 > sets_before[0] else 2
            if was_tiebreak:
                final_j1 = 7 if winner == 1 else 6
                final_j2 = 7 if winner == 2 else 6
            else:
                final_j1 = games_before[0] + (1 if winner == 1 else 0)
                final_j2 = games_before[1] + (1 if winner == 2 else 0)
            self.set_history.append([final_j1, final_j2])

        # 3) ¿Se ha cerrado un juego?
        #    - Cierre de set ⇒ el último juego del set quedó cerrado.
        #    - Cierre normal ⇒ la suma de juegos del set actual aumenta.
        #    Dentro de un tie-break en curso (sin cerrar set) NO rotamos: el
        #    tie-break se considera un único juego.
        game_closed = set_closed or (games_total_after > games_total_before)
        if game_closed:
            self.server_id = 2 if self.server_id == 1 else 1

        self._sync_from(m)

    def undo_point(self) -> None:
        """Restaura el último snapshot (deshace la última acción registrada)."""
        if not self.history:
            return
        self._restore(self.history.pop())

    def reset_match(self) -> None:
        self.puntos_j1 = self.puntos_j2 = 0
        self.juegos_j1 = self.juegos_j2 = 0
        self.sets_j1 = self.sets_j2 = 0
        self.is_tiebreak = False
        self.estado = ESTADO_EN_CURSO
        self.set_history = []
        self.history = []
        self.server_id = 1

    def toggle_server(self) -> None:
        self.server_id = 2 if self.server_id == 1 else 1
