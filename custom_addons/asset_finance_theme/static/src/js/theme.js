/** @odoo-module **/

/**
 * Asset Finance - Modern Theme JavaScript
 * Handles theme interactions using Odoo's native lifecycle services.
 */

/** @odoo-module **/

import { registry } from "@web/core/registry";

// ============================================================
// Theme Service
// ============================================================
const themeService = {
    dependencies: ["ui"], // 'action' dependency removed as it wasn't used

    start(env, { ui }) {
        console.log("Asset Finance Theme: Service Started");

        // 1. Global Keyboard Shortcuts
        // We attach to the window, but we should be careful about cleaning up.
        const handleKeydown = (e) => {
            // CTRL+K: Focus on Search Bar
            if ((e.ctrlKey || e.metaKey) && e.key === "k") {
                e.preventDefault();
                // Odoo 17/19 specific selector for the control panel search
                const searchInput = document.querySelector(".o_searchview input") || 
                                    document.querySelector(".o_control_panel .o_searchview input");
                if (searchInput) {
                    searchInput.focus();
                }
            }
        };

        window.addEventListener("keydown", handleKeydown);

        // Note: In a pure component (not a service), we would removeEventListener on destroy.
        // Since this is a persistent service, it stays alive for the session.
    }
};

registry.category("services").add("asset_finance_theme", themeService);

// ============================================================
// Utilities
// ============================================================
// Export these as standard ES modules if other files need them
// import { formatCurrency } from "@asset_finance_theme/js/theme";

export function formatCurrency(amount, currency = 'SGD') {
    return new Intl.NumberFormat('en-SG', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

export function formatNumber(number, decimals = 2) {
    return new Intl.NumberFormat('en-SG', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    }).format(number);
}