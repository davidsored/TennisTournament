"""Landing / selector de competición con estilo Advantage."""

from __future__ import annotations

import reflex as rx

from ..components.navbar import navbar


def _card(title: str, desc: str, href: str, badge: str) -> rx.Component:
    return rx.link(
        rx.el.div(
            rx.el.span(
                badge,
                class_name=(
                    "inline-block px-sm py-xs mb-sm rounded-full "
                    "bg-primary-container text-on-primary-container "
                    "text-label-bold uppercase tracking-wider"
                ),
            ),
            rx.el.h3(title, class_name="text-headline-lg text-graphite mb-xs"),
            rx.el.p(desc, class_name="text-body-md text-on-surface-variant"),
            class_name=(
                "p-lg rounded-xl bg-surface-container-lowest border-l-4 border-primary-container "
                "shadow-card hover:shadow-lift transition-shadow min-h-[12rem]"
            ),
        ),
        href=href,
        class_name="block",
    )


def home() -> rx.Component:
    return rx.el.div(
        navbar(),
        rx.el.main(
            rx.el.div(
                rx.el.h1(
                    "Gestión de torneos de tenis",
                    class_name="text-display-lg text-graphite text-center mb-sm",
                ),
                rx.el.p(
                    "Ligas Round Robin y torneos eliminatorios, con marcador en vivo "
                    "y lógica profesional de tie-break.",
                    class_name=(
                        "text-body-lg text-on-surface-variant text-center "
                        "max-w-2xl mx-auto mb-lg"
                    ),
                ),
                class_name="py-lg",
            ),
            rx.el.div(
                _card(
                    "Marcador en vivo",
                    "Arbitra un partido con ventaja de 2 puntos y tie-break a 7.",
                    "/scoreboard",
                    "Live",
                ),
                _card(
                    "Liga Round Robin x2",
                    "Todos contra todos, ida y vuelta, con tabla de posiciones.",
                    "/league",
                    "Liga",
                ),
                _card(
                    "Torneo eliminatorio",
                    "Bracket de una o varias rondas hasta la final.",
                    "/tournament",
                    "Torneo",
                ),
                class_name="grid grid-cols-1 md:grid-cols-3 gap-md max-w-5xl mx-auto",
            ),
            class_name="max-w-6xl mx-auto px-sm pb-xl",
        ),
        class_name="min-h-screen bg-surface font-sans",
    )
