"""Helper para iconos Material Symbols Outlined.

Reflex no expone Material Symbols en `rx.icon` (que usa Lucide), así que
renderizamos un `<span>` con la clase `material-symbols-outlined` y el nombre
del símbolo como contenido. La fuente se carga globalmente desde la App.
"""

from __future__ import annotations

import reflex as rx


def material_icon(
    name: str,
    *,
    fill: bool = False,
    class_name: str = "",
    style: dict | None = None,
) -> rx.Component:
    """Renderiza un Material Symbols Outlined.

    Args:
        name: nombre del símbolo (p.ej. "settings", "sports_tennis").
        fill: si True, usa la variante rellena (FILL = 1).
        class_name: utilidades Tailwind extra (color, tamaño, etc.).
        style: estilos CSS adicionales (se mezclan con font-variation-settings).
    """
    fvs = "'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24" if fill else "'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24"
    css = {"fontVariationSettings": fvs}
    if style:
        css.update(style)
    return rx.el.span(
        name,
        class_name=f"material-symbols-outlined {class_name}".strip(),
        style=css,
    )
