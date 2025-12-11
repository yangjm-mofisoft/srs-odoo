# Asset Finance - Modern Bootstrap 5 Theme

A beautiful, modern admin theme for Odoo 19 Asset Finance module, featuring Bootstrap 5 styling, smooth animations, and responsive design.

## ✨ Features

- **Modern Bootstrap 5 Design** - Clean, professional interface with beautiful gradients
- **Responsive Layout** - Works seamlessly on desktop, tablet, and mobile devices
- **Enhanced UI Components** - Styled cards, forms, tables, and buttons
- **Smooth Animations** - Fade-in effects and hover transitions
- **Custom Dashboard** - Beautiful KPI cards and chart containers
- **Professional Color Scheme** - Modern blue gradient with carefully chosen accent colors
- **Improved Typography** - Using Inter font for better readability
- **Enhanced Forms** - Better input fields, labels, and validation states
- **Modern Menu System** - Improved navigation with hover effects
- **Keyboard Shortcuts** - Ctrl+S to save, Ctrl+K for search, ESC to cancel

## 🚀 Installation

### Step 1: Install the Module

1. Restart Odoo to detect the new module:
   ```bash
   docker-compose restart web
   ```

2. Update the app list in Odoo:
   - Go to **Apps** menu
   - Click "Update Apps List"
   - Search for "Asset Finance - Modern Bootstrap 5 Theme"

3. Install the module:
   - Click **Install** button

### Step 2: Verify Installation

1. Refresh your browser (Ctrl+F5 or Cmd+Shift+R)
2. You should immediately see the new modern theme applied
3. Check that:
   - Navigation bar has gradient blue background
   - Forms have rounded corners and shadows
   - Buttons have modern styling with hover effects
   - Typography uses Inter font

## 🎨 Theme Components

### CSS Files

1. **modern_theme.css** - Main theme styles (navbar, buttons, general layout)
2. **dashboard.css** - KPI cards, charts, and dashboard components
3. **forms.css** - Form fields, inputs, labels, and validation
4. **menu.css** - Navigation menu and sidebar styling
5. **components.css** - Reusable components (badges, alerts, modals, etc.)

### SCSS Files

1. **bootstrap5_variables.scss** - Bootstrap 5 variable overrides (colors, spacing, etc.)
2. **theme.scss** - Main SCSS file with mixins and utilities

### JavaScript

1. **theme.js** - Interactive enhancements:
   - Smooth scrolling
   - Form animations
   - Keyboard shortcuts
   - Loading indicators
   - Tooltip initialization

## 🎯 Customization

### Changing Colors

Edit `static/src/scss/bootstrap5_variables.scss`:

```scss
// Primary brand color
$primary: #2563eb;  // Change this to your brand color

// Other colors
$success: #10b981;
$warning: #f59e0b;
$danger: #ef4444;
```

### Customizing Components

Each CSS file is organized by component type. Find the section you want to modify and update the styles.

Example - Changing button border radius:

```css
/* In modern_theme.css */
.btn, .o_form_button {
    border-radius: 0.5rem;  /* Change this value */
}
```

### Adding Custom Styles

Create a new CSS file in `static/src/css/` and add it to the manifest:

```python
'assets': {
    'web.assets_backend': [
        # ... existing files ...
        'asset_finance_theme/static/src/css/my_custom_styles.css',
    ],
},
```

## 📱 Responsive Breakpoints

The theme includes responsive design for all screen sizes:

- **Desktop**: ≥ 1200px (full layout)
- **Tablet**: 768px - 1199px (medium layout)
- **Mobile**: < 768px (compact layout)

## ⌨️ Keyboard Shortcuts

- **Ctrl/Cmd + S** - Save current form
- **Ctrl/Cmd + K** - Focus on search bar
- **ESC** - Cancel/close current form or modal

## 🎭 Theme Classes

Use these custom classes in your views:

### KPI Cards
```xml
<div class="af-kpi-card">
    <div class="kpi-icon primary">📊</div>
    <div class="kpi-label">Total Contracts</div>
    <div class="kpi-value">245</div>
    <div class="kpi-trend up">+12.5%</div>
</div>
```

### Status Pills
```xml
<span class="af-status-pill status-active">Active</span>
<span class="af-status-pill status-pending">Pending</span>
<span class="af-status-pill status-completed">Completed</span>
```

### Modern Cards
```xml
<div class="modern-card">
    <div class="card-header">Card Title</div>
    <div class="card-body">Card content...</div>
</div>
```

## 🐛 Troubleshooting

### Theme Not Applied

1. **Clear browser cache**: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)
2. **Clear Odoo assets**:
   - Go to Settings > Technical > Database Structure > Assets
   - Delete all assets
   - Restart Odoo
3. **Check module installation**: Ensure the theme module is installed and dependencies are met

### CSS Not Loading

1. Check browser console for errors (F12)
2. Verify file paths in `__manifest__.py`
3. Restart Odoo after making changes to asset files

### JavaScript Errors

1. Open browser console (F12)
2. Check for error messages
3. Verify that `/asset_finance_theme/static/src/js/theme.js` is loaded

## 📄 License

LGPL-3

## 👨‍💻 Developer

**Mofisoft PTE. LTD.**

## 🔄 Version History

### Version 1.0.0 (2025-12-11)
- Initial release
- Modern Bootstrap 5 design
- Responsive layout
- Enhanced forms and components
- Custom dashboard styling
- Keyboard shortcuts
- Smooth animations

## 🤝 Support

For issues and feature requests, please contact Mofisoft support.

---

**Enjoy your beautiful new theme!** 🎉
