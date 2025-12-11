/** @odoo-module **/

/**
 * Asset Finance - Modern Theme JavaScript
 * Handles theme interactions and enhancements
 */

import { registry } from "@web/core/registry";

// ============================================================
// Smooth Scroll Enhancement
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    // Add smooth scroll behavior
    document.documentElement.style.scrollBehavior = 'smooth';

    // Enhance form animations
    enhanceFormAnimations();

    // Initialize tooltips
    initializeTooltips();

    // Add keyboard shortcuts
    registerKeyboardShortcuts();
});

// ============================================================
// Form Animation Enhancements
// ============================================================

function enhanceFormAnimations() {
    // Observe form view changes
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.addedNodes.length) {
                mutation.addedNodes.forEach((node) => {
                    if (node.classList && node.classList.contains('o_form_view')) {
                        // Add fade-in animation
                        node.style.opacity = '0';
                        node.style.transform = 'translateY(10px)';

                        setTimeout(() => {
                            node.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                            node.style.opacity = '1';
                            node.style.transform = 'translateY(0)';
                        }, 10);
                    }
                });
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

// ============================================================
// Tooltip Enhancement
// ============================================================

function initializeTooltips() {
    // Initialize Bootstrap tooltips if available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }
}

// ============================================================
// Keyboard Shortcuts
// ============================================================

function registerKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + S to save form
        if ((e.ctrlKey || e.metaKey) && e.key === 's') {
            e.preventDefault();
            const saveButton = document.querySelector('.o_form_button_save');
            if (saveButton && !saveButton.disabled) {
                saveButton.click();
            }
        }

        // Ctrl/Cmd + K for quick search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('.o_searchview input');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // Esc to cancel/close
        if (e.key === 'Escape') {
            const cancelButton = document.querySelector('.o_form_button_cancel');
            if (cancelButton && !cancelButton.disabled) {
                cancelButton.click();
            }
        }
    });
}

// ============================================================
// Card Hover Effects
// ============================================================

document.addEventListener('DOMContentLoaded', function() {
    // Add hover effects to cards
    const cards = document.querySelectorAll('.af-kpi-card, .af-chart-card, .modern-card');

    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-4px)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
});

// ============================================================
// Loading State Enhancement
// ============================================================

// Note: Removed fetch override to avoid conflicts with Odoo's RPC system

function showLoadingIndicator() {
    let indicator = document.querySelector('.af-loading-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.className = 'af-loading-indicator';
        indicator.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        `;
        indicator.style.cssText = `
            position: fixed;
            top: 70px;
            right: 20px;
            z-index: 9999;
            background: white;
            padding: 12px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        `;
        document.body.appendChild(indicator);
    }
    indicator.style.display = 'block';
}

function hideLoadingIndicator() {
    const indicator = document.querySelector('.af-loading-indicator');
    if (indicator) {
        indicator.style.display = 'none';
    }
}

// ============================================================
// Number Formatting
// ============================================================

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

// Export utilities
window.AssetFinanceTheme = {
    formatCurrency,
    formatNumber,
    showLoadingIndicator,
    hideLoadingIndicator
};

// ============================================================
// Console Welcome Message
// ============================================================

console.log('%c Asset Finance - Modern Theme ', 'background: #2563eb; color: white; padding: 8px 16px; border-radius: 4px; font-weight: bold; font-size: 14px;');
console.log('%c Version 1.0.0 | Powered by Bootstrap 5 ', 'color: #64748b; font-size: 12px;');
console.log('%c Theme loaded successfully! ', 'color: #10b981; font-weight: bold;');

// ============================================================
// Auto-refresh Enhancements
// ============================================================

// Note: Removed window.location.reload override as it's read-only in modern browsers

// ============================================================
// Form Field Focus Enhancement
// ============================================================

document.addEventListener('focusin', function(e) {
    if (e.target.matches('input, select, textarea')) {
        const fieldContainer = e.target.closest('.o_field_widget');
        if (fieldContainer) {
            fieldContainer.classList.add('af-field-focused');
        }
    }
});

document.addEventListener('focusout', function(e) {
    if (e.target.matches('input, select, textarea')) {
        const fieldContainer = e.target.closest('.o_field_widget');
        if (fieldContainer) {
            fieldContainer.classList.remove('af-field-focused');
        }
    }
});

// Add CSS for focused state
const style = document.createElement('style');
style.textContent = `
    .af-field-focused {
        position: relative;
    }
    .af-field-focused::before {
        content: '';
        position: absolute;
        top: -4px;
        left: -4px;
        right: -4px;
        bottom: -4px;
        border: 2px solid rgba(37, 99, 235, 0.2);
        border-radius: 0.5rem;
        pointer-events: none;
    }
`;
document.head.appendChild(style);
