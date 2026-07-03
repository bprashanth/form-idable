# Deployment & Environment Variables

## How API routing works

API calls in the PWA go through `useApi.js`, which builds the URL as:

```js
const baseUrl = import.meta.env.VUE_APP_API_BASE_URL || ''
fetch(`${baseUrl}/api/upload`, ...)
```

The `|| ''` fallback means: if `VUE_APP_API_BASE_URL` is not set, calls use a relative
path (`/api/upload`), which Vite's dev proxy intercepts and forwards to `localhost:8070`.

This gives three tiers of behaviour with a single variable:

| Scenario | `VUE_APP_API_BASE_URL` set? | Where requests go |
|---|---|---|
| `npm run dev`, no `.env.local` var | No | Vite proxy - `localhost:8070` |
| `npm run dev`, var in `.env.local` | Yes | Directly to that URL |
| Netlify prod build | Yes (Netlify env var) | Directly to prod API |

## Local development (default)

No configuration needed. The Vite proxy in `vite.config.js` forwards `/api/*` to
`localhost:8070`:

```js
proxy: {
  '/api': {
    target: process.env.API_TARGET || 'http://localhost:8070',
    changeOrigin: true,
  }
}
```

Start the server, then start the PWA:

```bash
# Terminal 1 — API server
cd good-shepherd/server && uvicorn main:app --port 8070 --host 0.0.0.0

# Terminal 2 — PWA dev server
cd pwa && npm run dev
# -> http://localhost:5173 (or 5174 if port is taken)
```

## Pointing dev at a different server

To override the proxy and hit a different server (e.g. the prod API) during local dev,
add to `pwa/.env.local`:

```
VUE_APP_API_BASE_URL=https://your-prod-api.execute-api.ap-south-1.amazonaws.com/prod
```

`.env.local` is gitignored.

To revert to localhost, remove the line (or delete `.env.local`).

You can also override just the proxy target without touching env vars directly via cmd line:

```bash
$ API_TARGET=http://localhost:9000 npm run dev
```

**Precedence:** if `VUE_APP_API_BASE_URL` is set in `.env.local`, it takes full precedence -
`useApi.js` calls that URL directly and the Vite proxy (including `API_TARGET`) is never
reached. `API_TARGET` only matters when `VUE_APP_API_BASE_URL` is absent.

## Production (Netlify)

1. Netlify deployment is controlled via `netlify.toml`. The project is already configured in the netlify dashboard. 
2. To set/modify environment variables, go to **Project -> Site configuration -> Environment variables**:

| Variable | Value |
|---|---|
| `VUE_APP_API_BASE_URL` | `https://your-prod-api.execute-api.ap-south-1.amazonaws.com/prod` |
| `VITE_GOOGLE_CLIENT_ID` | (from `.env.local`) |
| `VITE_GOOGLE_API_KEY` | (from `.env.local`) |

`netlify.toml` includes a catch-all redirect (`/* -> /index.html 200`) so that
refreshing or deep-linking to any route (e.g. `/crop`, `/result`) works correctly.

