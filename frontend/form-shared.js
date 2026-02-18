/**
 * VictoryFormMixin
 * Shared Alpine.js mixin for form handling in Member Form and Admin Console.
 * Reduces duplication of validation, formatting, and data loading logic.
 * Depends on VictoryUtils (utils.js).
 */
const VictoryFormMixin = {
    // Lifecycle
    async init() {
        // Dark mode logic
        const savedTheme = localStorage.getItem('darkMode');
        this.isDarkMode = savedTheme !== null ? JSON.parse(savedTheme) : false;

        this.$watch('isDarkMode', val => {
            localStorage.setItem('darkMode', JSON.stringify(val));
        });

        // Load reference data
        await this.loadReferenceData();
    },

    // Data Loading
    async loadReferenceData() {
        const data = await VictoryUtils.fetchReferenceData();
        if (data) {
            this.applyReferenceData(data);
        } else {
            this.useFallbackData();
        }
    },

    // Validation Wrappers (binds to this.form, this.errors)
    validateEmail() {
        if (!this.form.email) {
            this.errors.email = true;
            return;
        }
        this.errors.email = !VictoryUtils.validateEmail(this.form.email);
    },

    validateDate(field) {
        const val = this.form[field];
        if (!val) {
            this.errors[field] = true;
            return;
        }
        this.errors[field] = !VictoryUtils.validateDate(val);
    },

    // Formatting Wrappers (binds to this.form, this.touched, this.errors)
    formatPhone(field, isRequired) {
        this.touched[field] = true;
        this.form[field] = VictoryUtils.formatPhone(this.form[field]);

        if (isRequired) {
            this.errors[field] = this.form[field].length !== 9;
        } else {
            this.errors[field] = this.form[field].length > 0 && this.form[field].length !== 9;
        }
    },

    formatDate(field) {
        this.touched[field] = true;
        this.form[field] = VictoryUtils.formatDate(this.form[field]);
        this.validateDate(field);
    },

    formatNumber(input) {
        if (input && input.value) {
            input.value = VictoryUtils.formatNumber(input.value);
        } else if (typeof input === 'string') {
            // If called with a string/model directly (though usually called with $el/input)
            return VictoryUtils.formatNumber(input);
        }
    },

    // Helper to parse comma-separated strings or arrays into arrays
    parseListField(value) {
        if (Array.isArray(value)) return value;
        if (typeof value === 'string' && value.trim()) {
            return value.split(',').map(s => s.trim()).filter(s => s);
        }
        return [];
    }
};

// Expose for usage
if (typeof window !== 'undefined') {
    window.VictoryFormMixin = VictoryFormMixin;
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = VictoryFormMixin;
}
