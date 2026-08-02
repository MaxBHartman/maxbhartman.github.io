# Your Strava training log

A personal stats site in the spirit of [nodaysoff.run](https://nodaysoff.run/),
built from **your own** Strava data. It covers every activity type — runs, rides,
swims, hikes — with totals, notable efforts, a wall of charts, geography, and a
day-by-day calendar.

Two pieces:

| File | What it does |
|------|--------------|
| `fetch_strava.py` | Logs into Strava (your data only), downloads your full history, writes `data.js` |
| `index.html` | The dashboard. Open it in a browser; it reads `data.js` |

You can preview it right now with the included demo data — just open `index.html`.
When you're ready for your real numbers, follow the steps below.

---

## Step 1 — Create a Strava API application (2 minutes, free)

1. Go to **https://www.strava.com/settings/api** (log in if needed).
2. Fill in the form:
   - **Application Name:** anything, e.g. `My Training Log`
   - **Category:** `Data Importer` is fine
   - **Website:** `http://localhost`
   - **Authorization Callback Domain:** `localhost`  ← this exact value matters
3. Click **Create**. You'll now see your **Client ID** and **Client Secret**.

Your app starts in "single player mode," which is exactly right — it can only ever
read your own account.

## Step 2 — Give the script your credentials

Create a file named `.env` in this folder (same place as `fetch_strava.py`):

```
STRAVA_CLIENT_ID=your_client_id_here
STRAVA_CLIENT_SECRET=your_client_secret_here
```

(Or `export` those two variables in your shell — either works.)

## Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

`requests` is required. `reverse_geocoder` + `pycountry` are optional and only power
the Geography section; skip them if you don't want maps.

## Step 4 — Download your data

```bash
python fetch_strava.py
```

The first run prints a Strava authorization URL. Open it, click **Authorize**, and
your browser will jump to a `http://localhost/...` page that **fails to load — that's
expected**. Copy the `code=` value from that page's address bar and paste it back into
the terminal. The script saves a token so you won't have to do this again; future runs
just refresh automatically.

It then pages through your whole history (about 15 requests per few-thousand activities,
well under Strava's limits) and writes `data.js`.

## Step 5 — Open the dashboard

Just double-click `index.html`, or open it in any browser. Because `data.js` is a plain
script (not a `fetch`), it works straight from `file://` with no local server needed.

> The charts use D3 and the maps use public boundary files, both loaded from a CDN, so
> the page needs an internet connection the first time you open it.

---

## Options & extras

**Add weather** (temperature + conditions charts). Strava doesn't store weather, so this
looks up historical weather for each activity's time and place via the free
[Open-Meteo](https://open-meteo.com/) archive (no key needed). It's slower:

```bash
python fetch_strava.py --weather
```

**Test quickly** with just your most recent activities:

```bash
python fetch_strava.py --limit 200
```

**Write your story.** Open `index.html`, search for `EDIT THIS`, and replace the
placeholder foreword with your own text.

**Refresh later.** Re-run `python fetch_strava.py` any time to pull in new activities.

**Put it online.** It's three static files (`index.html`, `data.js`, and nothing else
required). Drop them into any static host — GitHub Pages, Netlify, Cloudflare Pages —
and it's live. Note that this publishes your `data.js`, including approximate start
coordinates, so only do this if you're comfortable sharing that.

---

## What comes from where

- **Distance, time, elevation, pace, heart rate, start time, indoor/outdoor, route** —
  straight from Strava's activity list.
- **Countries & US states** — derived offline from each activity's start coordinates.
- **Temperature & conditions** — optional, from Open-Meteo (`--weather`).
- **Streaks, totals, all charts** — computed in your browser from `data.js`.

Sections with no data simply don't appear (e.g. no heart-rate monitor → no HR charts).

## Privacy

Everything runs locally. Your token lives in `strava_tokens.json` on your machine and is
never sent anywhere except Strava. Add `.env` and `strava_tokens.json` to `.gitignore`
if you put this in a repo.

## Credits

Concept and design inspired by **nodaysoff.run** by Adrien Friggeri. Fonts: Jost, Space
Mono. Boundaries: world-atlas / us-atlas (Natural Earth).
