---
name: Advantage
colors:
  surface: '#f8f9fa'
  surface-dim: '#d9dadb'
  surface-bright: '#f8f9fa'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f3f4f5'
  surface-container: '#edeeef'
  surface-container-high: '#e7e8e9'
  surface-container-highest: '#e1e3e4'
  on-surface: '#191c1d'
  on-surface-variant: '#444933'
  inverse-surface: '#2e3132'
  inverse-on-surface: '#f0f1f2'
  outline: '#747a60'
  outline-variant: '#c4c9ac'
  surface-tint: '#506600'
  primary: '#506600'
  on-primary: '#ffffff'
  primary-container: '#ccff00'
  on-primary-container: '#5b7300'
  inverse-primary: '#abd600'
  secondary: '#555f6f'
  on-secondary: '#ffffff'
  secondary-container: '#d6e0f3'
  on-secondary-container: '#596373'
  tertiary: '#006c49'
  on-tertiary: '#ffffff'
  tertiary-container: '#a7ffd2'
  on-tertiary-container: '#007a53'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#c3f400'
  primary-fixed-dim: '#abd600'
  on-primary-fixed: '#161e00'
  on-primary-fixed-variant: '#3c4d00'
  secondary-fixed: '#d9e3f6'
  secondary-fixed-dim: '#bdc7d9'
  on-secondary-fixed: '#121c2a'
  on-secondary-fixed-variant: '#3d4756'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#f8f9fa'
  on-background: '#191c1d'
  surface-variant: '#e1e3e4'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '800'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-xl:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: '1.3'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  label-bold:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: '1.2'
  score-display:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '800'
    lineHeight: '1'
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 0.5rem
  sm: 1rem
  md: 1.5rem
  lg: 2.5rem
  xl: 4rem
  container-padding: 1rem
  gutter: 1rem
---

## Brand & Style

This design system is engineered for high-performance tennis management, blending the technical precision of professional sports with the clarity of a modern SaaS interface. The brand personality is authoritative yet energetic, designed to instill confidence in club managers while providing athletes with a fast, frictionless experience.

The design style follows a **Modern Minimalist** approach. It utilizes expansive whitespace and a restrained color palette to ensure the vibrant "Tennis Green" remains the focal point for all critical actions. The interface avoids unnecessary decoration, relying instead on structural integrity, large tap targets for mobile-first utility, and high-contrast information displays that mimic professional scoreboard aesthetics.

## Colors

The palette is anchored by a high-visibility **Tennis Green (#CCFF00)**, reserved exclusively for primary calls to action, active states, and success indicators. This color provides maximum "pop" against the **Graphite (#1F2937)** text, ensuring the interface remains legible under stadium lights or bright outdoor sun.

- **Backgrounds:** The primary surface is #F9FAFB (Off-white), with pure white (#FFFFFF) reserved for elevated card elements.
- **Typography:** #1F2937 is used for all primary body and headline text to maintain a professional, grounded feel.
- **Accents:** A deep emerald green (#10B981) is utilized for secondary positive metrics to differentiate from the neon-lime primary action color.

## Typography

This design system utilizes **Inter** for its systematic, utilitarian nature. The hierarchy is optimized for quick scanning of data-heavy tables and player statistics.

- **Headlines:** Use tighter letter-spacing and heavier weights (700-800) to create a sense of strength.
- **Data Display:** Scoring elements use the `score-display` token, featuring heavy weights and increased letter spacing to replicate the look of digital scoreboards.
- **Labels:** Small caps or bold uppercase labels are used sparingly for metadata to distinguish between content and descriptive headers.

## Layout & Spacing

The layout philosophy follows a **Fluid Grid** model with a mobile-first priority. On handheld devices, the system uses a single-column layout with a 16px (1rem) margin. For desktop views, it expands to a 12-column grid.

- **Rhythm:** A 4px base unit ensures mathematical consistency across all margins and padding.
- **Touch Targets:** Minimum height for interactive elements is 48px to accommodate on-court usage where users may have sweaty hands or be in motion.
- **Whitespace:** Generous padding (md and lg) is used between content sections to prevent information fatigue in complex management dashboards.

## Elevation & Depth

This design system uses **Tonal Layers** combined with **Ambient Shadows** to create a focused, professional depth.

- **Surfaces:** The background is the lowest tier (#F9FAFB). Content resides on white (#FFFFFF) cards.
- **Shadows:** Shadows are highly diffused and low-opacity (4% to 8% alpha) using a Graphite tint (#1F2937) rather than pure black. This creates a "soft lift" rather than a harsh drop shadow.
- **Interactive Depth:** Buttons use a subtle inner-glow on hover rather than an increased shadow to maintain a clean, flat aesthetic while providing tactile feedback.

## Shapes

The shape language is defined by **XL rounded corners**, providing a modern, approachable feel that balances the "hard" nature of the high-contrast typography.

- **Cards & Modals:** Use the `rounded-xl` token (1.5rem) to create distinct containers.
- **Buttons & Inputs:** Use the `rounded-lg` token (1rem) to maintain a cohesive look with the larger containers.
- **Avatars:** Strictly circular to differentiate between people and UI containers.

## Components

- **Buttons:** Primary buttons use the Tennis Green background with Graphite text for maximum visibility. Secondary buttons use a Graphite outline. All buttons feature a 1rem corner radius.
- **Cards:** White background with a `rounded-xl` border radius and a soft ambient shadow. Cards for "Live Matches" should feature a 4px Tennis Green left-border accent.
- **Scoreboard Chips:** High-contrast Graphite blocks with white or Tennis Green text. These should have a slight inner-shadow to appear inset.
- **Inputs:** Soft gray borders (#E5E7EB) that transition to a 2px Tennis Green border on focus. Labels are always positioned above the field for mobile clarity.
- **Progress Bars:** Use a thick 8px track for athlete performance metrics, utilizing the Tennis Green for the filled state and a light gray for the unfilled track.
- **Match Status Labels:** Small, pill-shaped badges (rounded-full) using subtle background tints of Green (Active), Red (Cancelled), or Gray (Scheduled).
