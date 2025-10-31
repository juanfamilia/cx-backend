# SIETE CX - ACCESSIBILITY GUIDELINES

**Version:** 1.0  
**Last Updated:** January 2025  
**Target:** WCAG 2.1 Level AA & Lighthouse Score 90+

---

## TABLE OF CONTENTS

1. [Overview](#1-overview)
2. [ARIA Implementation](#2-aria-implementation)
3. [Keyboard Navigation](#3-keyboard-navigation)
4. [Color & Contrast](#4-color--contrast)
5. [Screen Reader Support](#5-screen-reader-support)
6. [Forms & Validation](#6-forms--validation)
7. [Testing Checklist](#7-testing-checklist)
8. [Lighthouse Optimization](#8-lighthouse-optimization)

---

## 1. OVERVIEW

### 1.1 Accessibility Commitment

Siete CX is committed to ensuring our platform is accessible to all users, including those with disabilities. We follow:

- **WCAG 2.1 Level AA** standards
- **Section 508** compliance
- **ADA** (Americans with Disabilities Act) requirements
- **Lighthouse Accessibility** score target: 90+

### 1.2 Core Principles (POUR)

- **Perceivable:** Information presented in ways users can perceive
- **Operable:** UI components and navigation are operable
- **Understandable:** Information and operation are understandable
- **Robust:** Content is robust enough for assistive technologies

---

## 2. ARIA IMPLEMENTATION

### 2.1 ARIA Landmarks

**Required landmarks for all pages:**

```html
<header role="banner">
  <nav role="navigation" aria-label="Main navigation">
    <!-- Navigation items -->
  </nav>
</header>

<main role="main" id="main-content">
  <!-- Main content -->
</main>

<aside role="complementary" aria-label="Sidebar">
  <!-- Sidebar content -->
</aside>

<footer role="contentinfo">
  <!-- Footer content -->
</footer>
```

### 2.2 ARIA Labels

**Dashboard Widgets:**
```html
<div role="region" aria-labelledby="nps-widget-title">
  <h3 id="nps-widget-title">NPS Trend</h3>
  <canvas aria-label="Line chart showing NPS trend over 30 days"></canvas>
</div>
```

**Interactive Elements:**
```html
<button 
  aria-label="Delete evaluation"
  aria-describedby="delete-hint"
>
  <span aria-hidden="true">🗑️</span>
</button>
<span id="delete-hint" class="sr-only">
  This action cannot be undone
</span>
```

**Tables:**
```html
<table aria-labelledby="evaluations-table-caption">
  <caption id="evaluations-table-caption">
    Company Evaluations (150 total)
  </caption>
  <thead>
    <tr>
      <th scope="col">ID</th>
      <th scope="col">Campaign</th>
      <th scope="col">Status</th>
    </tr>
  </thead>
  <tbody>
    <!-- Rows -->
  </tbody>
</table>
```

### 2.3 ARIA States

**Loading States:**
```html
<button aria-busy="true" disabled>
  <span class="spinner" role="status" aria-label="Loading..."></span>
  Submitting...
</button>
```

**Expanded/Collapsed:**
```html
<button 
  aria-expanded="false" 
  aria-controls="filters-panel"
  @click="toggleFilters()"
>
  Show Filters
</button>

<div id="filters-panel" [hidden]="!filtersExpanded">
  <!-- Filters -->
</div>
```

**Selected States:**
```html
<div role="tablist">
  <button 
    role="tab" 
    aria-selected="true"
    aria-controls="dashboard-panel"
  >
    Dashboard
  </button>
  <button 
    role="tab" 
    aria-selected="false"
    aria-controls="reports-panel"
  >
    Reports
  </button>
</div>
```

---

## 3. KEYBOARD NAVIGATION

### 3.1 Focus Management

**Skip Links (first element on page):**
```html
<a href="#main-content" class="skip-link">
  Skip to main content
</a>

<style>
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: #8b5cf6;
  color: white;
  padding: 8px;
  z-index: 100;
}

.skip-link:focus {
  top: 0;
}
</style>
```

**Focus Visible (always show focus indicators):**
```css
:focus-visible {
  outline: 2px solid #8b5cf6;
  outline-offset: 2px;
}

button:focus-visible,
a:focus-visible,
input:focus-visible {
  outline: 2px solid #8b5cf6;
  outline-offset: 2px;
}
```

### 3.2 Tab Order

**Ensure logical tab order:**
- Use `tabindex="0"` for interactive custom elements
- Use `tabindex="-1"` for elements that should receive focus programmatically but not via Tab
- **Never** use `tabindex > 0`

**Example - Modal Dialog:**
```typescript
openModal() {
  // Store currently focused element
  this.previouslyFocusedElement = document.activeElement;
  
  // Show modal
  this.showModal = true;
  
  // Focus first focusable element in modal
  setTimeout(() => {
    const firstInput = this.modalRef.nativeElement.querySelector('input, button');
    firstInput?.focus();
  });
}

closeModal() {
  this.showModal = false;
  
  // Return focus to previously focused element
  this.previouslyFocusedElement?.focus();
}
```

### 3.3 Keyboard Shortcuts

**Essential shortcuts:**
- `Tab` / `Shift+Tab` - Navigate between focusable elements
- `Enter` / `Space` - Activate buttons/links
- `Escape` - Close modals/dropdowns
- `Arrow Keys` - Navigate within components (menus, tabs, etc.)
- `Home` / `End` - Go to first/last item in lists

**Dropdown Example:**
```typescript
@HostListener('keydown', ['$event'])
handleKeyboard(event: KeyboardEvent) {
  switch(event.key) {
    case 'ArrowDown':
      event.preventDefault();
      this.focusNextItem();
      break;
    case 'ArrowUp':
      event.preventDefault();
      this.focusPreviousItem();
      break;
    case 'Escape':
      this.closeDropdown();
      break;
  }
}
```

---

## 4. COLOR & CONTRAST

### 4.1 Contrast Ratios (WCAG AA)

**Minimum requirements:**
- Normal text (< 18px): 4.5:1
- Large text (≥ 18px or 14px bold): 3:1
- UI components and graphics: 3:1

**Siete CX Color Palette (AA Compliant):**

```css
/* Primary Colors */
--primary: #8b5cf6;      /* On white: 4.52:1 ✅ */
--primary-dark: #6d28d9; /* Better contrast: 7.04:1 ✅ */

/* Success */
--success: #10b981;      /* On white: 2.85:1 ⚠️ (use darker variant for text) */
--success-dark: #059669; /* On white: 4.54:1 ✅ */

/* Warning */
--warning: #f59e0b;      /* On white: 2.37:1 ❌ */
--warning-dark: #d97706; /* On white: 4.51:1 ✅ */

/* Error */
--error: #ef4444;        /* On white: 3.94:1 ⚠️ */
--error-dark: #dc2626;   /* On white: 5.33:1 ✅ */
```

**Usage Guidelines:**
```css
/* ❌ Bad - Insufficient contrast */
.status-badge {
  background: #10b981;
  color: white; /* Only 2.85:1 */
}

/* ✅ Good - Sufficient contrast */
.status-badge {
  background: #059669;
  color: white; /* 4.54:1 ✅ */
}
```

### 4.2 Color Independence

**Never rely on color alone:**

```html
<!-- ❌ Bad - Color only -->
<span class="text-red-500">High Priority</span>

<!-- ✅ Good - Icon + Color + Text -->
<span class="text-red-700">
  <svg aria-hidden="true" class="icon">⚠️</svg>
  <span class="font-semibold">High Priority</span>
</span>
```

**Charts Accessibility:**
```html
<canvas 
  aria-label="Bar chart showing evaluation status. 
              150 completed (green), 
              50 pending (orange), 
              20 analyzing (blue)"
></canvas>

<!-- Provide data table alternative -->
<table class="sr-only">
  <caption>Evaluation Status Data</caption>
  <tr><td>Completed</td><td>150</td></tr>
  <tr><td>Pending</td><td>50</td></tr>
  <tr><td>Analyzing</td><td>20</td></tr>
</table>
```

---

## 5. SCREEN READER SUPPORT

### 5.1 Screen Reader Only Content

```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}
```

**Usage:**
```html
<button>
  <svg aria-hidden="true"><!-- Icon --></svg>
  <span class="sr-only">Delete evaluation</span>
</button>
```

### 5.2 Live Regions

**Announcements:**
```html
<div 
  role="status" 
  aria-live="polite" 
  aria-atomic="true"
  class="sr-only"
>
  {{ statusMessage }}
</div>
```

**Critical Alerts:**
```html
<div 
  role="alert" 
  aria-live="assertive" 
  aria-atomic="true"
>
  Error: Evaluation failed to save
</div>
```

**TypeScript Example:**
```typescript
announceToScreenReader(message: string) {
  const announcement = document.createElement('div');
  announcement.setAttribute('role', 'status');
  announcement.setAttribute('aria-live', 'polite');
  announcement.classList.add('sr-only');
  announcement.textContent = message;
  
  document.body.appendChild(announcement);
  
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
}
```

### 5.3 Hiding Decorative Content

```html
<!-- Icons that are purely decorative -->
<span aria-hidden="true">🎉</span>

<!-- SVG icons -->
<svg aria-hidden="true" focusable="false">
  <!-- Icon paths -->
</svg>
```

---

## 6. FORMS & VALIDATION

### 6.1 Form Labels

**Always associate labels with inputs:**

```html
<!-- ✅ Good - Explicit association -->
<label for="email-input">Email Address</label>
<input 
  id="email-input" 
  type="email" 
  required 
  aria-required="true"
/>

<!-- ✅ Good - Implicit association -->
<label>
  Email Address
  <input type="email" required />
</label>
```

### 6.2 Error Messages

**Link errors to fields:**
```html
<label for="password-input">Password</label>
<input 
  id="password-input"
  type="password"
  aria-invalid="true"
  aria-describedby="password-error"
/>
<span id="password-error" class="error" role="alert">
  Password must be at least 8 characters
</span>
```

**Form-level errors:**
```html
<div role="alert" class="error-summary">
  <h2 id="error-heading">There are 2 errors in this form</h2>
  <ul aria-labelledby="error-heading">
    <li><a href="#email-input">Email is required</a></li>
    <li><a href="#password-input">Password is too short</a></li>
  </ul>
</div>
```

### 6.3 Required Fields

```html
<label for="campaign-name">
  Campaign Name
  <abbr title="required" aria-label="required">*</abbr>
</label>
<input 
  id="campaign-name"
  required
  aria-required="true"
/>
```

---

## 7. TESTING CHECKLIST

### 7.1 Manual Testing

- [ ] Navigate entire app using only keyboard (no mouse)
- [ ] Test with screen reader (NVDA/JAWS/VoiceOver)
- [ ] Zoom to 200% - ensure no content loss
- [ ] Test in high contrast mode (Windows)
- [ ] Disable CSS - ensure content order is logical
- [ ] Test all form submissions with errors

### 7.2 Automated Testing Tools

**Browser Extensions:**
- axe DevTools
- WAVE
- Lighthouse (Chrome DevTools)
- IBM Equal Access Accessibility Checker

**Command Line:**
```bash
# Lighthouse CI
npm install -g @lhci/cli
lhci autorun --collect.url=https://cx.sieteic.com
```

**Angular Testing:**
```typescript
// Install: npm install --save-dev axe-core @axe-core/playwright
import { injectAxe, checkA11y } from 'axe-playwright';

test('Dashboard should be accessible', async ({ page }) => {
  await page.goto('/dashboard');
  await injectAxe(page);
  await checkA11y(page, null, {
    detailedReport: true,
    detailedReportOptions: { html: true }
  });
});
```

---

## 8. LIGHTHOUSE OPTIMIZATION

### 8.1 Target Metrics

- **Accessibility Score:** ≥ 90
- **Performance:** ≥ 85
- **Best Practices:** ≥ 90
- **SEO:** ≥ 90

### 8.2 Common Issues & Fixes

**Issue: Missing alt text**
```html
<!-- ❌ Bad -->
<img src="chart.png">

<!-- ✅ Good -->
<img src="chart.png" alt="NPS trend chart showing improvement from 7.5 to 8.2">
```

**Issue: Low contrast**
```html
<!-- ❌ Bad -->
<p class="text-gray-400">Subtle text</p> <!-- Contrast: 2.5:1 -->

<!-- ✅ Good -->
<p class="text-gray-700">Readable text</p> <!-- Contrast: 4.7:1 -->
```

**Issue: Missing form labels**
```html
<!-- ❌ Bad -->
<input placeholder="Search...">

<!-- ✅ Good -->
<label for="search">Search</label>
<input id="search" placeholder="Search...">
```

**Issue: Insufficient tap target size**
```css
/* All interactive elements should be at least 44x44px */
button,
a.clickable {
  min-height: 44px;
  min-width: 44px;
  padding: 12px 16px;
}
```

---

## APPENDIX A: ARIA Roles Reference

| Role | Usage | Example |
|------|-------|---------|
| `alert` | Important message | Error notifications |
| `button` | Clickable action | Custom button elements |
| `checkbox` | Toggle option | Custom checkboxes |
| `dialog` | Modal window | Confirmation dialogs |
| `menu` | Menu container | Dropdown menus |
| `menuitem` | Menu option | Dropdown menu item |
| `navigation` | Navigation area | Main nav, sidebar |
| `region` | Generic landmark | Widget containers |
| `search` | Search form | Search input area |
| `status` | Status update | Loading indicators |
| `tab` | Tab in tablist | Dashboard tabs |
| `tabpanel` | Tab content | Tab content area |

---

## APPENDIX B: Testing with Screen Readers

**NVDA (Windows - Free):**
- Download: https://www.nvaccess.org/
- Start: `Ctrl + Alt + N`
- Stop: `Insert + Q`
- Read next: `Down Arrow`

**JAWS (Windows - Paid):**
- Most popular enterprise screen reader
- Demo: https://www.freedomscientific.com/

**VoiceOver (macOS - Built-in):**
- Start: `Cmd + F5`
- Navigate: `Ctrl + Option + Arrow Keys`

**Mobile:**
- iOS VoiceOver: Settings → Accessibility → VoiceOver
- Android TalkBack: Settings → Accessibility → TalkBack

---

**End of Accessibility Documentation**

For UI implementation, see Angular component guidelines.  
For testing procedures, see `/docs/TESTING.md` (Phase 5).
