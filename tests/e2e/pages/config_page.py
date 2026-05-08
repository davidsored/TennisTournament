"""ConfigPage — formulario de creación de Liga / Torneo.

Maneja:
- Input "Nombre del Torneo" (placeholder: 'Ej. Torneo de Verano 2024').
- Steppers de Sets / Juegos (botones +/- con aria-label).
- Lista dinámica de jugadores (placeholder: 'Nombre del jugador').
- Botón "Guardar Configuración".
"""

from __future__ import annotations

from playwright.sync_api import expect

from .base_page import BasePage


class ConfigPage(BasePage):
    # Aceptar query para distinguir liga / torneo.
    PATH = "/tournament-config"

    # ----------------- Acciones de formulario -----------------

    def goto_for_league(self) -> "ConfigPage":
        return self.goto(query="?type=league")  # type: ignore[return-value]

    def goto_for_tournament(self) -> "ConfigPage":
        return self.goto(query="?type=tournament")  # type: ignore[return-value]

    def set_name(self, name: str) -> None:
        """Rellena el campo nombre."""
        self.fill_by_placeholder("Ej. Torneo de Verano 2024", name)

    def set_games_per_set(self, target: int) -> None:
        """Ajusta el stepper de 'Juegos por set' al valor `target`."""
        self._adjust_stepper("Juegos por set", target)

    def set_sets_per_match(self, target: int) -> None:
        """Ajusta el stepper de 'Sets por partido' al valor `target`."""
        self._adjust_stepper("Sets por partido", target)

    # ----------------- Helpers internos -----------------

    def _stepper_section(self, label_text: str):
        """Localiza el contenedor (rx.box outer) del stepper indicado.

        Estrategia: encontrar el `<label>` con el texto y subir al primer
        ancestor `<div>` que contenga al menos 2 botones (los del stepper).
        Inmune a cambios menores de classes y wrappers intermedios.
        """
        label_el = self.page.get_by_text(label_text, exact=False).first
        return label_el.locator(
            "xpath=ancestor::div[count(.//button) >= 2][1]"
        )

    def _adjust_stepper(self, label_text: str, target: int) -> None:
        """Itera pulsando − / + hasta llegar al valor objetivo.

        Los botones del stepper son `material_icon("remove")` y
        `material_icon("add")`. No tienen aria-label; el accessible-name
        es el texto del icono ('remove'/'add'). Tomamos los botones por
        posición dentro del stepper:
          - nth(0) → botón − (minus)
          - nth(1) → botón + (plus)
        """
        section = self._stepper_section(label_text)
        # Esperar a que el stepper esté visible para evitar timeouts.
        section.first.wait_for(state="visible", timeout=10_000)
        buttons = section.locator("button")
        minus_btn = buttons.nth(0)
        plus_btn = buttons.nth(1)

        for _ in range(20):  # safety cap
            current = self._read_stepper_value(section)
            if current == target:
                return
            if current < target:
                plus_btn.click()
            else:
                minus_btn.click()
            # Pequeño wait — Reflex actualiza el span por WS.
            self.page.wait_for_timeout(120)

    def add_players(self, players: list[str]) -> None:
        """Rellena la lista de jugadores. Si faltan inputs, pulsa
        'Añadir jugador' antes de seguir escribiendo.
        """
        for i, name in enumerate(players):
            inputs = self.page.get_by_placeholder("Nombre del jugador")
            count = inputs.count()
            if i >= count:
                # Necesitamos un input más → click en "Añadir jugador".
                self.page.get_by_role(
                    "button", name="Añadir jugador"
                ).click()
            self.page.get_by_placeholder("Nombre del jugador").nth(i).fill(name)

    def submit(self) -> None:
        """Confirma el formulario y espera la navegación al dashboard.

        Tras el click, Reflex ejecuta `setup_league` o `setup_tournament` en
        el backend y luego hace `redirect(...)`. Esperamos explícitamente
        a que la URL cambie a `/league-dashboard` o `/tournament-dashboard`
        antes de devolver el control al test — sin esto, el siguiente paso
        intentaría buscar elementos en la pantalla de config aún visible.
        """
        import re

        self.page.get_by_role("button", name="Guardar Configuración").click()
        try:
            self.page.wait_for_url(
                re.compile(r".*/(league|tournament)-dashboard.*"),
                timeout=20_000,
            )
        except Exception:
            # Capturamos evidencia para depurar fallos de validación / state.
            self.page.screenshot(path="debug_submit_no_redirect.png")
            raise

        # Tras el redirect, dar tiempo al hidratado WS del nuevo dashboard.
        self.page.wait_for_timeout(1000)
        try:
            self.page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass

    @staticmethod
    def _read_stepper_value(section_locator) -> int:
        """Extrae el entero mostrado entre los botones del stepper.

        La estructura es: <button>−</button> <span>{N}</span> <button>+</button>.
        Iteramos los spans del stepper y devolvemos el primer texto que sea
        un número entero (descartando spans de iconos como 'add'/'remove').
        """
        spans = section_locator.locator("span")
        n = spans.count()
        for i in range(n):
            text = spans.nth(i).inner_text().strip()
            if text.isdigit():
                return int(text)
        return 0

    def expect_loaded(self) -> None:
        expect(self.page.get_by_text("Detalles del Torneo", exact=False)).to_be_visible()
