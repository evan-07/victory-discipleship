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
            anniversary: ''
        },

        init() {
            // Load dark mode preference
            const savedTheme = localStorage.getItem('darkMode');
            if (savedTheme !== null) {
                this.isDarkMode = JSON.parse(savedTheme);
            } else {
                this.isDarkMode = false;
            }

            this.$watch('isDarkMode', val => {
                localStorage.setItem('darkMode', JSON.stringify(val));
            });
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
                anniversary: member.anniversary || ''
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
                anniversary: ''
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
                businessName: this.selectedMember.business_name || '',
                businessNature: this.selectedMember.business_nature || '',
                businessAddress: this.selectedMember.business_address || '',
                discipleship: this.selectedMember.discipleship_classes || '',
                isMember: this.selectedMember.is_vg_member ? 'Yes' : 'No',
                leaderName: this.selectedMember.vg_leader_name || '',
                wantVg: this.selectedMember.want_vg || '',
                isLeader: this.selectedMember.is_vg_leader ? 'Yes' : 'No',
                groupCount: this.selectedMember.vg_count || '',
                vgDetails: this.selectedMember.vg_details || '',
                hasIntern: this.selectedMember.has_intern ? 'Yes' : 'No',
                internNames: this.selectedMember.intern_names || '',
                isMinistryMember: this.selectedMember.is_ministry_member ? 'Yes' : 'No',
                ministry: Array.isArray(this.selectedMember.ministry_teams)
                    ? this.selectedMember.ministry_teams.join(', ')
                    : '',
                wantMinistry: Array.isArray(this.selectedMember.want_ministry)
                    ? this.selectedMember.want_ministry.join(', ')
                    : ''
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
