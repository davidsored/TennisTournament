"""Configuración de Reflex + Tailwind v4 alineada con DESIGN.md (Advantage).

Los tokens aquí definidos son la ÚNICA fuente de verdad para la UI y se consumen
desde los componentes mediante utilidades Tailwind (`class_name="bg-primary ..."`).
"""

import reflex as rx


TAILWIND_CONFIG = {
    "theme": {
        "extend": {
            "fontFamily": {
                "sans": ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
                "inter": ["Inter", "sans-serif"],
            },
            "colors": {
                # Superficies
                "surface": "#f8f9fa",
                "surface-dim": "#d9dadb",
                "surface-bright": "#f8f9fa",
                "surface-container-lowest": "#ffffff",
                "surface-container-low": "#f3f4f5",
                "surface-container": "#edeeef",
                "surface-container-high": "#e7e8e9",
                "surface-container-highest": "#e1e3e4",
                "surface-variant": "#e1e3e4",
                "background": "#f8f9fa",
                # Texto sobre superficies
                "on-surface": "#191c1d",
                "on-surface-variant": "#444933",
                "on-background": "#191c1d",
                "inverse-surface": "#2e3132",
                "inverse-on-surface": "#f0f1f2",
                # Contornos
                "outline": "#747a60",
                "outline-variant": "#c4c9ac",
                # Primario (Tennis Green)
                "primary": "#506600",
                "on-primary": "#ffffff",
                "primary-container": "#ccff00",
                "on-primary-container": "#5b7300",
                "inverse-primary": "#abd600",
                "surface-tint": "#506600",
                "primary-fixed": "#c3f400",
                "primary-fixed-dim": "#abd600",
                "on-primary-fixed": "#161e00",
                "on-primary-fixed-variant": "#3c4d00",
                # Secundario
                "secondary": "#555f6f",
                "on-secondary": "#ffffff",
                "secondary-container": "#d6e0f3",
                "on-secondary-container": "#596373",
                "secondary-fixed": "#d9e3f6",
                "secondary-fixed-dim": "#bdc7d9",
                "on-secondary-fixed": "#121c2a",
                "on-secondary-fixed-variant": "#3d4756",
                # Terciario (emerald accent)
                "tertiary": "#006c49",
                "on-tertiary": "#ffffff",
                "tertiary-container": "#a7ffd2",
                "on-tertiary-container": "#007a53",
                "tertiary-fixed": "#6ffbbe",
                "tertiary-fixed-dim": "#4edea3",
                "on-tertiary-fixed": "#002113",
                "on-tertiary-fixed-variant": "#005236",
                # Error
                "error": "#ba1a1a",
                "on-error": "#ffffff",
                "error-container": "#ffdad6",
                "on-error-container": "#93000a",
                # Graphite para tipografía principal (ver DESIGN.md)
                "graphite": "#1f2937",
            },
            "fontSize": {
                "display-lg": [
                    "48px",
                    {"lineHeight": "1.1", "letterSpacing": "-0.02em", "fontWeight": "800"},
                ],
                "headline-xl": [
                    "32px",
                    {"lineHeight": "1.2", "letterSpacing": "-0.01em", "fontWeight": "700"},
                ],
                "headline-lg": [
                    "24px",
                    {"lineHeight": "1.3", "fontWeight": "700"},
                ],
                "body-lg": ["18px", {"lineHeight": "1.6", "fontWeight": "400"}],
                "body-md": ["16px", {"lineHeight": "1.5", "fontWeight": "400"}],
                "label-bold": ["14px", {"lineHeight": "1.2", "fontWeight": "600"}],
                "score-display": [
                    "20px",
                    {"lineHeight": "1", "letterSpacing": "0.05em", "fontWeight": "800"},
                ],
            },
            "borderRadius": {
                "sm": "0.25rem",
                "DEFAULT": "0.5rem",
                "md": "0.75rem",
                "lg": "1rem",
                "xl": "1.5rem",
                "full": "9999px",
            },
            "spacing": {
                "xs": "0.5rem",
                "sm": "1rem",
                "md": "1.5rem",
                "lg": "2.5rem",
                "xl": "4rem",
            },
            "boxShadow": {
                # Sombras ambient difusas con tinte graphite (DESIGN.md → Elevation)
                "soft": "0 4px 24px 0 rgba(31, 41, 55, 0.06)",
                "card": "0 2px 12px 0 rgba(31, 41, 55, 0.04)",
                "lift": "0 8px 32px 0 rgba(31, 41, 55, 0.08)",
            },
        }
    },
}


config = rx.Config(
    app_name="TennisTournament",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(config=TAILWIND_CONFIG),
    ],
)
