# DocuMind AI — Phase 13 Product UI & Design System

## 1. Overview & Hallmark Design Philosophy

Phase 13 establishes the unified product experience for **DocuMind AI** by synthesising capabilities from all previous modules (Phases 1 through 12) into a cohesive, production-grade SaaS user interface. Built upon Hallmark design standards, the UI prioritises:

- **Clarity over Clutter**: Information density is balanced with generous whitespace, subtle 1px borders (`border-border`), and muted card backgrounds (`bg-card`).
- **Predictable Navigation**: Universal sidebar structure categorised by functional domains (Workspace, Intelligence, Processing, System) paired with dynamic breadcrumb trails and `Ctrl+K` command orchestration.
- **Accessibility by Default**: High-contrast typography, focus ring indicators (`ring-2 ring-primary focus-visible:outline-hidden`), full keyboard navigation, and screen-reader accessible ARIA roles.
- **Adaptive Intelligence Context**: The Universal File Inspector automatically adapts controls, visualisations, and actionable suggestions according to the inspected file format category.

---

## 2. Token Architecture & Theme Styling

The design system relies on Tailwind CSS v4 variables configured in `frontend/src/index.css`. The application supports full light and dark mode toggling with zero flash of unstyled content:

| Token | Light Theme Value | Dark Theme Value | Purpose |
|---|---|---|---|
| `--background` | `hsl(0 0% 100%)` | `hsl(222.2 84% 4.9%)` | Platform canvas background |
| `--foreground` | `hsl(222.2 84% 4.9%)` | `hsl(210 40% 98%)` | Primary typographic content |
| `--card` | `hsl(0 0% 100%)` | `hsl(222.2 84% 6.5%)` | Elevated content panels & cards |
| `--primary` | `hsl(221.2 83.2% 53.3%)` | `hsl(217.2 91.2% 59.8%)` | Primary interactive brand color |
| `--muted` | `hsl(210 40% 96.1%)` | `hsl(217.2 32.6% 17.5%)` | Subdued backgrounds & tags |
| `--muted-foreground`| `hsl(215.4 16.3% 46.9%)` | `hsl(215 20.2% 65.1%)` | Secondary helper descriptions |
| `--border` | `hsl(214.3 31.8% 91.4%)` | `hsl(217.2 32.6% 17.5%)` | Card and divider delineation |
| `--ring` | `hsl(221.2 83.2% 53.3%)` | `hsl(224.3 76.3% 48%)` | Accessible focus state rings |

---

## 3. Core UI Components

### 3.1 Button (`Button.tsx`)
- **Variants**: `primary`, `secondary`, `destructive`, `outline`, `ghost`, `link`.
- **Sizes**: `sm` (h-8, text-xs), `md` (h-9, text-xs), `lg` (h-10, text-sm).
- **Features**: Built-in SVG loading spinner (`isLoading`), left/right icon slots, automatic `disabled` state handling, and click inhibition during asynchronous loading.

### 3.2 Badge (`Badge.tsx`)
- **Variants**: `default`, `primary`, `success`, `warning`, `danger`, `purple`, `outline`.
- **Sizes**: `sm` (px-2 py-0.5, text-[10px]), `md` (px-2.5 py-1, text-xs).
- **Features**: Rounded-full pill presentation with semitransparent background and matching border tokens.

### 3.3 Modal (`Modal.tsx`)
- **Features**: Portal-like full-screen overlay with backdrop blur (`backdrop-blur-xs`), smooth CSS transitions, automatic scroll prevention on `document.body`, `Escape` key dismissal listener, and custom maximum widths (`sm` through `full`).

### 3.4 Tooltip (`Tooltip.tsx`)
- **Features**: Micro-interaction hover assistance with configurable positions (`top`, `bottom`, `left`, `right`), pointer events prevention, and smooth fade-in animations. Used extensively in the collapsed sidebar state.

### 3.5 Command Palette (`CommandPalette.tsx`)
- **Invocation**: Global keyboard shortcut (`Ctrl+K` or `Cmd+K`) or header search click.
- **Capabilities**: Full keyboard navigation (`ArrowUp`, `ArrowDown`, `Enter`), fast client-side fuzzy filtering across navigation routes, common actions (upload, clear queue, toggle dark mode), and existing stored files.

### 3.6 Toast System (`ToastContext.tsx`)
- **Types**: `success`, `error`, `warning`, `info`.
- **Behavior**: Auto-dismissing after 4000ms, close button, stacking order, accessibility labels, and icon cues.

---

## 4. Application Shell Architecture

```
+------------------------------------------------------------------------------------+
| Sidebar (Left)            | Header (Top)                                           |
|                           | [Breadcrumbs]     [Search / Ctrl+K]  [Upload] [Theme]  |
| - Logo & Platform Title   +--------------------------------------------------------+
| - Workspace Section       | Main View Canvas                                       |
|   - Dashboard             |                                                        |
|   - Upload & Ingest       |   (DashboardPage, FileLibraryPage, UniversalInspector, |
|   - File Library          |    AIWorkspacePage, KnowledgeSearchPage, JobsPage,     |
| - Intelligence Section    |    BulkProcessingPage, SettingsPage)                   |
|   - AI Workspace          |                                                        |
|   - Knowledge Search      |                                                        |
| - Processing Section      |                                                        |
|   - Bulk Processing       |                                                        |
|   - Processing Jobs       |                                                        |
| - System Section          |                                                        |
|   - System Status         |                                                        |
|   - Settings              |                                                        |
+------------------------------------------------------------------------------------+
```

### 4.1 Responsive Breakpoints
- **Mobile (< 768px)**: Sidebar is rendered as a drawer overlay toggled via the hamburger icon in Header. Full-width cards with single-column layouts.
- **Tablet (768px - 1024px)**: Collapsible sidebar option, 2-column dashboard grids, condensed table columns.
- **Desktop (>= 1024px)**: Fixed 256px sidebar, multi-column dashboard layouts, comprehensive table actions with side-by-side inspector views.
