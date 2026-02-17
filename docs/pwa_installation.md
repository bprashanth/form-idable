# PWA Installation & Standalone Mode

## How "Install App" works on Android

When Chrome visits a page that meets the **PWA installability criteria**, it shows
an "Install app" banner (or the option appears in the browser menu). Once
installed, the app launches in its own window — no address bar, no tabs.

### Installability criteria (Chrome on Android)

| Requirement | How we satisfy it |
|---|---|
| Served over HTTPS (or localhost) | Dev server on `localhost`; production behind HTTPS |
| A **web app manifest** with `name`, `start_url`, `display: standalone`, and at least a 192x192 PNG icon | `public/manifest.json` |
| A **registered service worker** with a `fetch` event handler | `vite-plugin-pwa` auto-generates one via Workbox |

All three are required. Without the service worker, Chrome treats "Add to Home
Screen" as a simple bookmark shortcut — it still opens inside Chrome with the
address bar visible.

## Manifest — `pwa/public/manifest.json`

```json
{
  "name": "scribe",
  "short_name": "scribe",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#111827",
  "theme_color": "#111827",
  "icons": [
    { "src": "/web-app-manifest-192x192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable" },
    { "src": "/web-app-manifest-512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

- **192x192** — standard home-screen icon.
- **512x512** — used for the splash screen shown while the app loads.
- **`purpose: maskable`** — tells the OS the icon has safe-zone padding so it can
  be clipped to circles, rounded squares, etc. without cutting off the logo.
  Icons were generated via [realfavicongenerator.net](https://realfavicongenerator.net/)
  from the source `icon.jpg`.

## Service Worker — `vite-plugin-pwa`

Configured in `vite.config.js`:

```js
VitePWA({
  registerType: 'autoUpdate',
  manifest: false,       // we provide our own public/manifest.json
  workbox: {
    globPatterns: ['**/*.{js,css,html,ico,png,svg,jpg,woff2}'],
  },
})
```

- **`registerType: 'autoUpdate'`** — when a new build is deployed, the service
  worker updates itself automatically without prompting the user.
- **`manifest: false`** — tells the plugin not to generate a manifest; we manage
  our own in `public/manifest.json`.
- **Workbox `globPatterns`** — precaches all static assets so the app shell loads
  instantly on repeat visits (and works offline for the cached pages).

Registration happens in `src/main.js`:

```js
import { registerSW } from 'virtual:pwa-register'
registerSW({ immediate: true })
```

This registers the generated service worker as soon as the app loads.

## What the service worker actually does

The service worker sits between the app and the network. On first load it caches
all static assets (JS bundles, CSS, HTML, images). On subsequent loads it serves
from cache first, then checks for updates in the background. This is what makes
Chrome treat the app as "installable" — it proves the app can handle being
offline or on a flaky connection.

Without a service worker, tapping the home-screen icon just opens Chrome with a
bookmark. With one, Android launches a standalone window (no browser chrome).

## Touch behavior

In `src/main.css`:

```css
body {
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
}
```

- **`touch-action: manipulation`** — disables double-tap-to-zoom so taps feel
  instant (like a native app). Pinch-to-zoom is preserved.
- **`-webkit-tap-highlight-color: transparent`** — removes the blue/grey
  highlight flash that appears when tapping links and buttons on mobile WebKit.

## Testing the install flow

Chrome requires **HTTPS or `localhost`** to register a service worker. A plain
LAN IP like `http://192.168.x.x:5174` won't work — Chrome will silently refuse
to register the SW and you'll only see "Add to Home Screen" (a bookmark), not
"Install app" (a real PWA install).

### Option A: Chrome port forwarding (recommended for dev)

1. Connect phone to laptop via USB, enable USB debugging on the phone.
2. On laptop, open `chrome://inspect/#devices` in Chrome.
3. Click **Port forwarding**, add `5174` → `localhost:5174`.
4. On phone, navigate to `http://localhost:5174`.
5. Chrome sees `localhost` → service worker registers → "Install app" appears.

If this doesn't work, try (on the laptop) 
```
$ adb devices
```
And accepting / unlocking permissions for usb. 
Also ensure usb file transfer is turned on (vs usb charging). 

### Option B: Production build behind HTTPS

```bash
cd pwa && npm run build && npx serve dist
```

Then serve behind an HTTPS reverse proxy (nginx, Caddy, Cloudflare tunnel, etc.).

### Install steps

1. Open the app URL in Chrome on your phone.
2. In Chrome menu, look for **"Install app"** (not just "Add to Home Screen").
   - If you only see "Add to Home Screen", the service worker hasn't registered.
     Check the URL is `localhost` or HTTPS, reload and wait a moment.
3. After installing, close Chrome and tap the "scribe" icon on your home screen.
4. The app should open in its own window — no address bar, no tabs.

### Clearing a stale install

If you previously added the site to your home screen (before the service worker
existed), that shortcut is just a bookmark. Delete it from the home screen, clear
Chrome's site data for the URL, then revisit and use "Install app".

## Viewport height

The root layout in `App.vue` uses `h-dvh` (dynamic viewport height) instead of
`h-screen` (`100vh`). On mobile, `100vh` includes the space behind the browser
address bar, causing content to overflow. `dvh` adjusts as the browser chrome
shows/hides, keeping buttons like "Crop & Send" always visible.
