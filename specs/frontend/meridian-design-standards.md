# Meridian Frontend Design Standards

> This document is the SINGLE SOURCE OF TRUTH for all Meridian frontend development.
> Every Dev task touching frontend MUST reference this spec.

## Product Identity

**Meridian** is a professional smart money signal platform for serious investors. The design communicates:
- **Authority**: We process real institutional data — design must feel credible and precise
- **Clarity**: Financial data must be instantly readable — no decoration, no clutter
- **Density**: Power users want information density — show more, waste less space
- **Restraint**: No glow, no gradients, no animations (except functional ones), no emoji in UI

### Design Philosophy
```
Bloomberg Terminal meets modern dark UI.
Every pixel either communicates data or provides breathing room.
Nothing decorative. Nothing cute. Nothing "AI-looking".
```

## Visual Language

### Color System (from app.css — NEVER deviate)

**Backgrounds** — 3 elevation levels ONLY:
```css
--bg-base:       #09090b;    /* Page background (zinc-950) */
--bg-surface:    #18181b;    /* Cards, panels (zinc-900) */
--bg-elevated:   #27272a;    /* Modals, dropdowns, hover (zinc-800) */
```

**Borders** — subtle, functional:
```css
--border-default: #27272a;
--border-hover:   #3f3f46;
--border-focus:   #52525b;
```

**Text** — 4 levels, use deliberately:
```css
--text-primary:   #fafafa;   /* Headlines, tickers, key numbers */
--text-secondary: #a1a1aa;   /* Body text, table cells */
--text-muted:     #71717a;   /* Labels, captions, secondary info */
--text-dimmed:    #52525b;   /* Table headers, timestamps, hints */
```

**Semantic** — data coloring ONLY:
```css
--green:  #22c55e;   /* Positive values, bullish, inflows */
--red:    #f87171;   /* Negative values, bearish, outflows */
--amber:  #f59e0b;   /* Warnings, mixed signals, neutral-active */
--blue:   #60a5fa;   /* Links, informational (rare) */
```

### Typography

**Body text**: Inter, -apple-system, system-ui, sans-serif
**Financial data & labels**: JetBrains Mono, SF Mono, Cascadia Code, monospace

| Element | Font | Size | Weight | Color |
|---------|------|------|--------|-------|
| Page title | Inter | 18px | 600 | --text-primary |
| Page subtitle | Inter | 12px | 400 | --text-muted |
| Section label | Mono | 11px UPPERCASE | 500 | --text-muted |
| Table header | Mono | 10-11px UPPERCASE | 500 | --text-dimmed |
| Table cell | Mono/Inter | 12-13px | 400-500 | --text-secondary |
| Ticker symbol | Mono | 13px | 600 | --text-primary |
| Big number | Mono | 24-28px | 700 | --text-primary |
| Score/value | Mono | 13px | 700 | contextual color |

### Numbers
- ALL financial numbers use monospace font with `font-variant-numeric: tabular-nums`
- Positive values: `var(--green)` with `+` prefix
- Negative values: `var(--red)` (minus is inherent)
- Zero/null: `var(--text-muted)` showing `—` (em-dash, NOT "0" or "$0")
- Large numbers: abbreviate with suffix — $1.2B, $345M, 12.5K
- Percentages: one decimal place — `+12.3%`, `-4.5%`
- Scores: one decimal place — `71.5`

## Component Patterns

### Card (`.card-base`)
```css
.card-base {
    background: var(--bg-surface);
    border: 1px solid var(--border-default);
    border-radius: 12px;
    padding: 20px;
}
```

### Section Label (`.section-label`)
```css
.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 12px;
}
```

### Data Table (`.data-table`)
- Full width, collapsed borders
- Header: mono 10-11px, uppercase, dimmed
- Cells: 12-13px, --text-secondary
- Row dividers: 1px solid var(--border-subtle) or rgba(255,255,255,0.04)
- Last row: no bottom border
- Right-align numeric columns

### Ticker Link (`.ticker-link`)
```css
.ticker-link {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    color: var(--text-primary);
    text-decoration: none;
    letter-spacing: 0.02em;
}
.ticker-link:hover {
    color: var(--accent, #818cf8);
}
```
**RULE**: Every ticker symbol MUST be a clickable link to `/ticker/{symbol}`.

### Direction Badge
```css
.direction-badge.bullish { color: var(--green); }
.direction-badge.bearish { color: var(--red); }
/* Mono, 11px, 600 weight, uppercase */
```

### Trade Type
```css
.trade-type.buy  { color: var(--green); }
.trade-type.sell { color: var(--red); }
```

### Two-Column Layout
```css
.two-col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
}
@media (max-width: 768px) {
    .two-col { grid-template-columns: 1fr; }
}
```

## Page Structure

Every page follows this skeleton:
```svelte
<div class="space-y-6">
    <!-- Header -->
    <div class="page-header">
        <div>
            <h1 class="page-title">{title}</h1>
            <p class="page-subtitle">{description}</p>
        </div>
        {#if cached_at}
            <span class="cache-label">Updated {time}</span>
        {/if}
    </div>

    <!-- Content cards -->
    <div class="card-base">
        <div class="section-label">SECTION NAME</div>
        <!-- content -->
    </div>
</div>
```

## Svelte 5 Conventions

- Props: `let { data }: { data: PageData } = $props();`
- Derived: `const d = $derived(data.data);`
- Snippets: Use `{#snippet children()}` pattern for Card components
- NO `$:` reactive statements (Svelte 4 syntax)
- NO `export let` (Svelte 4 syntax)

## Anti-Patterns (NEVER DO)

❌ Emoji in page titles, section labels, or data cells
❌ Gradient backgrounds or glowing effects
❌ Rounded pill badges with bright backgrounds
❌ Animated loading spinners (use simple text: "Loading...")
❌ Placeholder images or illustrations
❌ "AI-generated" aesthetic (purple gradients, sparkle effects)
❌ Showing `0` or `$0` for missing data — use `—`
❌ Ticker symbols as plain text (always link to `/ticker/{symbol}`)
❌ Sans-serif font for financial numbers
❌ Color for decoration (only for semantic meaning: up/down/warning)
❌ More than 3 elevation levels
❌ Custom colors outside the design token system

## Mobile Responsiveness

- Two-column grids collapse to single column at 768px
- Tables get horizontal scroll wrapper (`.table-wrap { overflow-x: auto; }`)
- Font sizes stay the same (don't shrink below 11px)
- Cards maintain 16-20px padding
- Page title stays at 18px

## Data Handling

- Always handle null/undefined gracefully
- Format functions at top of `<script>`: `fmtVol()`, `fmtPct()`, `fmtPrice()`, etc.
- Cache timestamps: show time only, not full datetime
- Empty states: centered text in --text-dimmed, descriptive message
- Error states: red text in card with error message

## Reference Pages

When building new pages, study these existing ones for patterns:
- `/crypto-signals/+page.svelte` — Full-featured data page
- `/smart-money/+page.svelte` — Signal ranking table
- `/dashboard/+page.svelte` — Multi-card overview
- `/ticker/[symbol]/+page.svelte` — Detail page
