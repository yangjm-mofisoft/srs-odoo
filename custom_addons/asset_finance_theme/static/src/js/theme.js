/** @odoo-module **/

/**
 * Asset Finance - Modern Theme JavaScript
 * Handles theme interactions using Odoo's native lifecycle services.
 */

import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser/browser";

// ============================================================
// Theme Service
// ============================================================
const themeService = {
    dependencies: ["ui", "action"],

    start(env, { ui, action }) {
        console.log("Asset Finance Theme Service: Initializing...");

        // 1. Enable Smooth Scrolling globally
        document.documentElement.style.scrollBehavior = "smooth";

        // 2. Apply critical theme styles via JavaScript (fallback)
        const applyThemeStyles = () => {
            const navbar = document.querySelector('.o_main_navbar');
            if (navbar) {
                navbar.style.cssText = 'background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important; box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important; border-bottom: none !important;';
                console.log("Asset Finance Theme: Navbar styled via JS");
            }

            // Apply body styles
            const body = document.body;
            if (body) {
                body.style.fontFamily = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
                body.style.backgroundColor = "#f9fafb";
            }
        };

        // Apply immediately and on DOM changes
        applyThemeStyles();
        setTimeout(applyThemeStyles, 100);
        setTimeout(applyThemeStyles, 500);

        // 3. Register Global Keyboard Shortcuts
        window.addEventListener("keydown", (e) => {
            // CTRL+K: Focus on Search Bar (Standard "Command Palette" feel)
            if ((e.ctrlKey || e.metaKey) && e.key === "k") {
                e.preventDefault();
                const searchInput = document.querySelector(".o_searchview input");
                if (searchInput) {
                    searchInput.focus();
                }
            }
        });

        console.log("Asset Finance Theme Service: Started Successfully");
    }
};

// Register the service so it starts automatically when Odoo loads
registry.category("services").add("asset_finance_theme", themeService);


// ============================================================
// Utilities (Optional)
// ============================================================
// We keep these strictly for any XML views that might be calling 
// window.AssetFinanceTheme.formatCurrency() directly.
// If you are not using these in your Views (XML), you can delete this section.

function formatCurrency(amount, currency = 'SGD') {
    return new Intl.NumberFormat('en-SG', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

function formatNumber(number, decimals = 2) {
    return new Intl.NumberFormat('en-SG', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(number);
}

// Expose utilities globally (Legacy support)
window.AssetFinanceTheme = {
    formatCurrency,
    formatNumber,
    // showLoadingIndicator removed: Use Odoo's native UI blocking instead
    // hideLoadingIndicator removed
};