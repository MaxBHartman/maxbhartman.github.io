#!/usr/bin/env python3
"""
fetch_strava.py -- pull your full Strava history and build data.js for the dashboard.

Quick start:
  1. Create an API application at https://www.strava.com/settings/api
     (see README.md for the exact fields to enter)
  2. Put your credentials in the environment (or a .env file next to this script):
        export STRAVA_CLIENT_ID=12345
        export STRAVA_CLIENT_SECRET=abc123...
  3. python fetch_strava.py           # first run opens a browser-based login
  4. python fetch_strava.py --weather # optional: adds temperature + conditions (slower)

Other flags:
  --demo      write synthetic data.js so you can preview the dashboard with no account
  --refresh   force a token refresh
  --limit N   only fetch the N most recent activities (handy for testing)

Only your own data is ever accessed (Strava "single player mode"). Nothing is uploaded
anywhere -- everything is written to data.js in this folder.
"""

import argparse
import datetime as dt
import json
import math
import os
import random
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOKEN_FILE = HERE / "strava_tokens.json"
OUT_FILE = HERE / "data.js"

API = "https://www.strava.com/api/v3"
AUTH_URL = "https://www.strava.com/oauth/authorize"
TOKEN_URL = "https://www.strava.com/oauth/token"

M_PER_MI = 1609.344
M_PER_FT = 0.3048

# Strava sport_type values that are "on foot" -> get pace / PR treatment
FOOT_TYPES = {"Run", "TrailRun", "Walk", "Hike", "VirtualRun"}


# --------------------------------------------------------------------------- #
# tiny .env loader (no dependency)
# --------------------------------------------------------------------------- #
def load_dotenv():
    env = HERE / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


# --------------------------------------------------------------------------- #
# OAuth
# --------------------------------------------------------------------------- #
def require_requests():
    try:
        import requests  # noqa
        return requests
    except ImportError:
        sys.exit("Missing dependency. Run:  pip install requests")


def get_credentials():
    cid = os.environ.get("STRAVA_CLIENT_ID")
    secret = os.environ.get("STRAVA_CLIENT_SECRET")
    if not cid or not secret:
        sys.exit(
            "Set STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET first.\n"
            "Either export them, or create a .env file (see README.md)."
        )
    return cid.strip(), secret.strip()


def do_oauth(requests, cid, secret):
    """First-time login: user authorizes in the browser, pastes back the code."""
    params = (
        f"client_id={cid}"
        "&response_type=code"
        "&redirect_uri=http://localhost/exchange_token"
        "&approval_prompt=auto"
        "&scope=activity:read_all"
    )
    url = f"{AUTH_URL}?{params}"
    print("\n1) Open this URL in your browser and click Authorize:\n")
    print("   " + url + "\n")
    print("2) Your browser will redirect to a http://localhost/... page that fails")
    print("   to load -- that's expected. Copy the value of `code=` from its address")
    print("   bar (the part between code= and &scope).\n")
    code = input("Paste the code here: ").strip()

    r = requests.post(
        TOKEN_URL,
        data={
            "client_id": cid,
            "client_secret": secret,
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    r.raise_for_status()
    tok = r.json()
    save_tokens(tok)
    return tok


def refresh_tokens(requests, cid, secret, tok):
    r = requests.post(
        TOKEN_URL,
        data={
            "client_id": cid,
            "client_secret": secret,
            "grant_type": "refresh_token",
            "refresh_token": tok["refresh_token"],
        },
        timeout=30,
    )
    r.raise_for_status()
    new = r.json()
    save_tokens(new)
    return new


def save_tokens(tok):
    TOKEN_FILE.write_text(json.dumps(tok, indent=2))


def get_access_token(requests, cid, secret, force_refresh=False):
    tok = None
    if TOKEN_FILE.exists():
        tok = json.loads(TOKEN_FILE.read_text())
    if tok is None:
        tok = do_oauth(requests, cid, secret)
    elif force_refresh or tok.get("expires_at", 0) <= time.time() + 60:
        tok = refresh_tokens(requests, cid, secret, tok)
    return tok["access_token"]


# --------------------------------------------------------------------------- #
# Fetching
# --------------------------------------------------------------------------- #
def fetch_all_activities(requests, token, limit=None):
    out, page, per_page = [], 1, 200
    headers = {"Authorization": f"Bearer {token}"}
    while True:
        r = requests.get(
            f"{API}/athlete/activities",
            headers=headers,
            params={"per_page": per_page, "page": page},
            timeout=60,
        )
        if r.status_code == 429:
            print("Rate limited by Strava; waiting 15 minutes...")
            time.sleep(15 * 60 + 5)
            continue
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        out.extend(batch)
        print(f"  fetched page {page} ({len(out)} activities so far)")
        if limit and len(out) >= limit:
            out = out[:limit]
            break
        page += 1
        time.sleep(0.3)  # be polite
    return out


def fetch_athlete_name(requests, token):
    try:
        r = requests.get(f"{API}/athlete", headers={"Authorization": f"Bearer {token}"}, timeout=30)
        r.raise_for_status()
        a = r.json()
        name = " ".join(x for x in [a.get("firstname"), a.get("lastname")] if x)
        return name or None
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Enrichment: offline reverse-geocoding (country + US state)
# --------------------------------------------------------------------------- #
def build_geocoder():
    """Returns a function latlng -> (country_name, us_state) or (None, None)."""
    try:
        import reverse_geocoder as rg
        import pycountry
    except ImportError:
        print("  (skipping geography: pip install reverse_geocoder pycountry to enable)")
        return None

    def cc_to_name(cc):
        try:
            c = pycountry.countries.get(alpha_2=cc)
            return c.name if c else cc
        except Exception:
            return cc

    def lookup(coords):
        # coords: list of (lat, lon) -> list of (country, state)
        res = rg.search(coords, verbose=False)
        out = []
        for row in res:
            cc = row.get("cc")
            country = cc_to_name(cc) if cc else None
            state = row.get("admin1") if cc == "US" else None
            out.append((country, state))
        return out

    return lookup


# --------------------------------------------------------------------------- #
# Enrichment: optional weather via Open-Meteo historical archive (no API key)
# --------------------------------------------------------------------------- #
WMO = {  # Open-Meteo weather codes -> coarse condition label
    0: "Clear", 1: "Clear", 2: "Clouds", 3: "Clouds",
    45: "Fog", 48: "Fog",
    51: "Drizzle", 53: "Drizzle", 55: "Drizzle", 56: "Drizzle", 57: "Drizzle",
    61: "Rain", 63: "Rain", 65: "Rain", 66: "Rain", 67: "Rain",
    71: "Snow", 73: "Snow", 75: "Snow", 77: "Snow",
    80: "Rain", 81: "Rain", 82: "Rain", 85: "Snow", 86: "Snow",
    95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm",
}


def add_weather(requests, records):
    base = "https://archive-api.open-meteo.com/v1/archive"
    done = 0
    for rec in records:
        if not rec["latlng"] or not rec["datetime"]:
            continue
        lat, lon = rec["latlng"]
        day = rec["datetime"][:10]
        hour = int(rec["datetime"][11:13])
        try:
            r = requests.get(
                base,
                params={
                    "latitude": round(lat, 3),
                    "longitude": round(lon, 3),
                    "start_date": day,
                    "end_date": day,
                    "hourly": "temperature_2m,weather_code",
                    "temperature_unit": "fahrenheit",
                    "timezone": "auto",
                },
                timeout=30,
            )
            if r.status_code != 200:
                continue
            h = r.json().get("hourly", {})
            temps, codes = h.get("temperature_2m") or [], h.get("weather_code") or []
            if hour < len(temps) and temps[hour] is not None:
                rec["temp_f"] = round(temps[hour])
            if hour < len(codes) and codes[hour] is not None:
                rec["condition"] = WMO.get(int(codes[hour]), "Clouds")
            done += 1
            if done % 50 == 0:
                print(f"  weather: {done} activities enriched")
            time.sleep(0.15)
        except Exception:
            continue
    print(f"  weather: {done} activities enriched")


# --------------------------------------------------------------------------- #
# Slim a raw Strava activity into what the dashboard needs
# --------------------------------------------------------------------------- #
def slim(a):
    dist_m = a.get("distance") or 0.0
    moving = a.get("moving_time") or 0
    sport = a.get("sport_type") or a.get("type") or "Workout"
    local = a.get("start_date_local") or a.get("start_date") or ""
    latlng = a.get("start_latlng") or None
    if latlng and len(latlng) == 2 and (latlng[0] or latlng[1]):
        latlng = [round(latlng[0], 5), round(latlng[1], 5)]
    else:
        latlng = None
    dist_mi = dist_m / M_PER_MI
    pace = (moving / dist_mi) if (dist_mi > 0 and sport in FOOT_TYPES) else None
    wtype = a.get("workout_type")
    return {
        "id": a.get("id"),
        "name": a.get("name") or "",
        "type": sport,
        "date": local[:10],
        "datetime": local[:19],
        "dist_mi": round(dist_mi, 3),
        "moving_s": moving,
        "elev_ft": round((a.get("total_elevation_gain") or 0.0) / M_PER_FT, 1),
        "avg_hr": round(a["average_heartrate"], 1) if a.get("average_heartrate") else None,
        "pace_s_per_mi": round(pace, 1) if pace else None,
        "trainer": bool(a.get("trainer") or a.get("type") == "VirtualRun"),
        "race": wtype in (1, 11),
        "latlng": latlng,
        "country": None,
        "us_state": None,
        "temp_f": None,
        "condition": None,
    }


# --------------------------------------------------------------------------- #
# Demo data
# --------------------------------------------------------------------------- #
def make_demo():
    random.seed(7)
    recs = []
    start = dt.date.today() - dt.timedelta(days=365 * 4)
    countries = [("United States", ["Colorado", "California", "New York", "Washington", "Oregon"]),
                 ("France", [None]), ("Japan", [None]), ("Canada", [None]), ("Italy", [None])]
    conds = ["Clear", "Clouds", "Clouds", "Rain", "Snow", "Fog"]
    d = start
    end = dt.date.today()
    while d <= end:
        # ~85% of days have an activity, occasional doubles
        n = 0
        if random.random() < 0.85:
            n = 1 + (1 if random.random() < 0.12 else 0)
        for _ in range(n):
            foot = random.random() < 0.7
            sport = random.choice(["Run", "Run", "Run", "TrailRun", "Walk"]) if foot \
                else random.choice(["Ride", "Ride", "VirtualRide", "Swim"])
            if sport == "Swim":
                dist = round(random.uniform(0.5, 2.0), 2)
            elif sport in ("Ride", "VirtualRide"):
                dist = round(random.uniform(8, 45), 2)
            else:
                base = random.choice([1, 3, 3, 4, 5, 6, 8, 10, 13, 18])
                dist = round(base + random.uniform(-0.4, 1.2), 2)
            pace = random.uniform(7.5, 10.5) * 60 if sport in FOOT_TYPES else None
            moving = int((dist * pace) if pace else dist / 15 * 3600)
            hour = int(min(23, max(4, random.gauss(7.5, 2.5))))
            hr = int(random.gauss(138, 16)) if random.random() < 0.85 else None
            country, states = random.choices(countries, weights=[70, 8, 6, 8, 8])[0]
            recs.append({
                "id": random.randint(10**9, 9 * 10**9),
                "name": f"{sport} {d.isoformat()}",
                "type": sport,
                "date": d.isoformat(),
                "datetime": f"{d.isoformat()}T{hour:02d}:{random.randint(0,59):02d}:00",
                "dist_mi": dist,
                "moving_s": moving,
                "elev_ft": round(max(0, random.gauss(dist * 60, 120)), 1),
                "avg_hr": hr,
                "pace_s_per_mi": round(pace, 1) if pace else None,
                "trainer": sport in ("VirtualRide",) or random.random() < 0.2,
                "race": random.random() < 0.02,
                "latlng": [39.7 + random.uniform(-0.2, 0.2), -105.0 + random.uniform(-0.2, 0.2)],
                "country": country,
                "us_state": random.choice(states),
                "temp_f": random.randint(15, 92),
                "condition": random.choice(conds),
            })
        d += dt.timedelta(days=1)
    meta = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "athlete_name": "Demo Athlete",
        "units": "imperial",
        "has_weather": True,
        "has_geo": True,
        "demo": True,
    }
    return {"meta": meta, "activities": recs}


# --------------------------------------------------------------------------- #
# Write
# --------------------------------------------------------------------------- #
def write_data(payload):
    js = "window.STRAVA_DATA = " + json.dumps(payload, separators=(",", ":")) + ";\n"
    OUT_FILE.write_text(js)
    n = len(payload["activities"])
    print(f"\nWrote {OUT_FILE}  ({n} activities, {len(js)//1024} KB)")
    print("Open index.html to view your dashboard.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="write synthetic data, no Strava needed")
    ap.add_argument("--weather", action="store_true", help="add temperature/conditions (slow)")
    ap.add_argument("--refresh", action="store_true", help="force token refresh")
    ap.add_argument("--limit", type=int, default=None, help="only newest N activities")
    args = ap.parse_args()

    if args.demo:
        write_data(make_demo())
        return

    load_dotenv()
    requests = require_requests()
    cid, secret = get_credentials()
    token = get_access_token(requests, cid, secret, force_refresh=args.refresh)

    print("Fetching activities from Strava...")
    raw = fetch_all_activities(requests, token, limit=args.limit)
    print(f"Got {len(raw)} activities.")
    records = [slim(a) for a in raw]

    # geography
    geocode = build_geocoder()
    has_geo = False
    if geocode:
        pts = [(r["latlng"][0], r["latlng"][1]) for r in records if r["latlng"]]
        if pts:
            print("Reverse-geocoding locations (offline)...")
            results = geocode(pts)
            i = 0
            for r in records:
                if r["latlng"]:
                    r["country"], r["us_state"] = results[i]
                    i += 1
            has_geo = True

    # weather (optional)
    has_weather = False
    if args.weather:
        print("Fetching historical weather (this can take a while)...")
        add_weather(requests, records)
        has_weather = any(r["temp_f"] is not None for r in records)

    meta = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "athlete_name": fetch_athlete_name(requests, token),
        "units": "imperial",
        "has_weather": has_weather,
        "has_geo": has_geo,
        "demo": False,
    }
    write_data({"meta": meta, "activities": records})


if __name__ == "__main__":
    main()
