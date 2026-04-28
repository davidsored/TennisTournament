"""Bento card (acción primaria) con icono Material y degradado de fondo."""

from __future__ import annotations

import reflex as rx

from .material_icon import material_icon


def bento_card(
    title: str,
    subtitle: str,
    icon: str,
    href: str,
) -> rx.Component:
    """Tarjeta grande tipo "Bento" para crear competiciones."""
    return rx.link(
        rx.el.button(
            # Capa de degradado al fondo
            rx.box(
                class_name=(
                    "absolute inset-0 bg-gradient-to-br from-surface-container-lowest "
                    "to-surface-container opacity-50 z-0"
                ),
            ),
            # Contenido por encima del degradado
            rx.box(
                rx.box(
                    material_icon(
                        icon,
                        class_name="text-on-primary-container text-[40px]",
                    ),
                    class_name=(
                        "bg-primary-container p-sm rounded-full text-on-primary-container "
                        "group-hover:scale-110 transition-transform duration-300 shadow-sm"
                    ),
                ),
                rx.el.h2(
                    title,
                    class_name=(
                        "text-headline-lg text-on-surface text-center mt-xs"
                    ),
                ),
                rx.el.p(
                    subtitle,
                    class_name="text-body-md text-on-surface-variant text-center",
                ),
                class_name="z-10 flex flex-col items-center gap-sm",
            ),
            class_name=(
                "bg-surface-container-lowest rounded-md p-md "
                "border border-surface-container-highest "
                "shadow-[0_4px_20px_-4px_rgba(31,41,55,0.04)] "
                "flex flex-col items-center justify-center gap-sm "
                "aspect-square md:aspect-auto md:h-64 "
                "hover:border-primary-container transition-colors group cursor-pointer "
                "text-left w-full relative overflow-hidden"
            ),
        ),
        href=href,
        class_name="block w-full",
    )
