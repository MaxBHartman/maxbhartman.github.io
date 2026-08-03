const STRAVA_API = "https://www.strava.com/api/v3";
const STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token";
const GEOCODE_URL = "https://api.bigdatacloud.net/data/reverse-geocode-client";
const WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive";

const M_PER_MI = 1609.344;
const M_PER_FT = 0.3048;
const FOOT_TYPES = new Set(["Run", "TrailRun", "Walk", "Hike", "VirtualRun"]);
const CACHE_TTL_SECONDS = 300; // rate-limit safety net, not a data-staleness mechanism

const WMO = {
  0: "Clear", 1: "Clear", 2: "Clouds", 3: "Clouds",
  45: "Fog", 48: "Fog",
  51: "Drizzle", 53: "Drizzle", 55: "Drizzle", 56: "Drizzle", 57: "Drizzle",
  61: "Rain", 63: "Rain", 65: "Rain", 66: "Rain", 67: "Rain",
  71: "Snow", 73: "Snow", 75: "Snow", 77: "Snow",
  80: "Rain", 81: "Rain", 82: "Rain", 85: "Snow", 86: "Snow",
  95: "Thunderstorm", 96: "Thunderstorm", 99: "Thunderstorm",
};

// ---------------------------------------------------------------------------
// Strava OAuth — access token cached in KV, refreshed on demand
// ---------------------------------------------------------------------------
async function getAccessToken(env) {
  const expiresAt = Number((await env.STRAVA_KV.get("expires_at")) || 0);
  if (expiresAt > Date.now() / 1000 + 60) {
    return env.STRAVA_KV.get("access_token");
  }

  const refreshToken = await env.STRAVA_KV.get("refresh_token");
  if (!refreshToken) {
    throw new Error("No refresh_token in KV — seed it once via `wrangler kv key put`");
  }

  const res = await fetch(STRAVA_TOKEN_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      client_id: env.STRAVA_CLIENT_ID,
      client_secret: env.STRAVA_CLIENT_SECRET,
      grant_type: "refresh_token",
      refresh_token: refreshToken,
    }),
  });
  if (!res.ok) throw new Error(`Strava token refresh failed: ${res.status}`);
  const tok = await res.json();

  await Promise.all([
    env.STRAVA_KV.put("access_token", tok.access_token),
    env.STRAVA_KV.put("expires_at", String(tok.expires_at)),
    env.STRAVA_KV.put("refresh_token", tok.refresh_token),
  ]);
  return tok.access_token;
}

// ---------------------------------------------------------------------------
// Strava data
// ---------------------------------------------------------------------------
async function fetchAllActivities(token) {
  const out = [];
  let page = 1;
  const perPage = 200;
  while (true) {
    const res = await fetch(
      `${STRAVA_API}/athlete/activities?per_page=${perPage}&page=${page}`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (!res.ok) throw new Error(`Strava activities fetch failed: ${res.status}`);
    const batch = await res.json();
    if (!batch.length) break;
    out.push(...batch);
    page += 1;
  }
  return out;
}

async function fetchAthleteName(token) {
  const res = await fetch(`${STRAVA_API}/athlete`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return null;
  const a = await res.json();
  return [a.firstname, a.lastname].filter(Boolean).join(" ") || null;
}

function slim(a) {
  const distM = a.distance || 0;
  const moving = a.moving_time || 0;
  const sport = a.sport_type || a.type || "Workout";
  const local = a.start_date_local || a.start_date || "";
  let latlng = a.start_latlng;
  if (latlng && latlng.length === 2 && (latlng[0] || latlng[1])) {
    latlng = [Math.round(latlng[0] * 1e5) / 1e5, Math.round(latlng[1] * 1e5) / 1e5];
  } else {
    latlng = null;
  }
  const distMi = distM / M_PER_MI;
  const pace = distMi > 0 && FOOT_TYPES.has(sport) ? moving / distMi : null;

  return {
    id: a.id,
    name: a.name || "",
    type: sport,
    date: local.slice(0, 10),
    datetime: local.slice(0, 19),
    dist_mi: Math.round(distMi * 1000) / 1000,
    moving_s: moving,
    elev_ft: Math.round(((a.total_elevation_gain || 0) / M_PER_FT) * 10) / 10,
    avg_hr: a.average_heartrate ? Math.round(a.average_heartrate * 10) / 10 : null,
    pace_s_per_mi: pace ? Math.round(pace * 10) / 10 : null,
    trainer: Boolean(a.trainer || a.type === "VirtualRun"),
    race: a.workout_type === 1 || a.workout_type === 11,
    latlng,
    country: null,
    us_state: null,
    temp_f: null,
    condition: null,
  };
}

// ---------------------------------------------------------------------------
// Permanent enrichment (geo + weather), written by the daily cron only
// ---------------------------------------------------------------------------
async function mergeEnrichment(activities, env) {
  let hasGeo = false;
  let hasWeather = false;
  await Promise.all(
    activities.map(async (act) => {
      if (!act.latlng) return;
      const [geo, weather] = await Promise.all([
        env.STRAVA_KV.get(`geo:${act.id}`, "json"),
        env.STRAVA_KV.get(`weather:${act.id}`, "json"),
      ]);
      if (geo) {
        act.country = geo.country;
        act.us_state = geo.us_state;
        hasGeo = true;
      }
      if (weather) {
        act.temp_f = weather.temp_f;
        act.condition = weather.condition;
        hasWeather = true;
      }
    })
  );
  return { hasGeo, hasWeather };
}

async function enrichOne(act, env) {
  if (!act.latlng) return;
  const [lat, lon] = act.latlng;

  const geoKey = `geo:${act.id}`;
  if (!(await env.STRAVA_KV.get(geoKey))) {
    try {
      const res = await fetch(
        `${GEOCODE_URL}?latitude=${lat}&longitude=${lon}&localityLanguage=en`
      );
      if (res.ok) {
        const j = await res.json();
        const country = j.countryName || null;
        const usState = j.countryCode === "US" ? j.principalSubdivision || null : null;
        await env.STRAVA_KV.put(geoKey, JSON.stringify({ country, us_state: usState }));
      }
    } catch (_) {
      // leave unresolved; next cron run retries
    }
  }

  const weatherKey = `weather:${act.id}`;
  if (!(await env.STRAVA_KV.get(weatherKey)) && act.datetime) {
    try {
      const day = act.datetime.slice(0, 10);
      const hour = Number(act.datetime.slice(11, 13));
      const res = await fetch(
        `${WEATHER_URL}?latitude=${lat.toFixed(3)}&longitude=${lon.toFixed(3)}` +
          `&start_date=${day}&end_date=${day}&hourly=temperature_2m,weather_code` +
          `&temperature_unit=fahrenheit&timezone=auto`
      );
      if (res.ok) {
        const j = await res.json();
        const temps = (j.hourly && j.hourly.temperature_2m) || [];
        const codes = (j.hourly && j.hourly.weather_code) || [];
        if (temps[hour] != null) {
          const tempF = Math.round(temps[hour]);
          const condition = WMO[codes[hour]] || "Clouds";
          await env.STRAVA_KV.put(weatherKey, JSON.stringify({ temp_f: tempF, condition }));
        }
      }
    } catch (_) {
      // leave unresolved; next cron run retries
    }
  }
}

// ---------------------------------------------------------------------------
// fetch() — GET /api/strava, cached briefly as a Strava rate-limit safety net
// ---------------------------------------------------------------------------
async function handleFetch(request, env, ctx) {
  const cache = caches.default;
  const cacheKey = new Request(new URL(request.url).toString(), request);

  const cached = await cache.match(cacheKey);
  if (cached) return cached;

  const token = await getAccessToken(env);
  const [raw, athleteName] = await Promise.all([
    fetchAllActivities(token),
    fetchAthleteName(token),
  ]);
  const activities = raw.map(slim);
  const { hasGeo, hasWeather } = await mergeEnrichment(activities, env);

  const payload = {
    meta: {
      generated_at: new Date().toISOString(),
      athlete_name: athleteName,
      units: "imperial",
      has_weather: hasWeather,
      has_geo: hasGeo,
      demo: false,
    },
    activities,
  };

  const response = new Response(JSON.stringify(payload), {
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Cache-Control": `public, max-age=${CACHE_TTL_SECONDS}`,
    },
  });
  ctx.waitUntil(cache.put(cacheKey, response.clone()));
  return response;
}

// ---------------------------------------------------------------------------
// scheduled() — daily cron, enriches whatever hasn't been resolved yet
// ---------------------------------------------------------------------------
async function handleScheduled(env) {
  const token = await getAccessToken(env);
  const raw = await fetchAllActivities(token);
  const activities = raw.map(slim);
  let attempted = 0;
  for (const act of activities) {
    if (act.latlng) attempted++;
    await enrichOne(act, env);
  }
  return { total: activities.length, withLatlng: attempted };
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname === "/api/strava/enrich") {
      try {
        const stats = await handleScheduled(env);
        return new Response(JSON.stringify({ ok: true, ...stats }), {
          headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
        });
      } catch (err) {
        return new Response(JSON.stringify({ ok: false, error: String(err), stack: err.stack }), {
          status: 502,
          headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
        });
      }
    }
    if (url.pathname.startsWith("/api/strava")) {
      try {
        return await handleFetch(request, env, ctx);
      } catch (err) {
        return new Response(JSON.stringify({ error: String(err) }), {
          status: 502,
          headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
        });
      }
    }
    return new Response("Not found", { status: 404 });
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(handleScheduled(env));
  },
};
