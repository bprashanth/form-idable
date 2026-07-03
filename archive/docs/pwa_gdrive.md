# Google Drive Integration Setup

The PWA has a "Save to Google Drive" button on the result screen. This requires a Google Cloud Platform (GCP) project with the right APIs, credentials, and test users configured.

## GCP Project Setup

### 1. Enable APIs

In the GCP console under **APIs & Services → Library**, enable:
- **Google Drive API**
- **Google Picker API**

### 2. OAuth Consent Screen

Under **APIs & Services → OAuth consent screen**:
- Publishing status: **Testing** (until you go through Google verification)
- App name: `scribe`
- Scope: `https://www.googleapis.com/auth/drive.file`

#### Adding Test Users

While the app is in "Testing" publishing status, only explicitly listed test users can authenticate. Under **OAuth consent screen → Audience**, add each user's email individually. Without this, users will see a "This app is blocked" error when trying to sign in.

### 3. OAuth 2.0 Client ID

Under **APIs & Services → Credentials**, create an OAuth 2.0 Client ID (Web application):

- **Authorized JavaScript origins**:
  - `http://localhost:5173` (local dev)
  - `http://localhost:5174` (alternate vite port)
  - `https://yoursite.netlify.app` (production)

- **Authorized redirect URIs**:
  - `http://localhost:5173` (local dev)
  - `https://yoursite.netlify.app` (production)

### 4. API Key

Under **APIs & Services → Credentials**, create an API key:

- **Application restrictions**: HTTP referrers (web sites)
- **Website restrictions** — add each allowed origin:
  - `http://localhost:5173`
  - `http://localhost:5174`
  - `https://yoursite.netlify.app`
- **API restrictions**: Restrict to **Google Picker API** and **Google Drive API**

## Environment Variables

The PWA reads two variables at build time:

```
VITE_GOOGLE_CLIENT_ID=<your-oauth-client-id>
VITE_GOOGLE_API_KEY=<your-api-key>
```

### Local Development

Create `pwa/.env.local` with the values above. This file is gitignored.

### Netlify Deployment

Add `VITE_GOOGLE_CLIENT_ID` and `VITE_GOOGLE_API_KEY` in **Site settings → Environment variables** in the Netlify dashboard. Without these, the "Save to Google Drive" button will fail silently since the auth and picker APIs won't have valid credentials.
