/**
 * Shared utilities used across all frontend pages.
 */

const App = {
    /**
     * Format a number as US currency.
     */
    formatCurrency(value) {
        const num = parseFloat(value);
        if (isNaN(num)) return "$0.00";
        return new Intl.NumberFormat("en-US", {
            style: "currency",
            currency: "USD",
        }).format(num);
    },

    /**
     * Show a toast notification.
     */
    showToast(message, type = "success") {
        const toast = document.getElementById("toast");
        const toastMessage = document.getElementById("toast-message");
        const toastIcon = document.getElementById("toast-icon");
        if (!toast) return;

        toastMessage.textContent = message;
        toastIcon.textContent = type === "success" ? "✓" : "⚠";
        toast.classList.add("show");
        setTimeout(() => {
            toast.classList.remove("show");
        }, 3000);
    },

    /**
     * Show or hide the loading overlay.
     */
    setLoading(show, message = "Loading...") {
        const overlay = document.getElementById("loading-overlay");
        const msgEl = document.getElementById("loading-message");
        if (!overlay) return;
        if (msgEl) msgEl.textContent = message;
        overlay.classList.toggle("hidden", !show);
    },

    /**
     * Make an API request with JSON body and return JSON response.
     */
    async api(url, options = {}) {
        const defaults = {
            headers: {
                "Content-Type": "application/json",
            },
        };
        const response = await fetch(url, { ...defaults, ...options });
        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.error || `HTTP ${response.status}`);
        }
        return response.json();
    },

    /**
     * Calculate age from a date string (YYYY-MM-DD).
     */
    calculateAge(dobString) {
        if (!dobString) return null;
        const dob = new Date(dobString);
        if (isNaN(dob)) return null;
        const today = new Date();
        let age = today.getFullYear() - dob.getFullYear();
        const m = today.getMonth() - dob.getMonth();
        if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) {
            age--;
        }
        return age;
    },

    /**
     * Parse a float safely, defaulting to 0.
     */
    parseFloat(value) {
        if (value === "" || value === null || value === undefined) return 0;
        const num = parseFloat(value);
        return isNaN(num) ? 0 : num;
    },
};

// Expose globally for page-specific scripts
window.App = App;
