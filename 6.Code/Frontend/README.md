# SmartWatch Manager — Frontend

Industrial-HMI-styled dashboard for the SmartWatch Manager telemetry pipeline.

## Setup

```
npm install
npm run dev
```

Runs on `http://localhost:5173` by default. Requires the FastAPI backend
running on `http://localhost:8000` (see `src/lib/AuthContext.jsx` -> `API_BASE`
if yours runs elsewhere).

**CORS note:** `main.py`'s CORS middleware is currently `allow_origins=["*"]`,
so this will work as-is against your dev API. Tighten that before any real
deployment, per the TODO already in that file.

## Architecture

- `src/lib/usePolling.js` - the ONLY place that knows data is fetched via
  polling rather than pushed. Every data hook is built on this. If you later
  add WebSocket support, this is the one file that changes - components stay
  the same.
- `src/lib/useTelemetry.js` - domain-specific hooks (`useMachines`,
  `useCurrentSummary`, `useVibrationSummary`) built on `usePolling`.
  Components should use these, not `usePolling` directly.
- `src/lib/AuthContext.jsx` - JWT storage (sessionStorage) and login/logout.
- `src/theme.css` - design tokens (color, type, spacing). Change the look
  of the whole app from this one file.
- `src/components/` - one component per concern: `TopBar`, `MachineStrip`
  (the machine-status annunciator strip), `MachineDetail` (the per-channel
  gauge grid), `GaugeCard` (single-channel sparkline + readout), `LoginScreen`.

## Design direction

Industrial HMI aesthetic - steel-gray chrome, safety-yellow accent reserved
for selection/active states only, monospace for every numeric telemetry
readout. The machine-status strip (`MachineStrip.jsx`) is styled after a
physical indicator-light / annunciator panel rather than a generic card list
- this is the app's one deliberate visual signature; keep the rest quiet
around it.

## Known limitations (by design, for the prototype)

- Polling every 3s per machine, not WebSocket push - see `usePolling.js` for
  why this is the right call for a first pass.
- JWT lives in `sessionStorage`, cleared on tab close - fine for a prototype
  demo, not a production auth strategy.
- No route-based navigation yet - single view, machine selection via local
  state. Add React Router if the app grows more screens.
