# Al Noir — Design system

> **Update: direction 2, "fine dining".** The first direction (cool "Obsidian & Brass") was replaced after review by a warmer, photography-led one. Tokens keep their names, so everything below still applies; values changed to warm black (`--bg #0a0806`), ivory text (`--text #f1e7d3`) and champagne gold (`--accent #cfa95b`). Public pages are editorial: full-bleed hero photo, arch-framed photography, typographic menu lines with dotted leaders, underline form fields, and a photo + form reservation layout. Signed-in pages keep the app shell, with the same palette and no photography. Photos come from Site Settings (hero image); `static/images/hero-default.jpg` and `dish-default.jpg` are only fallbacks and should be replaced with real photography of the restaurant's dishes.

Source of truth for the interface. All tokens live at the top of `static/css/style.css`; nothing below that block should contain a raw colour, radius or shadow value.

## Audit summary (what the redesign fixes)

| Area | Problem found | Fix |
|---|---|---|
| Staff and client dashboards | Plain pages inside the marketing navbar and footer. No persistent navigation, and no logout control anywhere (`LogoutView` is POST-only in Django 5 and no form existed). | Dedicated app shell: sidebar, topbar, user menu with a POST logout. |
| Staff dashboard | Five equal KPI tiles. Profit, the number that matters, had the same weight as "Tickets". Stock alerts were comma lists and invoices a bullet list. | Hierarchy: profit and revenue first, then composition charts, then alert tables. |
| Reports | `daily_sales` was computed by the view and never rendered. | Daily sales column chart, with a screen-reader table fallback. |
| Visual language | Saturated gold on every label, heading and border. Two display styles, emoji used as icons. | One brass accent used for actions only, an SVG icon set, one type scale. |
| Forms | Three different field markup patterns. The auth form hints were unstyled. | One `partials/field.html` component and one set of control styles. |
| Menu page | Hero was 86vh tall, so no dish was visible without scrolling. Tabs depended on absolute-positioned panels. | Compact header with sticky category tabs. Every category is visible when JS is off. |
| JS | The scroll-reveal ran twice, in `main.js` and again in `scroll-reveal.js`. | One IntersectionObserver implementation that honours `prefers-reduced-motion`. |
| Admin | Themed with hard-coded hex values that duplicated the public CSS. | `admin-theme.css` maps Django's variables to the same tokens. |

## Direction: "Obsidian & Brass"

Keep Al Noir's identity (dark, candlelit, restaurant) but drop the decorative gold. The interface is a neutral near-black with 1px borders doing the work that shadows and glows did before. Brass is reserved for the primary action, the active nav item and data emphasis.

- **Typeface.** Inter for all UI, tables and numbers (tabular figures on every figure). Cormorant Garamond is used only for display headings on public pages, so the restaurant keeps its voice and the dashboards read as software.
- **Density.** Dashboards are compact (14px body, 40px controls). Public pages are airy (16px body, large display type).
- **Motion.** 120–200ms ease-out for state changes, 500ms for the one-time scroll reveal. Everything is disabled under `prefers-reduced-motion`.

## Tokens

### Colour

| Token | Value | Use |
|---|---|---|
| `--bg` | `#0a0a0b` | Page background |
| `--surface-1` | `#111113` | Cards, sidebar |
| `--surface-2` | `#17171a` | Inputs, raised hover |
| `--surface-3` | `#1f1f23` | Table header, chips |
| `--border` / `--border-strong` | `#26262b` / `#36363d` | Hairlines / inputs |
| `--text` / `--text-2` / `--text-3` | `#f4f4f5` / `#a8a8b2` / `#85858f` | Primary / secondary / tertiary (all ≥ 4.5:1 on `--bg`) |
| `--accent` / `--accent-hover` | `#c9a45c` / `#d9b872` | Primary action, focus ring, active nav |
| `--accent-ink` | `#16110a` | Text on the accent (9.5:1) |
| `--success` `--warning` `--danger` `--info` | muted, each with a `-soft` tint | Status only |

### Type scale

`12 / 13 / 14 / 16 / 18 / 22 / 28 / 36 / clamp(40–64)` as `--text-xs … --text-hero`. Line height 1.5 for body, 1.15 for headings. KPI numbers use `font-variant-numeric: tabular-nums`.

### Spacing, radius, elevation

- Spacing: 4px base, `--space-1 … --space-9` = 4, 8, 12, 16, 20, 24, 32, 48, 80.
- Radius: `--radius-sm` 6 (controls), `--radius-md` 10 (cards), `--radius-lg` 16 (panels, hero media), `--radius-pill`.
- Elevation: `--shadow-1` for cards, `--shadow-2` for menus and drawers. Cards otherwise rely on a border.

## Components

Buttons `btn-primary | btn-secondary | btn-ghost | btn-danger`, sizes `btn-sm | btn-lg`, states hover, active, `:focus-visible`, `[disabled]`, `.is-loading`. Fields `field` with label, control, hint and error. Feedback `alert-*`, `badge-*`, `empty-state`, `skeleton`, `spinner`. Data `card`, `kpi`, `bar-list`, `stack-bar`, `column-chart`, `data-table` (collapses to stacked rows under 720px), `progress`. Navigation `navbar` (public), `sidebar` + `topbar` (app).

## Layout

- **Public shell** (`base.html`): navbar, content, footer.
- **App shell** (`app_base.html`, extends `base.html`): sidebar and topbar, no marketing footer. Used by client dashboard, staff dashboard, reports and schedule.
- Sidebar is fixed at 248px from 1024px up. Below that it becomes an off-canvas drawer with a scrim, focus handling and `Esc` to close.

## Why the new template layer was necessary

The dashboards were rendered inside the public marketing chrome. A persistent sidebar cannot be added to that without either hiding the navbar with CSS or duplicating `base.html`. `base.html` now exposes `{% block chrome %}` and `app_base.html` overrides it. The public pages are untouched structurally. No views, URLs, models or forms were replaced.

## Out of scope on purpose

No profile or settings pages exist in the backend (no views, no forms), and the brief forbids inventing functionality, so none were added. The user chip in the sidebar shows the existing account name and email read-only. Adding editable profile and settings pages would be a separate backend task.
