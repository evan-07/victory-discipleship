/**
 * VictoryUtils
 * Shared utility functions for Victory Discipleship frontend applications.
 * Reduces duplication between index.html (Member Form) and admin.js (Admin Console).
 */
const VictoryUtils = {
    // ==========================================
    // VALIDATION
    // ==========================================

    validateEmail(email) {
        if (!email) return false;
        if (email.length > 254) return false; // RFC 5321 limit to prevent ReDoS
        // Use a safe regex that avoids backtracking on dots within the domain
        const regex = /^[^\s@]+@([^\s@.]+\.)+[^\s@.]+$/;
        return regex.test(email);
    },

    validateDate(dateString) {
        if (!dateString) return false;
        // Check format MM/DD/YYYY
        const regex = /^(0[1-9]|1[0-2])\/(0[1-9]|[12]\d|3[01])\/(19|20)\d{2}$/;
        if (!regex.test(dateString)) return false; // Keep the regex test from original

        // Parse the date components
        const parts = dateString.split('/');
        if (parts.length !== 3) return false;

        const month = Number.parseInt(parts[0], 10);
        const day = Number.parseInt(parts[1], 10);
        const year = Number.parseInt(parts[2], 10);

        // Check if the date is valid
        if (isNaN(month) || isNaN(day) || isNaN(year)) return false;

        // Basic range check
        if (month < 1 || month > 12) return false;
        if (day < 1 || day > 31) return false;
        if (year < 1900 || year > 2100) return false;

        const date = new Date(year, month - 1, day);
        // Check if the date object created is valid and matches the input components
        // Also ensure the date is not in the future (original logic)
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        return date && (date.getMonth() + 1) === month && date.getDate() === day && date <= today;
    },

    // ==========================================
    // FORMATTING
    // ==========================================

    formatPhone(phone) {
        if (!phone) return '';
        // Remove non-numeric characters
        const cleaned = phone.toString().replace(/\D/g, ''); // Still use replace regex for global
        // Return only the last 10 digits/characters max (0917-123-4567 -> 9171234567 or last 11)
        // Adjusting logic to match typical 11 digit format but storing without prefix if needed
        return cleaned.substring(0, 11);
    },

    escapeHtml(unsafe) {
        if (!unsafe) return "";
        return unsafe
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll("\"", "&quot;")
            .replaceAll("'", "&#039;");
    },

    formatNumber(value) {
        if (!value) return '';
        return String(value).replace(/\D/g, '');
    },

    formatDate(value) {
        if (!value) return '';
        let v = String(value).replace(/\D/g, '').slice(0, 8);
        if (v.length >= 5) {
            return `${v.slice(0, 2)}/${v.slice(2, 4)}/${v.slice(4)}`;
        } else if (v.length >= 3) {
            return `${v.slice(0, 2)}/${v.slice(2)}`;
        }
        return v;
    },

    // ==========================================
    // DATA FETCHING & CACHING
    // ==========================================

    async fetchReferenceData() {
        const CACHE_KEY = 'victory_reference_data';
        const CACHE_TTL = 24 * 60 * 60 * 1000; // 24 hours

        // 1. Check LocalStorage Cache
        const cached = localStorage.getItem(CACHE_KEY);
        if (cached) {
            try {
                const { data, timestamp } = JSON.parse(cached);
                if (Date.now() - timestamp < CACHE_TTL) {
                    console.log('Using cached reference data');
                    return data;
                }
            } catch (e) {
                console.error('Cache parse error:', e);
            }
        }

        // 2. Fetch from API
        try {
            console.log('Fetching reference data from API...');
            const response = await fetch('https://member-api-132324496795.asia-southeast1.run.app/api/reference-data');
            const result = await response.json();

            if (result.result === 'success') {
                // Update Cache
                localStorage.setItem(CACHE_KEY, JSON.stringify({
                    data: result.data,
                    timestamp: Date.now()
                }));
                return result.data;
            }
        } catch (error) {
            console.error('Failed to load reference data:', error);
        }

        return null; // Return null to signal fallback required
    },

    getFallbackLists() {
        return {
            discipleshipClasses: [
                "One2One",
                "Victory Weekend",
                "Spiritual Foundations",
                "Discipleship Class / Leader's Lab",
                "Leadership L113"
            ],
            ministryOptions: [
                "Kids Church",
                "Multimedia",
                "Prayer",
                "Safety",
                "Stage Mgmt",
                "Technical",
                "Ushering",
                "Worship"
            ],
            wantMinistryOptions: [
                "None, I'll pray for it",
                "Kids Church",
                "Multimedia",
                "Prayer",
                "Safety",
                "Stage Mgmt",
                "Technical",
                "Ushering",
                "Worship"
            ]
        };
    }
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = VictoryUtils;
}
