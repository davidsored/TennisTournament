"""Estado del marcador en vivo.

La lógica de puntuación vive en `models/match.py` (clase `Match`). Aquí mantenemos
un espejo reactivo de sus campos para que Reflex pueda renderizar cambios; cada
acción reconstruye una instancia transitoria de `Match`, delega en `add_point()`
y vuelca el resultado al state. Así el state nunca duplica reglas.
"""

from __future__ import annotations

import json

import reflex as rx

from ..logic.serving import resolve_initial_server
from ..models.league import League
from ..models.league_match import LeagueMatch
from ..models.match import ESTADO_EN_CURSO, ESTADO_FINALIZADO, Match
from ..models.tournament import Tournament
from .league_state import LeagueState


class ScoreboardState(rx.State):
    """Marcador en vivo. Espejo reactivo del modelo `Match`."""

    # ---- Identidad y contexto del partido ----
    player_j1: str = ""
    player_j2: str = ""
    config_sets: int = 3
    config_games: int = 6  # juegos por set elegidos al crear la competición

    match_title: str = "Nuevo partido"
    match_subtitle: str = ""

    # Si > 0, el marcador está jugando un partido concreto de la liga.
    league_match_id: int = 0

    # ID del torneo si el partido viene de un cuadro eliminatorio (vacío si liga).
    # Lo usamos para volver al dashboard correcto al finalizar.
    tournament_id: str = ""

    # True si el partido es "amistoso" (creado desde /casual-match sin DB).
    is_casual: bool = False

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

    # True cuando el sacador inicial ya fue elegido (o recuperado de la DB).
    # Mientras sea False y haya partido cargado, la UI muestra el modal
    # "¿Quién comienza sacando?". Queda FUERA de la pila de undo a propósito:
    # deshacer hasta 0-0 no debe volver a preguntar.
    server_chosen: bool = False

    # Pila de snapshots (JSON) para soportar deshacer la última acción.
    history: list[str] = []

    # ---------------- Lifecycle (on_load) ----------------

    def _reset_all(self) -> None:
        """Resetea el marcador a un estado limpio."""
        self.player_j1 = ""
        self.player_j2 = ""
        self.match_title = "Nuevo partido"
        self.match_subtitle = ""
        self.league_match_id = 0
        self.tournament_id = ""
        self.is_casual = False
        self.config_sets = 3
        self.config_games = 6
        self.puntos_j1 = self.puntos_j2 = 0
        self.juegos_j1 = self.juegos_j2 = 0
        self.sets_j1 = self.sets_j2 = 0
        self.is_tiebreak = False
        self.estado = ESTADO_EN_CURSO
        self.set_history = []
        self.history = []
        self.server_id = 1
        self.server_chosen = False

    async def setup_scoreboard(self):
        """Hidrata el marcador desde los query params de la URL.

        Soporta tres modos:
          - `?match_id=N` → partido de liga/torneo (consulta DB vía LeagueState).
          - `?casual=1&p1=…&p2=…&sets=…&games=…` → partido amistoso.
          - Sin params → marcador vacío.

        Persistencia ante refresco: si los parámetros casuales coinciden con el
        partido ya cargado, NO reseteamos para conservar puntos/juegos/sets.
        """
        params = self.router.page.params

        # --- Modo casual: hidratación desde URL ---
        if params.get("casual", "") == "1":
            p1 = params.get("p1", "").strip() or "Jugador 1"
            p2 = params.get("p2", "").strip() or "Jugador 2"
            try:
                sets = int(params.get("sets", "3"))
                games = int(params.get("games", "6"))
            except (TypeError, ValueError):
                sets, games = 3, 6

            # Refresco con la misma configuración → preserva el progreso.
            same_setup = (
                self.is_casual
                and self.player_j1 == p1
                and self.player_j2 == p2
                and self.config_sets == sets
                and self.config_games == games
            )
            if same_setup:
                return

            self._reset_all()
            self.player_j1 = p1
            self.player_j2 = p2
            self.config_sets = sets
            self.config_games = games
            self.match_title = "Partido Amistoso"
            self.match_subtitle = f"Al mejor de {sets} sets · {games} juegos"
            self.is_casual = True
            return

        # --- Modo competición (liga/torneo) ---
        self._reset_all()

        match_id_param = params.get("match_id", "")
        if not match_id_param:
            return
        try:
            match_id = int(match_id_param)
        except (TypeError, ValueError):
            return

        # Consultas dirigidas: el partido por PK y su competición padre para
        # el título. (Antes se hidrataba TODA la BD y se buscaba en bucles.)
        with rx.session() as session:
            target_match = session.get(LeagueMatch, match_id)
            if target_match is None:
                return
            comp = None
            if target_match.tournament_id is not None:
                comp = session.get(Tournament, target_match.tournament_id)
            elif target_match.league_id is not None:
                comp = session.get(League, target_match.league_id)

        self.player_j1 = target_match.home
        self.player_j2 = target_match.away
        self.league_match_id = match_id
        # Sacador inicial: si ya se eligió (persistido en DB) lo recuperamos;
        # si el partido ya tiene progreso o terminó, no volvemos a preguntar.
        self.server_id, self.server_chosen = resolve_initial_server(
            target_match.initial_server,
            target_match.status,
            target_match.sets_home,
            target_match.sets_away,
        )
        # CRÍTICO: leer el scoring config DESDE EL PARTIDO (desnormalizado en
        # league_matches). Si el match guarda 4 juegos por set, el marcador
        # debe cerrar el set en 4-2/5-3 etc., no en 6-X.
        self.config_sets = target_match.config_sets or (
            comp.sets_per_match if comp else 3
        )
        self.config_games = target_match.config_games or (
            comp.games_per_set if comp else 6
        )
        self.match_title = (comp.name if comp else "") or "Partido"
        # Recordamos el origen del partido para volver al dashboard correcto
        # tras finalizar (torneo vs liga). `tournament_id` se almacena como
        # string para mantenerlo simple en el state; se usa tal cual en la URL.
        if target_match.tournament_id is not None:
            self.tournament_id = str(target_match.tournament_id)
            self.match_subtitle = f"Ronda {target_match.round_num}"
        else:
            self.tournament_id = ""
            leg_label = "Ida" if target_match.leg == 1 else "Vuelta"
            self.match_subtitle = (
                f"Ronda {target_match.round_num} • {leg_label}"
            )

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
        """Reconstruye una instancia transitoria de `Match` con el estado actual.

        IMPORTANTE: pasamos AMBOS `config_sets` y `config_games` al constructor
        para que la state machine de scoring (`Match._award_game`) cierre el
        set en el nº correcto de juegos. Olvidar `config_games` aquí hacía que
        Match cayera al default `=6` y siempre se jugara a 6 juegos por set.
        """
        m = Match(
            player_j1=self.player_j1,
            player_j2=self.player_j2,
            config_sets=self.config_sets,
            config_games=self.config_games,
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
    def show_server_modal(self) -> bool:
        """True mientras falte elegir sacador en un partido cargado y en curso.

        La guarda sobre los nombres evita que el modal aparezca en /scoreboard
        sin query params (marcador vacío).
        """
        return (
            not self.server_chosen
            and self.estado != ESTADO_FINALIZADO
            and bool(self.player_j1)
            and bool(self.player_j2)
        )

    @rx.var
    def is_finished(self) -> bool:
        return self.estado == ESTADO_FINALIZADO

    @rx.var
    def is_in_progress(self) -> bool:
        return self.estado != ESTADO_FINALIZADO

    @rx.var
    def is_league_match(self) -> bool:
        return self.league_match_id > 0

    @rx.var
    def winner_name(self) -> str:
        if self.estado != ESTADO_FINALIZADO:
            return ""
        if self.sets_j1 == self.sets_j2:
            return ""
        return self.player_j1 if self.sets_j1 > self.sets_j2 else self.player_j2

    # ---------------- Event handlers ----------------

    def sumar_punto(self, player_id: int) -> None:
        """Suma un punto delegando en `Match.add_point`.

        IMPORTANTE: aunque al cumplirse la condición de victoria el partido
        pasa a `ESTADO_FINALIZADO`, NO redirigimos automáticamente. Se entra
        en una "fase de revisión": los botones de + Punto se bloquean en la
        UI, pero el usuario aún puede pulsar Deshacer para corregir el último
        punto. La salida real la dispara el botón "Finalizar partido".
        """
        if self.estado == ESTADO_FINALIZADO:
            return

        self.history.append(self._snapshot())

        m = self._build_match()

        sets_before = (m.sets_j1, m.sets_j2)
        games_before = (m.juegos_j1, m.juegos_j2)
        games_total_before = games_before[0] + games_before[1]
        was_tiebreak = m.is_tiebreak

        m.add_point(player_id)

        set_closed = (m.sets_j1, m.sets_j2) != sets_before
        games_total_after = m.juegos_j1 + m.juegos_j2

        if set_closed:
            winner = 1 if m.sets_j1 > sets_before[0] else 2
            if was_tiebreak:
                final_j1 = 7 if winner == 1 else 6
                final_j2 = 7 if winner == 2 else 6
            else:
                final_j1 = games_before[0] + (1 if winner == 1 else 0)
                final_j2 = games_before[1] + (1 if winner == 2 else 0)
            self.set_history.append([final_j1, final_j2])

        game_closed = set_closed or (games_total_after > games_total_before)
        if game_closed:
            self.server_id = 2 if self.server_id == 1 else 1

        self._sync_from(m)
        # Sin redirección automática: la UI consultará `is_finished` para bloquearse.

    async def finish_match(self):
        """Botón manual del footer.

        Solo opera si el partido realmente ha terminado (`is_finished`):
          1) Si es un partido de competición (liga o torneo), persiste el
             resultado vía `LeagueState.record_result` ANTES de redirigir.
          2) Redirige al dashboard correcto según el origen:
             - Torneo (`tournament_id` no vacío) → `/tournament-dashboard?id=…`
             - Liga                              → `/league-dashboard`
          3) Si no proviene de competición, vuelve a la home.
        Si el partido sigue en curso, no hace nada (la UI también lo bloquea).
        """
        if self.estado != ESTADO_FINALIZADO:
            return  # Defensivo: el botón debería estar disabled, pero por si acaso.

        if self.league_match_id > 0:
            league = await self.get_state(LeagueState)
            # Persistir en Postgres ANTES de redirigir.
            league.record_result(
                match_id=self.league_match_id,
                sets_home=self.sets_j1,
                sets_away=self.sets_j2,
            )
            # Redirección inteligente según el origen del partido.
            if self.tournament_id:
                return rx.redirect(
                    f"/tournament-dashboard?id={self.tournament_id}"
                )
            return rx.redirect(
                f"/league-dashboard?id={league.active_competition_id}"
                if league.active_competition_id
                else "/league-dashboard"
            )

        # Partido fuera de competición: vuelve a la home.
        return rx.redirect("/")

    # Alias retro-compatible (por si alguna referencia externa aún lo invoca).
    async def finish_league_match(self):
        return await self.finish_match()

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
        # Reiniciar el partido vuelve a preguntar quién saca.
        self.server_chosen = False

    def choose_server(self, player_id: int) -> None:
        """Fija el sacador inicial elegido en el modal.

        Para partidos de competición persiste la elección en la fila
        `league_matches` (sobrevive a refrescos y queda registrada).
        Los turnos posteriores siguen rotando en `sumar_punto`.
        """
        if player_id not in (1, 2) or self.server_chosen:
            return
        self.server_id = player_id
        self.server_chosen = True

        if self.league_match_id > 0:
            with rx.session() as session:
                m = session.get(LeagueMatch, self.league_match_id)
                if m is not None:
                    m.initial_server = player_id
                    session.add(m)
                    session.commit()
