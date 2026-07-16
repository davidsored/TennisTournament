"""Estilo compartido del contenido de los diálogos modales.

Único punto de verdad para el "shell" visual de los `rx.dialog.content` de la
app (admin, sacador inicial, edición de participantes). DESIGN.md manda
`rounded-xl` (1.5rem) para cards y modales; el padding equivale al token
`md` (24px) de la escala de spacing.
"""

from __future__ import annotations

DIALOG_CONTENT_STYLE: dict[str, str] = {
    "min_width": "450px",
    "max_width": "90vw",
    "padding": "24px",
    "background_color": "var(--surface-container-lowest)",
    "border_radius": "1.5rem",  # rounded-xl (DESIGN.md §Shapes)
}
