# strava-live Worker

Proxies Strava for `/run` so the page can fetch current data on every visit
without shipping a client secret to the browser. See `../run/README.md` for
the full picture; this is just the deploy checklist.

## One-time deploy

Run these yourself against your own Cloudflare account (`npm i -g wrangler`
if you don't have it):

```bash
cd worker
wrangler login

# 1. Create the KV namespace, then paste the printed id into wrangler.toml
wrangler kv namespace create STRAVA_KV

# 2. Strava app credentials (from strava.com/settings/api)
wrangler secret put STRAVA_CLIENT_ID
wrangler secret put STRAVA_CLIENT_SECRET

# 3. Seed the refresh token you got from the one-time OAuth login
#    (see ../run/README.md "One-time setup") — the id is the same
#    namespace you created above.
wrangler kv key put refresh_token "PASTE_REFRESH_TOKEN_HERE" --binding=STRAVA_KV

# 4. Ship it
wrangler deploy
```

Then, in the Cloudflare dashboard for the `maxhartman.net` zone, confirm the
route `maxhartman.net/api/strava*` is bound to this Worker (wrangler.toml
declares it, but double-check it took under Workers Routes) and that the
zone is proxied (orange-clouded) so the route can intercept it.

## Verifying it

```bash
curl https://maxhartman.net/api/strava
```

should return JSON shaped like `{"meta": {...}, "activities": [...]}` with
your real activities. Open `/run/` in a browser and confirm the dashboard
renders.

To test the enrichment cron without waiting for its schedule:

```bash
wrangler dev --test-scheduled
# then, in another terminal:
curl "http://localhost:8787/__scheduled?cron=0+8+*+*+*"
```

Geography/Weather sections on `/run` stay hidden until this has run at least
once and found something to enrich.

## Rotating credentials

If you ever need to revoke access, regenerate the Strava app's client secret
at strava.com/settings/api and re-run `wrangler secret put
STRAVA_CLIENT_SECRET`. The refresh token in KV keeps working across normal
token refreshes — the Worker updates it automatically if Strava ever issues a
new one.
