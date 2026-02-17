const adminForm = require('../admin.js');

// Mock global objects
global.fetch = jest.fn();
global.localStorage = {
    getItem: jest.fn(),
    setItem: jest.fn()
};

// Mock VictoryUtils since admin.js relies on it
global.VictoryUtils = {
    fetchReferenceData: jest.fn(),
    getFallbackLists: jest.fn().mockReturnValue({
        discipleshipClasses: ['Class A'],
        ministryOptions: ['Ministry B']
    })
};

describe('Admin Form', () => {
    let component;

    beforeEach(() => {
        jest.clearAllMocks();
        component = adminForm();
        component.$watch = jest.fn(); // Mock Alpine.js $watch
        component.init();
    });

    describe('Initialization', () => {
        test('loads reference data on init', async () => {
            await component.init();
            expect(VictoryUtils.fetchReferenceData).toHaveBeenCalled();
        });

        test('uses fallback data if API fails', async () => {
            VictoryUtils.fetchReferenceData.mockResolvedValue(null);
            await component.init();
            expect(VictoryUtils.getFallbackLists).toHaveBeenCalled();
            expect(component.lists.discipleshipClasses).toEqual(['Class A']);
        });
    });

    describe('Search', () => {
        test('does nothing if query is empty', async () => {
            component.searchQuery = '  ';
            await component.searchMembers();
            expect(fetch).not.toHaveBeenCalled();
        });

        test('fetches members on valid query', async () => {
            component.searchQuery = 'doe';
            global.fetch.mockResolvedValueOnce({
                ok: true,
                json: async () => ({ result: 'success', members: [{ email: 'doe@example.com' }] })
            });

            await component.searchMembers();

            expect(fetch).toHaveBeenCalledWith(expect.stringContaining('doe'));
            expect(component.searchResults).toHaveLength(1);
            expect(component.searchResults[0].email).toBe('doe@example.com');
            expect(component.searched).toBe(true);
        });

        test('handles API error gracefully', async () => {
            component.searchQuery = 'error';
            global.fetch.mockResolvedValueOnce({
                ok: false,
                json: async () => ({ message: 'API Error' })
            });

            await component.searchMembers();

            expect(component.searchError).toBe('API Error');
            expect(component.searchResults).toEqual([]);
        });
    });

    describe('Member Selection', () => {
        const mockMember = {
            first_name: 'John',
            last_name: 'Doe',
            mobile_number: '09171234567',
            discipleship_classes: 'One2One, Victory Weekend',
            is_vg_member: true
        };

        test('populates form with member data', () => {
            component.selectMember(mockMember);

            expect(component.form.firstName).toBe('John');
            expect(component.form.primaryMobile).toBe('171234567'); // Strips 09
            expect(component.form.discipleshipList).toEqual(['One2One', 'Victory Weekend']);
            expect(component.form.isMemberToggle).toBe(true);
        });

        test('handles null fields gracefully', () => {
            component.selectMember({ first_name: 'Jane' });
            expect(component.form.firstName).toBe('Jane');
            expect(component.form.discipleshipList).toEqual([]);
        });
    });

    describe('Update Submission', () => {
        let mockEvent;

        beforeEach(() => {
            component.selectMember({ email: 'test@example.com', first_name: 'Test' });

            mockEvent = {
                target: {
                    checkValidity: jest.fn().mockReturnValue(true),
                    classList: { add: jest.fn(), remove: jest.fn() }
                }
            };
        });

        test('submits valid form data', async () => {
            global.fetch.mockResolvedValueOnce({
                json: async () => ({ result: 'success' })
            });

            await component.submitUpdate(mockEvent);

            expect(fetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/submit'),
                expect.objectContaining({
                    method: 'POST',
                    body: expect.stringContaining('"email":"test@example.com"')
                })
            );
            expect(component.status.type).toBe('success');
        });

        test('validates form before submission', async () => {
            mockEvent.target.checkValidity.mockReturnValue(false);

            await component.submitUpdate(mockEvent);

            expect(fetch).not.toHaveBeenCalled();
            expect(component.status.type).toBe('error');
        });

        test('handles submission error', async () => {
            global.fetch.mockResolvedValueOnce({
                json: async () => ({ result: 'error', error: 'Database fail' })
            });

            await component.submitUpdate(mockEvent);

            expect(component.status.message).toContain('Database fail');
            expect(component.status.type).toBe('error');
        });
    });
});
