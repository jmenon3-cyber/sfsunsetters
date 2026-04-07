# SF Sunsetters — How It Works

## What This App Does

SF Sunsetters predicts how good the sunset will look from 20 different San Francisco neighborhoods, tonight and over the next two days. Each neighborhood gets a score from 0 to 100 and a rating from "Skip it" to "Spectacular."

## Where the Weather Data Comes From

The app fetches a single weather forecast from [wttr.in](https://wttr.in/) for San Francisco. It uses the actual sunset time from the API's astronomy data to pick the closest forecast time slot. If astronomy data isn't available, it falls back to a seasonal estimate:

- **Winter** (Nov–Feb): 5:00 PM
- **Spring** (Mar–May): 7:00 PM
- **Summer** (Jun–Aug): 8:00 PM
- **Fall** (Sep–Oct): 6:00 PM

To smooth out sharp weather transitions, the app blends the sunset time slot with the preceding slot (60/40 weighting), giving a better picture of the lead-up conditions.

From that forecast, it derives six weather measurements: cloud cover, low cloud cover, mid-level cloud cover, high cloud cover, visibility, and humidity.

### How Cloud Types Are Inferred

The API doesn't report cloud altitude directly. Instead, the app infers cloud character from related signals:

- **Low clouds** (fog, marine layer): Derived from the chance of fog and low visibility readings. High fog chance + poor visibility = lots of low clouds.
- **Mid-level clouds**: Estimated from total cloud cover weighted against the chance of sunshine. Overcast with no sunshine suggests thick mid-level clouds.
- **High clouds** (cirrus, the "good" sunset clouds): Inferred when cloud cover is present but fog chance is low and some sunshine is getting through — thin, high clouds that catch sunset light.

## How Each Neighborhood Gets a Different Score

San Francisco is small enough that the raw weather data is essentially the same city-wide. What actually changes the sunset experience is *where you're standing*. The app adjusts each neighborhood's weather data using three geographic traits:

### Horizon View (biggest factor)

How much of the western sky you can actually see. If buildings and hills block your view of the horizon, it doesn't matter how perfect the clouds are.

- **Best:** Sunset (1.0) — directly faces the open Pacific, nothing in the way
- **Best:** Twin Peaks (0.95) and Presidio (0.95) — elevated with panoramic western views
- **Worst:** Tenderloin (0.10) — surrounded by tall buildings, almost no sky visible
- **Worst:** SoMa (0.15) — similar situation, hemmed in by downtown

### Fog Exposure

How much the marine layer (Karl the Fog) affects the neighborhood. Fog rolls in from the Pacific, so western neighborhoods get hit first and hardest.

- **Most fog:** Sunset (1.0) — first neighborhood the fog reaches
- **Heavy fog:** Outer Richmond (0.85), Lake Merced (0.80) — also right on the coast
- **Least fog:** Tenderloin (0.05), SoMa (0.05), Mission (0.05) — protected by hills and distance from the coast

Fog exposure isn't static — it varies by two additional factors:

#### Seasonal Fog

San Francisco's marine layer is heavily seasonal. The app applies a monthly fog multiplier so western neighborhoods are penalized more during fog season (June–August) and less during clear months (October–February).

#### Wind-Based Fog

Wind direction and speed affect how far inland the fog pushes. Westerly winds (from the ocean, 210°–330°) amplify fog exposure — the stronger the wind, the deeper the fog reaches. Non-westerly winds (especially offshore easterlies) suppress fog, letting coastal neighborhoods score higher.

### Elevation

Higher neighborhoods can often see above the fog layer, giving them a clearer view. Elevation also slightly improves visibility scores.

- **Highest:** Twin Peaks (1.0) — tallest point in the city
- **High:** Nob Hill (0.75), Potrero Hill (0.70)
- **Lowest:** Tenderloin (0.05), SoMa (0.05) — essentially at sea level in a valley

## How the Score Is Calculated

Every neighborhood gets a score out of 100, built from five components. Each one uses a smooth curve rather than hard cutoffs, so even small weather differences produce different scores.

### Cloud Cover (up to 35 points)

The ideal cloud coverage for a colorful sunset is about 45%. Too few clouds means nothing to catch the light. Too many clouds block the sun entirely. The score peaks at 45% and smoothly drops off in both directions.

### Cloud Altitude (up to 25 points)

High-altitude clouds are the canvas for spectacular sunsets — they catch light from the sun well after it dips below the horizon and glow in reds and oranges. Mid-level clouds help too, but less. Low clouds (fog, marine layer) block the view and reduce the score.

- High clouds: up to 25 points
- Mid clouds: a smaller bonus
- Low clouds: a penalty that subtracts from the score

### Visibility (up to 20 points)

The sweet spot is around 6–9 miles. Very low visibility (under 3 miles) means haze or fog is washing out colors. Extremely high visibility (crystal-clear air over 15 miles) can actually mean there aren't enough particles in the atmosphere to scatter light into warm colors.

### Humidity (up to 10 points)

Moderate humidity (around 50–60%) is ideal. Some moisture in the air helps scatter light into warm sunset tones. Too dry and the colors are flat; too humid and haze takes over.

### Horizon View (up to 10 points)

A direct bonus based on how much open western sky the neighborhood has. This is the geographic factor described above — it doesn't change with the weather but has a big impact on whether you can actually *see* the sunset.

## Rating Scale

| Score     | Rating       | What It Means                                              |
|-----------|-------------|-------------------------------------------------------------|
| 80–100    | Spectacular | Drop everything and go watch                                |
| 60–79     | Beautiful   | Worth making a point to see                                 |
| 40–59     | Decent      | Nice if you happen to be outside                            |
| 20–39     | Muted       | Some color but nothing special                              |
| 0–19      | Skip it     | Overcast, foggy, or no view — stay inside                   |

## Neighborhood Profiles

The 20 neighborhoods ranked roughly by sunset-watching potential:

| Neighborhood    | Horizon View | Fog Exposure | Elevation | Best For                           |
|----------------|-------------|-------------|-----------|-------------------------------------|
| Sunset          | Full ocean   | Very high    | Low       | Clear days — unbeatable ocean views |
| Twin Peaks      | Panoramic    | Moderate     | Highest   | Most consistent — above the fog     |
| Presidio        | Full ocean   | High         | Moderate  | Great when fog stays low            |
| Outer Richmond  | Full ocean   | Very high    | Low       | Similar to Sunset                   |
| Marina          | Good         | Moderate     | Low       | Bay + Golden Gate Bridge views      |
| Lake Merced     | Good         | High         | Low       | Coastal lake with open western sky  |
| Inner Richmond  | Good         | Moderate     | Low       | Solid western exposure              |
| Potrero Hill    | Good         | Very low     | High      | Clear skies, city panorama          |
| Nob Hill        | Moderate     | Low          | High      | Above downtown, partial western sky |
| Castro          | Moderate     | Low          | Moderate  | Hilltop streets with western gaps   |
| Haight          | Moderate     | Low-moderate | Moderate  | Panhandle park views                |
| Noe Valley      | Limited      | Low          | Moderate  | Valley blocks much of the horizon   |
| North Beach     | Limited      | Very low     | Low-mod   | Better for bay views than sunsets   |
| Ingleside       | Limited      | Low          | Low-mod   | Some hilltop spots along the ridge  |
| Excelsior       | Limited      | Low          | Low-mod   | Some hilltop spots work             |
| Hunter's Point  | Limited      | Very low     | Low       | Faces east, not ideal for sunsets   |
| Hayes Valley    | Limited      | Low          | Low       | Buildings block most of the sky     |
| Mission         | Limited      | Very low     | Low       | Between hills, limited sky          |
| SoMa            | Minimal      | Very low     | Flat      | Downtown canyon, almost no horizon  |
| Tenderloin      | Minimal      | Very low     | Flat      | Dense buildings, no western view    |
