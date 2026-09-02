# UI/UX Design System Specification (2026 Edition)
## ROOMMET — Multi-Tenant Hostel SaaS Platform

---

## 1. Design Philosophy & Aesthetic Pillars

The ROOMMET design system is built specifically around **Enterprise Usability, 2026 Dark Glassmorphism, Tactile Claymorphism, and Fluid Bento Layouts**:
1. **Depth & Translucency:** Semi-transparent frosted glass layers (`backdrop-filter: blur(12px)`) with subtle multi-layered borders.
2. **Curated Color Harmonies:** Slate backgrounds paired with vibrant Sky Blue (`#38bdf8`) and Neon Violet (`#a855f7`) gradients.
3. **Tactile Micro-Interactions:** Subtle scale-downs on active clicks (`transform: scale(0.98)`), gentle elevation on hover, and smooth tab transitions.
4. **Adaptive Accessibility:** First-class dark and light themes, high contrast text tokens, and visible focus rings.
5. **Production-Grade UI Structure:** Replacing generic AI artifacts (such as blurry text, floating unanchored buttons, or inconsistent lighting) with clean, deliberate spatial hierarchy.

---

## 2. Color Palette & Token System

### 2.1. Dark Mode (Default)

| Token Name | Hex / CSS Value | Semantic Role |
|------------|-----------------|---------------|
| `--bg-root` | `#070a13` | Deep root canvas background with ambient radial glow |
| `--bg-main` | `#090d16` | Main canvas background |
| `--bg-secondary` | `#0f172a` | App shell and surface background for modals/sidebars |
| `--card-surface` | `#1e293b` | Bento cards and panel surfaces |
| `--popover-surface` | `#334155` | Inspection popovers and contextual flyouts |
| `--glass-bg` | `rgba(30, 41, 59, 0.45)` | Translucent card and surface layer |
| `--glass-border` | `rgba(255, 255, 255, 0.06)` | Hairline 1px glass border highlights |
| `--primary` | `#38bdf8` (Sky Blue) | Primary action items, active links, brand accents |
| `--primary-glow` | `rgba(56, 189, 248, 0.25)` | Glowing shadows on primary buttons and badges |
| `--accent` | `#a855f7` (Vibrant Purple) | Secondary accents, hero highlights, gradient transitions |
| `--accent-glow` | `rgba(168, 85, 247, 0.25)` | Ambient glow for secondary interactive widgets |
| `--success` | `#10b981` (Emerald) | Verified status badges, success toasts, 92%+ collection |
| `--warning` | `#f59e0b` (Amber) | Pending requests, maintenance state, cautionary alerts |
| `--danger` | `#ef4444` / `#f43f5e` (Rose/Red) | Outstanding rent, deletion triggers, rejected receipts |
| `--text-primary` | `#f8fafc` | High-contrast headers and primary body typography |
| `--text-secondary` | `#94a3b8` | Subtext, labels, and secondary metadata |
| `--text-muted` | `#64748b` | Timestamps, placeholders, and inactive elements |

### 2.2. Light Mode (`:root.light-theme`)

| Token Name | Hex / CSS Value | Semantic Role |
|------------|-----------------|---------------|
| `--bg-main` | `#f1f5f9` | Light slate canvas background |
| `--bg-secondary` | `#ffffff` | Clean white card and modal surface |
| `--glass-bg` | `rgba(241, 245, 249, 0.5)` | Frosted light panel surface |
| `--glass-border` | `rgba(15, 23, 42, 0.08)` | Crisp boundary border |
| `--primary` | `#0284c7` (Sky 700) | High-contrast primary action color |
| `--accent` | `#7e22ce` (Purple 700) | High-contrast secondary accent color |
| `--text-primary` | `#0f172a` (Slate 900) | Deep readable text |
| `--text-secondary` | `#475569` (Slate 600) | Secondary body copy |

---

## 3. Typography System

- **Headings & Brand Title:** `Outfit`, sans-serif (Weights: 600, 700, 800) with `-0.02em` letter-spacing.
- **Body & Controls:** `Inter`, sans-serif (Weights: 400, 500, 600, 700) with `1.6` line-height.
- **Monospace Financial Ledger:** `JetBrains Mono` / `Courier New`, monospace for currency values, structured invoice IDs (`RM-2026-11-01`), and `<kbd>` tags.

---

## 4. Detailed Design Breakdown & Architecture

### 4.1. Real-World Architectural Layout (Bento Grid)
- **Property Switcher & Hierarchy:** Multi-tenant architecture allowing managers to quickly toggle between hostel branches (*Branch Office A*, *Downtown Executive Wing*, *Westside Lofts*) without page reloads.
- **Interactive Floorplan Grid:** Room nodes organized into structural wings. Each node displays room identifiers (`301`, `302`, `306`) along with status indicators:
  - 🟢 **Emerald (`#10b981`):** Occupied / Good standing
  - 🟡 **Amber (`#f59e0b`):** Maintenance / Pending check-in
  - 🔵 **Cyan Highlight (`#38bdf8`):** Selected / Active focus
- **Hover Inspection Flyout:** Selecting or hovering over a room displays tenant metadata (*Tenant: Sarah J. Parker, Status: Student, Rent: Up-to-date*) directly on top of the layout without obscuring neighboring rooms.

### 4.2. Realistic Financial & Operational Data
- **Rent Collection Doughnut:** A functional collection ring displaying accurate proportion metrics (e.g., **92% Collected** in Emerald `#10b981` vs. **Outstanding** in Rose `#ef4444`).
- **Monospaced Ledger:** Financial entries use monospaced numbers for currency figures and structured invoice IDs (`RM-2026-11-01`), aligning numbers cleanly for optimal accounting readability.

### 4.3. Spatial Surface & Lighting Hierarchy
- **Surface Stacking:** 
  $$\text{Root Canvas (\#070a13)} \longrightarrow \text{App Shell (\#0f172a)} \longrightarrow \text{Bento Cards (\#1e293b)} \longrightarrow \text{Inspection Popovers (\#334155)}$$
- **Micro-Borders:** Hairline 1px borders with `rgba(255, 255, 255, 0.06)` give crisp boundary definition across high-DPI displays without GPU-intensive blur lag.
- **Cyan-to-Cobalt Flow:** Vibrant gradients are reserved strictly for high-priority user actions (*Add New Tenant*, *Reconcile Payments*, and active selection rings) to maintain optical focus.

---

## 5. Component Library Architecture

### 5.1. Sticky Glass Navbar
- **Height:** 70px (`--navbar-height`).
- **Scroll Behavior:** Automatic shrink to `0.65rem` padding on scroll >40px (`.scrolled` class) with a deeper shadow.
- **Controls:** Brand logo, contextual navigation links with gradient underline animation, theme toggle (`☀️ / 🌙`), shortcuts button (`?`), and mobile hamburger toggle.

### 5.2. Bento Grid System
- **Desktop (≥1024px):** 12-column grid system with 1.5rem gap (`col-12`, `col-8`, `col-6`, `col-4`, `col-3`).
- **Tablet (768px–1023px):** Reflows 3 and 4-column cards into 6-column half-width spans.
- **Mobile (<768px):** Reflows all grid items to single-column full-width cards.

### 5.3. Interactive Glass Cards
- `.glass-minimal`: Translucent card with 12px blur and subtle white edge highlights.
- `.glass-liquid`: Inset glass lighting effect for featured promotional banners.
- `.tactile-outset` / `.tactile-inset`: 3D Neumorphic-lite button styling with tactile press depths.
- `.clay-btn`: Gradient-filled pill button with soft clay depth and hover lift.

### 5.4. Toast Notification Engine
- Positioned in bottom-right corner (`#toast-container`).
- Supports `success`, `danger`, `warning`, `info` types with animated progress bars and auto-dismiss timers.
- API: `showToast(title, message, type, duration)`.

### 5.5. Skeleton Loading System
- CSS shimmer animation (`@keyframes shimmer`) simulating content placeholders.
- API: `showSkeleton(container, 'card'|'list'|'profile', count)` and `hideSkeleton(container)`.

### 5.6. Expandable FAQ Accordion
- Accessible buttons with auto-rotating chevron indicators (`transform: rotate(180deg)`).
- Single-open accordion mechanism with smooth CSS `max-height` transitions.

### 5.7. Floating Back-to-Top Button
- Appears smoothly after 300px vertical scroll.
- Clicking initiates smooth scroll to page origin (`window.scrollTo({ top: 0, behavior: 'smooth' })`).

---

## 6. Keyboard Navigation & Shortcuts Guide

| Key Combination | Action |
|-----------------|--------|
| `?` | Open / Close Keyboard Shortcuts Modal |
| `Esc` | Close Shortcuts Modal or Mobile Drawer |
| `Ctrl + K` / `Cmd + K` | Focus Search Input |
| `Alt + T` | Toggle Dark / Light Theme |
| `Home` | Smooth scroll to top of page |
| `Tab` (at page top) | Reveal and focus "Skip to content" accessibility link |
