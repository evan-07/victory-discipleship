const fs = require('fs');
const path = require('path');

// Mock localStorage
const localStorageMock = (function () {
    let store = {};
    return {
        getItem: function (key) {
            return store[key] || null;
        },
        setItem: function (key, value) {
            store[key] = value.toString();
        },
        clear: function () {
            store = {};
        }
    };
})();

Object.defineProperty(window, 'localStorage', {
    value: localStorageMock
});

// Mock fetch
global.fetch = jest.fn();

// Use require for coverage instrumentation
const VictoryUtils = require('../utils');

describe('VictoryUtils', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        localStorage.clear();
    });

    describe('Validation', () => {
        test('validateEmail returns true for valid emails', () => {
            expect(VictoryUtils.validateEmail('test@example.com')).toBe(true);
            expect(VictoryUtils.validateEmail('user.name+tag@domain.co.uk')).toBe(true);
            expect(VictoryUtils.validateEmail('user@sub.domain.com')).toBe(true);
        });

        test('validateEmail returns false for invalid emails', () => {
            expect(VictoryUtils.validateEmail('invalid-email')).toBe(false);
            expect(VictoryUtils.validateEmail('@domain.com')).toBe(false);
            expect(VictoryUtils.validateEmail('user@')).toBe(false);
            expect(VictoryUtils.validateEmail('')).toBe(false);
        });

        test('validateEmail rejects emails longer than 254 chars (ReDoS protection)', () => {
            const longEmail = 'a'.repeat(250) + '@example.com';
            expect(VictoryUtils.validateEmail(longEmail)).toBe(false);
        });

        test('validateDate returns true for valid MM/DD/YYYY dates', () => {
            expect(VictoryUtils.validateDate('12/31/2023')).toBe(true);
            expect(VictoryUtils.validateDate('01/01/1990')).toBe(true);
        });

        test('validateDate returns false for invalid dates', () => {
            expect(VictoryUtils.validateDate('31/12/2023')).toBe(false); // Day/Month swapped
            expect(VictoryUtils.validateDate('2023/12/31')).toBe(false); // Wrong format
            expect(VictoryUtils.validateDate('invalid')).toBe(false);
            expect(VictoryUtils.validateDate('')).toBe(false);
            expect(VictoryUtils.validateDate('02/30/2023')).toBe(false); // Invalid day
            const futureDate = new Date();
            futureDate.setFullYear(futureDate.getFullYear() + 1);
            const futureString = `01/01/${futureDate.getFullYear()}`;
            expect(VictoryUtils.validateDate(futureString)).toBe(false); // Future date
        });
    });

    describe('Formatting', () => {
        test('formatPhone strips non-digits and truncates to 11 chars', () => {
            expect(VictoryUtils.formatPhone('0917-123-4567')).toBe('09171234567');
            expect(VictoryUtils.formatPhone('+63 917 123 4567')).toBe('63917123456');
        });

        test('formatPhone handles empty input', () => {
            expect(VictoryUtils.formatPhone('')).toBe('');
            expect(VictoryUtils.formatPhone(null)).toBe('');
        });

        test('formatDate formats string input to MM/DD/YYYY style', () => {
            const input = '10252023';
            const formatted = VictoryUtils.formatDate(input);
            expect(formatted).toBe('10/25/2023');
        });

        test('formatDate handles partial inputs', () => {
            expect(VictoryUtils.formatDate('10')).toBe('10');
            expect(VictoryUtils.formatDate('102')).toBe('10/2');
            expect(VictoryUtils.formatDate('1025')).toBe('10/25');
        });

        test('formatNumber strips non-digits', () => {
            expect(VictoryUtils.formatNumber(1000)).toBe('1000'); // No commas added by current util
            expect(VictoryUtils.formatNumber('1,000')).toBe('1000');
            expect(VictoryUtils.formatNumber('abc123xyz')).toBe('123');
        });
    });

    describe('Data Fetching', () => {
        test('fetchReferenceData returns cached data if valid', async () => {
            const cachedData = {
                timestamp: Date.now(),
                data: { classes: ['A'], teams: ['B'] }
            };
            localStorage.setItem('victory_reference_data', JSON.stringify(cachedData));

            const data = await VictoryUtils.fetchReferenceData();
            expect(data).toEqual(cachedData.data);
            expect(fetch).not.toHaveBeenCalled();
        });

        test('fetchReferenceData fetches from API if cache expired or missing', async () => {
            const apiData = { result: 'success', data: { classes: ['C'], teams: ['D'] } };

            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => apiData
            });

            const data = await VictoryUtils.fetchReferenceData();
            expect(data).toEqual(apiData.data);
            expect(fetch).toHaveBeenCalledTimes(1);
        });

        test('fetchReferenceData returns null if API fails', async () => {
            global.fetch.mockRejectedValueOnce(new Error('API Error'));

            const data = await VictoryUtils.fetchReferenceData();
            expect(data).toBeNull();
        });
    });
});
