---
name: ui-review
description: "UI Quality Review (design system, states, responsive, dark mode, accessibility)."
---

# /ui-review — UI Quality Review

I am not lazy. I am not in a rush. I do not take shortcuts. My job is to deliver a great output that works first time.

Trigger: User invokes `/ui-review`, or automatically as part of `/review` and `/implement` for any user-facing changes.

## Purpose

Verify that UI code follows the project's design system, is consistent with existing pages, handles all visual states, and matches the reference implementation's look and behaviour (if one exists).

## Prerequisites

Before reviewing, read the project's CLAUDE.md to understand:
- The CSS/styling framework used (e.g. Tailwind, UnoCSS, CSS modules, styled-components)
- The design system: shortcuts, tokens, component library
- The reference implementation path (if any)
- Frontend directory structure

Then read the project's actual design system config and global styles to understand available shortcuts, tokens, and components.

## Instructions

### Step 1: Identify Scope

- If a file/path is specified, review that
- If no path, review all uncommitted changes that touch frontend code
- Skip files with no UI impact (pure logic, types, backend)

### Step 2: Spawn UI Review Agent

Launch an Agent that checks the following categories:

## Human Visibility Standard (BLOCKING)

This is the most important check. **Every interactive element must be visible to a human user without any interaction.**

A UI that looks clean but hides its controls is worse than an ugly UI where everything is obvious. Users cannot click what they cannot see.

### Rules

- **Buttons must not rely on hover states to become visible** — they must be clearly visible at rest
- **Navigation links must be visually distinct from plain text** — use color, weight, underline, or background to differentiate
- **Text contrast minimums**: 4.5:1 for normal text, 3:1 for large text (18px+) and UI components/graphical objects

### Specific CSS Class Anti-Patterns to Flag as BLOCKING

- `text-gray-400` or `text-gray-500` on `bg-white` or `bg-gray-50` backgrounds for interactive elements
- `text-gray-500` for buttons without a background color
- Any button or link that has no `bg-*`, `border-*`, or distinguishing visual treatment
- Navigation items that are identical in appearance to body text

### Required Visual Treatments for Interactive Elements

- **Primary actions**: visible background color (e.g., `bg-blue-600 text-white`)
- **Secondary actions**: visible border or background tint (e.g., `border border-gray-300` or `bg-gray-100`)
- **Navigation links**: distinct color from body text, or underline, or font-weight difference
- **Destructive actions**: red-tinted styling (`text-red-600` or `bg-red-*`)

### The Squint Test

If you squint and cannot tell which elements are clickable, the UI fails this check. This is a **BLOCKING** failure.

---

#### A. Design System Compliance

Check that the code uses the project's established design system shortcuts, components, and tokens — not raw/inline equivalents:

- **Buttons** — uses the project's button classes/components, not raw styling
- **Inputs** — uses the project's input classes/components, not raw styling
- **Cards/containers** — uses the project's card/container classes, not raw styling
- **Typography** — uses the project's heading/text classes, not raw font sizes
- **Badges/pills** — uses the project's badge classes, not raw styling
- **Layout containers** — uses the project's container width classes, not raw max-widths
- **Colors** — uses design token names, not hardcoded hex/rgb values

Flag any raw utility strings that duplicate an existing shortcut as **SHOULD FIX**.

To identify what shortcuts exist, read the project's CSS config file and global styles.

#### B. Visual States

Every data-fetching component must handle all states. This is not optional polish — it is core functionality. A page that shows blank space while loading, or nothing when there is no data, is broken — not "could be improved."

Every data-fetching view **MUST** have:

1. **Loading** — shows a loading indicator (skeleton preferred, spinner is the minimum), not blank space
2. **Empty** — shows a helpful empty state with message and CTA, not just nothing
3. **Error** — shows error message with retry action or navigation path
4. **Success** — renders data correctly

Missing states = **BLOCKING**. A page that shows nothing while loading or when empty is a broken experience that ships confusion to users.

#### C. Responsive Behaviour

Check that components work across breakpoints:

1. **Mobile layout** — no horizontal overflow, readable text, tappable targets (min 44px)
2. **Breakpoint usage** — follows the project's responsive pattern (mobile-first or otherwise)
3. **Container width** — page uses appropriate container width for its content type
4. **Hidden/shown elements** — navigation items properly toggle between mobile and desktop
5. **Grid layouts** — responsive column counts adjust for smaller screens

Overflow or broken layout on mobile = **BLOCKING**.

#### D. Dark Mode (if the project supports it)

Check that the component works in dark mode:

1. **Background colours** — has dark mode variants where needed
2. **Text colours** — has dark mode variants
3. **Borders** — has dark mode variants
4. **No hardcoded colours** — light-only colours without dark mode equivalents

Missing dark mode on a visible element = **SHOULD FIX**.

#### E. Consistency with Existing Pages

Compare the new/changed UI against adjacent pages in the app:

1. **Page structure** — does it follow the same layout pattern? (heading → description → content)
2. **Spacing** — matches the vertical rhythm of similar pages
3. **Typography** — headings use the same classes as equivalent headings elsewhere
4. **Actions** — buttons/links use the same patterns (primary for main CTA, secondary/ghost for others)
5. **Tables** — if rendering tabular data, matches the table styling from other list pages

Inconsistency with existing pages = **CONSIDER** (unless egregious, then **SHOULD FIX**).

#### F. Reference Implementation Comparison (if a reference exists)

If CLAUDE.md defines a reference implementation:

1. Read the reference component (READ-ONLY)
2. Compare layout structure, spacing, visual hierarchy
3. Check that key UI elements are present (icons, badges, metadata, action buttons)
4. Verify interaction patterns match (hover states, click targets, transitions)

Major visual divergence from reference = **SHOULD FIX** with specific details of what differs.

#### G. Accessibility Basics

1. **Form labels** — every input has a `<label>` with matching `for`/`id`
2. **Alt text** — images have `alt` attributes
3. **Focus indicators** — keyboard users must be able to see which element is focused; interactive elements must have visible focus styles (e.g., `focus:ring-2` or equivalent)
4. **Semantic HTML** — uses `<button>` for actions (not `<div onClick>`), `<a>` for navigation
5. **Colour contrast** — text on coloured backgrounds meets minimum contrast ratios (4.5:1 normal text, 3:1 large text)
6. **Clickable area size** — interactive elements must be at least 44x44px (mobile tap target minimum per WCAG)
7. **Semantic color usage** — do not rely on color alone to convey meaning; use icons, text, or patterns alongside color
8. **Missing labels** — form inputs without labels or `aria-label` attributes

Contrast violations = **BLOCKING**.
Missing form labels = **BLOCKING**.
Other accessibility violations = **SHOULD FIX**.

#### H. Icons & Visual Polish

1. **Icon usage** — uses the project's icon system consistently, correct sizing
2. **Icon alignment** — icons in buttons/links vertically centered with text
3. **Transitions** — interactive elements have smooth state change transitions
4. **Loading indicators** — async actions show a spinner or disabled state while pending

#### I. Navigation Completeness

Every feature and page must be reachable through the UI navigation. Features that can only be reached by typing a URL directly are broken.

1. **Main navigation** — check that the main nav, sidebar, or dashboard has links to all major sections of the app
2. **Sub-navigation** — pages with child routes must have tabs, breadcrumbs, or equivalent sub-nav
3. **Route coverage** — cross-reference defined routes against navigation links; every route should be reachable from at least one nav element
4. **Link visibility** — every nav link must be clearly visible and distinguishable (see Human Visibility Standard above)
5. **Orphan pages** — pages with no inbound navigation link are **BLOCKING** failures

Features that can only be reached by typing a URL = **BLOCKING**.
Missing sub-navigation on pages with child routes = **SHOULD FIX**.

### Step 3: Report

Present findings grouped by severity:

- **BLOCKING** — broken layout, overflow, unusable on mobile, invisible interactive elements, missing visual states (loading/empty/error), unreachable pages or features, contrast violations, missing form labels. **If a real user would struggle to find or use a feature, it is BLOCKING — not a suggestion.**
- **SHOULD FIX** — inconsistent design tokens, missing dark mode, accessibility gaps beyond contrast/labels, reference divergence, missing sub-navigation
- **CONSIDER** — minor spacing differences, polish opportunities, animation suggestions

Each finding must cite the specific file, line, the issue, and what the fix should be.

## Integration

This skill is invoked:
1. **Standalone** via `/ui-review` for targeted UI reviews
2. **As part of `/review`** — the UI Review Agent runs alongside Architecture, Security, Performance, and Test Coverage agents when changes touch frontend code
3. **As part of `/implement`** — after code agents complete, if the implementation unit includes UI components, the UI Review Agent checks them before the integration check
