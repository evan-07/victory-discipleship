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
        if (!regex.test(dateString)) return false;

        // Check logical validity
        const parts = dateString.split('/');
        const m = parseInt(parts[0], 10);
        const d = parseInt(parts[1], 10);
        const y = parseInt(parts[2], 10);

        const inputDate = new Date(y, m - 1, d);
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        return inputDate.getFullYear() === y &&
            inputDate.getMonth() === m - 1 &&
            inputDate.getDate() === d &&
            inputDate <= today;
    },

    // ==========================================
    // FORMATTING
    // ==========================================

    formatPhone(value) {
        if (!value) return '';
        const v = String(value).replace(/\D/g, '');
        return v.slice(0, 11);
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
