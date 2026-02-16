# Manual Verification Plan - Phase 5

## Objective
Verify that `index.html` and `admin.html` function correctly after refactoring validation, formatting, and data loading logic to `utils.js`.

## Checklist

### 1. Index.html (Member Form)
- [ ] **Load:** Open page, check console for "Fetching reference data..." or "Using cached reference data".
- [ ] **Validation:**
  - Enter invalid email (e.g., "test") -> Expect error.
  - Enter valid email -> Expect success.
  - Enter invalid date -> Expect error.
  - Enter valid date -> Expect success.
- [ ] **Formatting:**
  - Type phone number -> Expect "09" prefix handling (if logic kept) or just formatting.
  - *Note:* Our refactor in `index.html` calls `VictoryUtils.formatPhone` which strips non-digits and slices to 9 chars.
- [ ] **Submission:** Submit form -> Expect success (mock response).

### 2. Admin.html (Admin Console)
- [ ] **Load:** Open page, check console.
- [ ] **Search:** Enter query -> Expect results.
- [ ] **Edit:** Select member -> Verify data population.
- [ ] **Update:** Save changes -> Expect success.

## Browser Test Command
We will use `browser_subagent` to open the files and perform these checks.
