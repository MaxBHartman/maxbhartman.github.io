# maxhartman.github.io

Personal site. Plain static HTML/CSS/JS, no build step — design inspired by
[friggeri.net](https://friggeri.net/).

```
index.html          landing page
work/                experience & education
research/            publications
run/                 Strava training-log dashboard (see run/README.md)
books/                reading list
projects/             project index + per-project pages
assets/css/site.css   shared design system
```

Served directly from `main` via GitHub Pages (Settings → Pages → Deploy from a
branch → `main` / root). `.nojekyll` at the repo root tells Pages to serve the
files as-is without running them through Jekyll.

To preview locally:

```
python3 -m http.server
```
