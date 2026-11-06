# DocuMind AI — Accessibility & WCAG AA Compliance (Phase 13)

## 1. Compliance Standards

DocuMind AI aims for full compliance with the **Web Content Accessibility Guidelines (WCAG) 2.1 Level AA**. The platform is designed to be fully usable by individuals relying on keyboard navigation, screen readers, and high-contrast display modes.

---

## 2. Accessible Design Elements

### 2.1 Color Contrast
- Normal text meets a contrast ratio of at least 4.5:1 against card and background surfaces.
- Large headers and prominent badges meet at least 3.0:1 contrast.
- Visual status indicators pair colors with icons or explicit textual labels (e.g. green dot + check icon + "Processed" text) to prevent color-only signal dependence.

### 2.2 Focus Indicators & Outline Rings
- All interactive elements (buttons, inputs, links, dropdowns) carry uniform focus rings:
  ```css
  focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2
  ```
- Focus states are preserved in both light and dark themes.

### 2.3 Keyboard Navigation Matrix
| Key Combination | Scope | Action |
|---|---|---|
| `Tab` / `Shift+Tab` | Universal | Forward / backward sequential element navigation |
| `Ctrl+K` / `Cmd+K` | Global | Opens the Command Palette |
| `Escape` | Modals / Dialogs / Palette | Closes active overlay and returns focus to trigger element |
| `ArrowUp` / `ArrowDown` | Command Palette & Dropdowns | Navigates candidate list items |
| `Enter` / `Space` | Buttons & List Items | Activates focused control |

### 2.4 Semantic Structure & ARIA Attributes
- Modals implement `role="dialog"`, `aria-modal="true"`, and accessible labels (`aria-label="Close dialog"`).
- Alert banners carry `role="alert"` for real-time screen reader notification.
- Tables implement `th` headers with `scope="col"` and accessible row labels.
- Sidebar links utilize `aria-current="page"` when active.
