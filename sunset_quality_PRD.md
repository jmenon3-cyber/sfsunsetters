# Product Requirements Document: SF Sunset Quality App

**Version:** 2.0  
**Updated:** April 2026  
**Status:** In development  

---

## Overview

A Mr. Chilly-inspired neighborhood-level sunset quality forecaster for San Francisco and the greater Bay Area. The app shows a color-coded heatmap of SF neighborhoods scored on how good the sunset will look — updated with live atmospheric data at each neighborhood's coordinates.

---

## Problem Statement

Generic weather apps report a single temperature or cloud cover value for all of San Francisco — usually pulled from SFO or a downtown sensor. SF's microclimates make this nearly useless: it can be socked in at Ocean Beach while the Mission basks in golden hour. No existing tool gives neighborhood-level sunset quality predictions.

---

## Goals

- Show sunset quality scores per SF neighborhood, not just city-wide
- Pull real atmospheric data at sunset time from a free, reliable API
- Surface the key variables that drive sunset quality (cloud cover by altitude, visibility, humidity)
- Match the visual language of Mr. Chilly: illustrated map, color-coded heatmap, tap-to-inspect

---

## Non-Goals (v1)

- Native iOS/Android app (web-first)
- Fog layer visualization
- Animated day/night cycle
- Push notifications
- User-saved locations

---

## Scoring Algorithm

Each neighborhood receives a **Sunset Score from 0–100**, computed at the local sunset hour using five weighted factors.

### Inputs (from Open-Meteo `/v1/forecast`)

| Variable | API Parameter | Weight |
|----------|--------------|--------|
| Total cloud cover | `cloud_cover` | High |
| High cloud cover | `cloud_cover_high` | High |
| Mid cloud cover | `cloud_cover_mid` | Medium |
| Low cloud cover | `cloud_cover_low` | Low |
| Visibility | `visibility` | Medium |
| Relative humidity | `relative_humidity_2m` | Low |

### Scoring Breakdown

**Cloud cover score (max 35 pts)**
- 30–70% total cloud cover → 35 pts *(optimal canvas for color)*
- 10–30% or 70–85% → 15 pts
- Outside these ranges → 0 pts

**Cloud altitude score (max 25 pts)**
- High clouds (cirrus/cirrostratus) present (>20%) → 25 pts
- Mid clouds (altocumulus) present (>20%) → 10 pts
- Only low clouds or no clouds → 0 pts

**Atmospheric clarity score (max 20 pts)**
- Visibility 5–20 km (light haze) → 20 pts *(enhances scattering)*
- Visibility > 20 km (very clear) → 10 pts
- Visibility < 5 km (heavy haze/fog) → 0 pts

**Humidity score (max 10 pts)**
- 40–70% humidity → 10 pts
- 20–40% or 70–85% → 5 pts
- Outside these ranges → 0 pts

**Post-frontal bonus (max 10 pts)**
- *(v2 feature — requires NWS frontal passage data)*

### Rating Scale

| Score | Rating | Description |
|-------|--------|-------------|
| 80–100 | Spectacular 🔥 | Once-in-a-week sky. Drop everything. |
| 60–79 | Beautiful 🌅 | Vivid colors, well worth watching. |
| 40–59 | Decent 🌤️ | Some color, but nothing dramatic. |
| 20–39 | Muted 😐 | Faint hues, easily missed. |
| 0–19 | Skip it ☁️ | Overcast or featureless sky. |

---

## Data Architecture

### Primary Data Source: Open-Meteo

**Endpoint:** `https://api.open-meteo.com/v1/forecast`

**Parameters:**
```
latitude={lat}
longitude={lon}
hourly=cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,visibility,relative_humidity_2m
forecast_days=3
timezone=America/Los_Angeles
```

**Why Open-Meteo:**
- Free, no API key required
- Returns cloud cover split by altitude layer (low/mid/high) — critical for score accuracy
- Hourly resolution for up to 7 days
- No rate limiting for reasonable usage
- Global coverage, reliable uptime

### Sunset Hour Logic

Scores are extracted at the local sunset hour for each neighborhood's day of interest. Estimated sunset hours by season:

| Season | Approx. Sunset Hour (PT) |
|--------|--------------------------|
| Winter (Nov–Jan) | 17:00 |
| Spring (Mar–May) | 19:00 |
| Summer (Jun–Aug) | 20:00 |
| Fall (Sep–Oct) | 18:00 |

*v2 enhancement: use a solar position library (e.g. SunCalc) for precise sunset time by exact date and latitude.*

### Neighborhood Coordinates

Each neighborhood is represented by a single lat/lon centroid. The API is called once per neighborhood per page load and results are cached for the session.

| Neighborhood | Latitude | Longitude |
|---|---|---|
| Presidio | 37.7989 | -122.4662 |
| Outer Richmond | 37.7780 | -122.4883 |
| Inner Richmond | 37.7799 | -122.4571 |
| Marina | 37.8030 | -122.4363 |
| North Beach | 37.8061 | -122.4103 |
| Nob Hill | 37.7930 | -122.4161 |
| Outer Sunset | 37.7502 | -122.5076 |
| Haight | 37.7692 | -122.4481 |
| Hayes Valley | 37.7759 | -122.4245 |
| Tenderloin | 37.7835 | -122.4147 |
| SoMa | 37.7785 | -122.3948 |
| Mission | 37.7599 | -122.4148 |
| Twin Peaks | 37.7544 | -122.4477 |
| Castro | 37.7609 | -122.4350 |
| Noe Valley | 37.7502 | -122.4338 |
| Potrero Hill | 37.7601 | -122.4013 |
| Bayview | 37.7309 | -122.3892 |
| Excelsior | 37.7240 | -122.4245 |

---

## UI Specification

### Map View

- SVG-based illustrated map of SF with neighborhood polygons
- Each polygon filled with a color from the sunset quality scale
- Score displayed as a number inside each polygon
- Tap/hover on a neighborhood to reveal tooltip with: score, rating, cloud cover %, visibility, humidity

### Color Scale

| Rating | Hex Color |
|--------|-----------|
| Spectacular | `#C42828` (deep red) |
| Beautiful | `#E8580C` (burnt orange) |
| Decent | `#D4891A` (amber) |
| Muted | `#A07828` (dark gold) |
| Skip it | `#555E3B` (olive gray) |

Colors intentionally mirror the palette of a real sunset sky.

### Tooltip

Shown on hover (desktop) or tap (mobile). Contains:
- Neighborhood name
- Score (colored to match rating)
- Rating label and emoji
- Raw values: cloud cover %, visibility (km), humidity (%)

### Day Switcher

Three buttons — Tonight, Tomorrow, In 2 days — switch the displayed forecast. All three days are fetched on load and cached; switching days is instant with no additional API calls.

### Ranked List

Below the map: top 10 neighborhoods sorted by score descending, shown in a 2-column grid. Each row displays neighborhood name, score, and emoji indicator.

### Loading State

While API calls are in flight, a spinner overlay covers the map. If API calls fail (e.g. network unavailable), an error message replaces the spinner with context.

---

## Performance & Caching

- All 18 neighborhood API calls are fired in parallel with `Promise.allSettled`
- `Promise.allSettled` (not `Promise.all`) ensures a single failed call doesn't block rendering
- Results are cached in-memory for the session — day switching never re-fetches
- Fallback score of 45 ("Decent") is used for any neighborhood where the fetch fails

---

## Known Limitations

- Open-Meteo data is gridded at ~1 km resolution — differences between adjacent SF neighborhoods may be small or identical in the API response even though microclimate variation is real
- Fog is not modeled as a distinct layer — it affects the `visibility` variable and `cloud_cover_low`, which the scoring algorithm partially captures
- Post-frontal bonus is not yet implemented (requires NWS frontal passage API, planned for v2)
- Sunset hour is estimated by season, not calculated precisely — off by up to 30 minutes at equinoxes

---

## Roadmap

### v1 (current)
- Live data from Open-Meteo per neighborhood
- 3-day forecast switcher
- Tooltip with raw atmospheric values
- In-memory caching

### v2
- Precise sunset time via SunCalc library
- Post-frontal bonus via NWS API
- Fog layer visualization overlay
- Bay Area expansion (Oakland, Marin, Peninsula)
- Shareable links per day/neighborhood

### v3
- Push notifications ("Tonight looks spectacular in the Mission")
- Historical accuracy scoring (compare predictions to actual photos)
- User-submitted sunset photos per neighborhood

---

## Technical Stack

| Layer | Choice |
|-------|--------|
| Frontend | HTML/CSS/JS (single file, no build step) or React |
| Map | SVG with hand-drawn neighborhood polygons |
| Weather data | Open-Meteo REST API (free, no key) |
| Hosting | Any static host (Vercel, Netlify, GitHub Pages) |
| Future: sunset time | SunCalc.js (MIT) |
| Future: NWS frontal data | api.weather.gov (free, no key) |
