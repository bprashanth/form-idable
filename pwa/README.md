# Scribe frontend

See [../docs/pwa.md](../docs/pwa.md) for more details.

```console
# This sources the apiserver addresses via `vite.config` and `.env.local` on locahost
$ npm run dev
```

## Server discovery

There are two backend servers. How the PWA reaches them depends on whether it's
running in dev or production.

### `/api/*` — good-shepherd (Textract upload + sessions)

Handled by `useApi.js`, which prepends `import.meta.env.VUE_APP_API_BASE_URL` to
every fetch path.

| Context | `VUE_APP_API_BASE_URL` | Result |
|---------|------------------------|--------|
| `npm run dev` (default) | unset → `""` | fetch stays relative → Vite proxies `/api/*` to `http://localhost:8070` |
| `npm run dev` + `API_TARGET=...` in `.env.local` | unset | Vite proxy target overridden to the value of `API_TARGET` |
| `npm run dev` + `VUE_APP_API_BASE_URL=...` in `.env.local` | set → absolute URL | `useApi.js` uses the absolute URL directly; Vite proxy is bypassed |
| Netlify prod build | set in Netlify console → API Gateway URL | baked into the JS bundle; requests go directly to the API Gateway URL |

There is no `netlify.toml` redirect for `/api/*` — in production the URL is fully
qualified before the browser even sends the request.

### `/agent/*` — form-idable-agent (species checks, serial checks)

Agent calls in `ResultView.vue` use plain relative paths (`/agent/...`) with a bare
`fetch()`, never prefixed by `useApi.js`.

| Context | Result |
|---------|--------|
| `npm run dev` (default) | Vite proxies `/agent/*` to `http://localhost:8071` |
| `npm run dev` + `AGENT_TARGET=...` in `.env.local` | Vite proxy target overridden to the Lambda URL |
| Netlify prod build | `netlify.toml` redirects `/agent/*` to the Lambda Function URL |

The Lambda Function URL in `netlify.toml` must be updated whenever the agent server is
redeployed (the URL is stable across deploys, but changes if the function is torn down
and recreated).

### Quick reference: switching targets in dev

```bash
# .env.local — uncomment one or both lines to point at production servers
# API_TARGET=https://<good shepherd lambda>.ap-south-1.amazonaws.com/prod
# AGENT_TARGET=https://<formidable agent lambda>.ap-south-1.on.aws
```
