"""Estado del modo administrador.

La clave se lee del entorno (`ADMIN_KEY`). Cuando el usuario la introduce
correctamente, guardamos la propia clave en `rx.LocalStorage` para que el
estado "admin" persista entre recargas de la página. La validación de
`is_admin` se hace siempre contra la env var en el servidor — si la clave
cambia (o se elimina) el modo admin se invalida automáticamente.
"""

from __future__ import annotations

import os

import reflex as rx


class AdminState(rx.State):
    """Gestiona la sesión de admin sin sistema de cuentas (single secret key)."""

    # Token persistente en localStorage (= la propia clave admin si fue válida).
    # El servidor revalida contra ADMIN_KEY en cada uso, así que asignarlo a
    # mano no concede privilegios sin la clave real.
    admin_token: str = rx.LocalStorage("")

    # UI / dialog
    key_input: str = ""
    dialog_open: bool = False
    error_message: str = ""

    # ---------------- Computed ----------------

    @rx.var
    def is_admin(self) -> bool:
        admin_key = os.getenv("ADMIN_KEY", "")
        return bool(admin_key) and self.admin_token == admin_key

    @rx.var
    def admin_key_configured(self) -> bool:
        return bool(os.getenv("ADMIN_KEY", ""))

    # ---------------- Event handlers ----------------

    def open_dialog(self) -> None:
        self.dialog_open = True
        self.key_input = ""
        self.error_message = ""

    def set_dialog_open(self, value: bool) -> None:
        self.dialog_open = value
        if not value:
            self.key_input = ""
            self.error_message = ""

    def set_key_input(self, value: str) -> None:
        self.key_input = value
        self.error_message = ""

    def check_admin_key(self):
        """Valida `key_input` contra ADMIN_KEY del entorno y persiste si es OK."""
        admin_key = os.getenv("ADMIN_KEY", "")
        if not admin_key:
            self.error_message = (
                "ADMIN_KEY no está configurada en el servidor."
            )
            return
        if self.key_input == admin_key:
            self.admin_token = self.key_input
            self.dialog_open = False
            self.key_input = ""
            self.error_message = ""
            return rx.toast.success("Modo administrador activado")
        self.error_message = "Clave incorrecta"

    def logout_admin(self):
        self.admin_token = ""
        self.dialog_open = False
        self.key_input = ""
        self.error_message = ""
        return rx.toast("Modo administrador desactivado")
