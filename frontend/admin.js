// Admin form logic for searching and updating member details
function adminForm() {
    return {
        isDarkMode: false,
        searchQuery: '',
        searching: false,
        searched: false,
        searchResults: [],
        searchError: '',
        selectedMember: null,
        submitting: false,
        status: { message: '', type: '' },

        // Helper to parse comma-separated strings or arrays into arrays
        parseListField(value) {
            if (Array.isArray(value)) {
                return value;
            }
            if (typeof value === 'string' && value.trim()) {
                return value.split(',').map(s => s.trim()).filter(s => s);
            }
            return [];
        },

        form: {
            firstName: '',
            middleName: '',
            lastName: '',
            suffix: '',
            email: '',
            fbName: '',
            primaryMobile: '',
            secondaryMobile: '',
            gender: '',
            birthday: '',
            maritalStatus: '',
            anniversary: '',
            // Occupation fields
            occupationType: '',
            educationLevel: '',
            school: '',
            yearLevel: '',
            course: '',
            jobTitle: '',
            company: '',
            employerIndustry: '',
            businessName: '',
            businessNature: '',
            businessAddress: '',
            // Discipleship (array for checkboxes)
            discipleshipList: [],
            // VG fields
            isMemberToggle: false,
            leaderName: '',
            wantVgToggle: false,
            isLeaderToggle: false,
            groupCount: '',
            vgDetails: '',
            hasInternToggle: false,
            internNames: '',
            // Ministry fields (arrays for checkboxes)
            isMinistryMemberToggle: false,
            ministryList: [],
            wantMinistryList: []
        },

        // Reference lists for validation (populated from API)
        lists: {
            discipleshipClasses: [], // Populated from API
            ministryOptions: []      // Populated from API
        },

        async init() {
            // Load dark mode preference
            const savedTheme = localStorage.getItem('darkMode');
            if (savedTheme !== null) {
                this.isDarkMode = JSON.parse(savedTheme);
            } else {
                this.isDarkMode = false;
            }

            this.$watch('darkMode', val => {
                localStorage.setItem('darkMode', JSON.stringify(val));
            });

            // Load reference data from API
            await this.loadReferenceData();
        },

        async loadReferenceData() {
            const data = await VictoryUtils.fetchReferenceData();
            if (data) {
                this.applyReferenceData(data);
            } else {
                this.useFallbackData();
            }
        },

        applyReferenceData(data) {
            if (data.discipleship_classes) {
                this.lists.discipleshipClasses = data.discipleship_classes;
            }
            if (data.ministry_teams) {
                this.lists.ministryOptions = data.ministry_teams;
            }
        },

        useFallbackData() {
            // Use shared fallback data
            const fallbacks = VictoryUtils.getFallbackLists();
            this.lists.discipleshipClasses = fallbacks.discipleshipClasses;
            this.lists.ministryOptions = fallbacks.ministryOptions;
        },

        async searchMembers() {
            if (!this.searchQuery.trim()) return;

            this.searching = true;
            this.searchError = '';
            this.searchResults = [];
            this.searched = false;

            const API_ENDPOINT = 'https://member-api-132324496795.asia-southeast1.run.app/api/search';

            try {
                const response = await fetch(`${API_ENDPOINT}?query=${encodeURIComponent(this.searchQuery.trim())}`);
                const data = await response.json();

                if (response.ok && data.result === 'success') {
                    this.searchResults = data.members || [];
                    this.searched = true;
                } else {
                    this.searchError = data.message || 'An error occurred while searching.';
                }
            } catch (error) {
                this.searchError = 'Network error: ' + error.message;
            } finally {
                this.searching = false;
            }
        },

        selectMember(member) {
            this.selectedMember = member;

            // Strip "09" prefix if present
            const primaryMobile = member.mobile_number?.startsWith('09')
                ? member.mobile_number.substring(2)
                : member.mobile_number || '';
            const secondaryMobile = member.sec_mobile_number?.startsWith('09')
                ? member.sec_mobile_number.substring(2)
                : member.sec_mobile_number || '';

            // Populate form with member data
            this.form = {
                // Personal details
                firstName: member.first_name || '',
                middleName: member.middle_name || '',
                lastName: member.last_name || '',
                suffix: member.suffix || '',
                email: member.email || '',
                fbName: member.fb_name || '',
                primaryMobile: primaryMobile,
                secondaryMobile: secondaryMobile,
                gender: member.gender || '',
                birthday: member.birthday || '',
                maritalStatus: member.marital_status || '',
                anniversary: member.anniversary || '',
                // Occupation fields
                occupationType: member.occupation_type || '',
                educationLevel: member.education_level || '',
                school: member.school || '',
                yearLevel: member.year_level || '',
                course: member.course || '',
                jobTitle: member.job_title || '',
                company: member.company || '',
                employerIndustry: member.employer_industry || '',
                businessName: member.business_name || '',
                businessNature: member.business_nature || '',
                businessAddress: member.business_address || '',
                // Discipleship (parse comma-separated to array)
                discipleshipList: this.parseListField(member.discipleship_classes),
                // VG fields
                isMemberToggle: member.is_vg_member || false,
                leaderName: member.vg_leader_name || '',
                wantVgToggle: member.want_vg === 'Yes',
                isLeaderToggle: member.is_vg_leader || false,
                groupCount: member.vg_count || '',
                vgDetails: member.vg_details || '',
                hasInternToggle: member.has_intern || false,
                internNames: member.intern_names || '',
                // Ministry fields (parse comma-separated to arrays)
                isMinistryMemberToggle: member.is_ministry_member || false,
                ministryList: this.parseListField(member.ministry_teams),
                wantMinistryList: this.parseListField(member.want_ministry)
            };

            // Reset status
            this.status = { message: '', type: '' };
        },

        cancelEdit() {
            this.selectedMember = null;
            this.form = {
                firstName: '',
                middleName: '',
                lastName: '',
                suffix: '',
                email: '',
                fbName: '',
                primaryMobile: '',
                secondaryMobile: '',
                gender: '',
                birthday: '',
                maritalStatus: '',
                anniversary: '',
                occupationType: '',
                educationLevel: '',
                school: '',
                yearLevel: '',
                course: '',
                jobTitle: '',
                company: '',
                employerIndustry: '',
                businessName: '',
                businessNature: '',
                businessAddress: '',
                discipleshipList: [],
                isMemberToggle: false,
                leaderName: '',
                wantVgToggle: false,
                isLeaderToggle: false,
                groupCount: '',
                vgDetails: '',
                hasInternToggle: false,
                internNames: '',
                isMinistryMemberToggle: false,
                ministryList: [],
                wantMinistryList: []
            };
            this.status = { message: '', type: '' };
        },

        async submitUpdate(e) {
            // Basic validation
            if (!e.target.checkValidity()) {
                e.target.classList.add('was-validated');
                this.status = { message: 'Please fill in all required fields correctly', type: 'error' };
                return;
            }

            this.submitting = true;
            this.status = { message: '', type: '' };

            // Build payload matching the existing /api/submit format
            // This is a simplified version - only personal details
            const payload = {
                firstName: this.form.firstName,
                middleName: this.form.middleName,
                lastName: this.form.lastName,
                suffix: this.form.suffix,
                email: this.form.email,
                fbName: this.form.fbName,
                primaryMobile: '09' + this.form.primaryMobile,
                secondaryMobile: this.form.secondaryMobile ? '09' + this.form.secondaryMobile : '',
                gender: this.form.gender,
                birthday: this.form.birthday,
                maritalStatus: this.form.maritalStatus,
                anniversary: this.form.anniversary,

                // Include existing data for other fields to maintain completeness
                occupationType: this.selectedMember.occupation_type || '',
                educationLevel: this.selectedMember.education_level || '',
                school: this.selectedMember.school || '',
                yearLevel: this.selectedMember.year_level || '',
                course: this.selectedMember.course || '',
                jobTitle: this.selectedMember.job_title || '',
                company: this.selectedMember.company || '',
                employerIndustry: this.selectedMember.employer_industry || '',
                businessName: this.form.businessName,
                businessNature: this.form.businessNature,
                businessAddress: this.form.businessAddress,
                discipleship: this.form.discipleshipList.join(', '),
                isMember: this.form.isMemberToggle ? 'Yes' : 'No',
                leaderName: this.form.leaderName,
                wantVg: this.form.wantVgToggle ? 'Yes' : 'No',
                isLeader: this.form.isLeaderToggle ? 'Yes' : 'No',
                groupCount: this.form.groupCount,
                vgDetails: this.form.vgDetails,
                hasIntern: this.form.hasInternToggle ? 'Yes' : 'No',
                internNames: this.form.internNames,
                isMinistryMember: this.form.isMinistryMemberToggle ? 'Yes' : 'No',
                ministry: this.form.ministryList.join(', '),
                wantMinistry: this.form.wantMinistryList.join(', ')
            };

            const API_ENDPOINT = 'https://member-api-132324496795.asia-southeast1.run.app/api/submit';

            try {
                const response = await fetch(API_ENDPOINT, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (data.result === 'success') {
                    this.submitting = false;
                    this.status = {
                        message: 'Profile updated successfully! Note: Changes will be visible in search after the data pipeline runs.',
                        type: 'success'
                    };
                    e.target.classList.remove('was-validated');

                    // Wait a moment then return to search
                    setTimeout(() => {
                        this.cancelEdit();
                        this.searchResults = [];
                        this.searchQuery = '';
                        this.searched = false;
                    }, 3000);
                } else {
                    throw new Error(data.error || 'Unknown error');
                }
            } catch (error) {
                this.submitting = false;
                this.status = { message: 'Error: ' + error.message, type: 'error' };
            }
        }
    };
}
