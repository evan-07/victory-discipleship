# V2 Architecture Frontend Design Spec
**Status:** Planning (Not Implemented)

## Overview
The frontend for Phase 1 will be a static web application hosted on **Cloudflare Pages**. It will utilize standard web technologies (HTML/CSS/JS) enhanced by **Bootstrap 5** for UI and **Alpine.js** for reactive data binding.

## Project Structure
```plaintext
frontend/
├── index.html           # Landing page / routing point
├── admin.html           # Admin Portal (Protected by Cloudflare Access)
├── leader.html          # VG Leader Form
└── js/
    ├── app.js           # Core Alpine.js logic
    └── auth.js          # Firebase Auth logic
```

## Key Technologies
- **Cloudflare Pages**: Provides lightning-fast edge hosting with a built-in Github Actions integration.
- **Bootstrap 5**: Ensures mobile responsiveness and clean grid architecture.
- **Alpine.js**: Provides Vue/React-like reactivity without the build step or heavy bundle.
- **Firebase Auth (Client SDK)**: Handles Google Sign-In.

## Component: VG Leader Form (`leader.html`)
- **State Management**: Alpine.js `x-data` component will map the JSON schema defined in `architecture_test.md` (e.g. `first_name`, `address`... and an array for `victory_groups`).
- **Auth Flow**: The page will check the Firebase Auth state. If authenticated, it will retrieve a JWT and make a `GET /api/me` call to the Cloud Run backend to pre-fill the form with existing Silver layer data.
- **Submission**: On submit, the Alpine component will serialize the data and `POST /api/submit` using `fetch()`, authenticated by the Firebase JWT token.

## Component: Admin Portal (`admin.html`)
- This page is gatekept by **Cloudflare Access** policies (enforced via edge networking).
- Inside the portal, an admin interface will list the `pending` submissions and allow the admin to take action on merging or approving profiles.

## Mobile Responsiveness Strategy
- Implementation must follow a mobile-first philosophy using Bootstrap `col-12 col-md-6` structures.
- Forms should utilize standard HTML5 input types (`tel`, `email`, `date`) to invoke native mobile keyboards.
