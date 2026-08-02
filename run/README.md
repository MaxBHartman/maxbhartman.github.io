# Training log — live from Strava

`/run` fetches your Strava data on every page view via a small Cloudflare
Worker (`../worker/`), rather than reading a committed data file. There's no
`data.js` generated or checked in — the dashboard calls `GET /api/strava` and
renders whatever comes back.

```
run/index.html      dashboard — fetches /api/strava, renders charts/tables
run/fetch_strava.py one-time local bootstrap (see below), nothing else
worker/              Cloudflare Worker: proxies Strava, holds the OAuth
                     secret, does daily geo/weather enrichment
```

## Why a Worker

Refreshing a Strava OAuth token requires the app's **client secret**, which
can never be shipped in client-side JS on a public site — anyone viewing page
source could extract it and pull your activity history directly. The Worker
holds that secret server-side; the page only ever talks to `/api/strava`.

## One-time setup

1. Create a Strava API application at
   [strava.com/settings/api](https://www.strava.com/settings/api):
   - **Website:** `http://localhost`
   - **Authorization Callback Domain:** `localhost` (exact value matters)
2. `pip install -r requirements.txt`
3. Run the OAuth login once, locally, to obtain a refresh token:
   ```
   export STRAVA_CLIENT_ID=your_client_id
   export STRAVA_CLIENT_SECRET=your_client_secret
   python3 fetch_strava.py
   ```
   It prints an authorize URL — open it, click Authorize, then copy the
   `code=` value from the (expected-to-fail) `localhost` redirect and paste
   it back into the terminal. This writes `strava_tokens.json` locally —
   open it and copy the `refresh_token` value.
4. Seed that refresh token into the Worker and deploy it — see
   `../worker/wrangler.toml` and the deploy checklist for exact commands.

After this one-time step, `fetch_strava.py` isn't part of the ongoing
pipeline — the Worker refreshes its own access token automatically from then
on. (`--demo` still works if you just want to preview the dashboard's look
with synthetic data by pointing `index.html` at a local `data.js` again.)

## Privacy

The Worker returns the same slimmed/aggregated shape this page renders
(distance, pace, elevation, approximate start coordinates, etc. — not raw GPS
tracks). Geography and Weather are resolved once per activity by a daily cron
in the Worker and cached there permanently, since historical weather/location
for a past activity never changes; both sections stay hidden until the first
cron run has enriched something.

## Credits

Concept and design inspired by **nodaysoff.run** by Adrien Friggeri. Fonts:
Jost, Space Mono.
