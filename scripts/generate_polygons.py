#!/usr/bin/env python3
"""
Generate geographically accurate SVG polygon data from DataSF GeoJSON.

Downloads the "Analysis Neighborhoods" dataset, maps/merges 41 official
neighborhoods into the 20 used by SF Sunsetters, simplifies paths, and
outputs ready-to-paste JavaScript.

Usage:
    pip install shapely requests
    python scripts/generate_polygons.py
"""

import json
import math
import sys
import urllib.request

from shapely.geometry import shape, MultiPolygon, Polygon
from shapely.ops import unary_union

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

GEOJSON_URL = "https://raw.githubusercontent.com/blackmad/neighborhoods/master/san-francisco.geojson"
TOLERANCE = 0.002         # ~222 meters — compact and clean shapes
OUTLINE_TOLERANCE = 0.002  # ~222m for coastline
SVG_WIDTH = 560
SVG_HEIGHT = 700
PADDING = 20
CENTER_LAT = 37.76  # for cos(lat) aspect correction

# Map every GeoJSON neighborhood name to one of our 20 app IDs
# Source: blackmad/neighborhoods san-francisco.geojson (37 neighborhoods)
GEOJSON_TO_APP_ID = {
    "Bayview":                            "huntersPoint",
    "Bernal Heights":                     "noeValley",
    "Castro/Upper Market":                "castro",
    "Chinatown":                          "nobHill",
    "Crocker Amazon":                     "excelsior",
    "Diamond Heights":                    "twinPeaks",
    "Downtown/Civic Center":              "tenderloin",
    "Excelsior":                          "excelsior",
    "Financial District":                 "soma",
    "Glen Park":                          "noeValley",
    "Golden Gate Park":                   "__PARK__",
    "Haight Ashbury":                     "haight",
    "Inner Richmond":                     "innerRichmond",
    "Inner Sunset":                       "sunset",
    "Lakeshore":                          "lakeMerced",
    "Marina":                             "marina",
    "Mission":                            "mission",
    "Nob Hill":                           "nobHill",
    "Noe Valley":                         "noeValley",
    "North Beach":                        "northBeach",
    "Ocean View":                         "ingleside",
    "Outer Mission":                      "excelsior",
    "Outer Richmond":                     "outerRichmond",
    "Outer Sunset":                       "sunset",
    "Pacific Heights":                    "marina",
    "Parkside":                           "sunset",
    "Potrero Hill":                       "potreroHill",
    "Presidio":                           "presidio",
    "Presidio Heights":                   "presidio",
    "Russian Hill":                       "nobHill",
    "Seacliff":                           "outerRichmond",
    "South of Market":                    "soma",
    "Treasure Island/YBI":                "__EXCLUDE__",
    "Twin Peaks":                         "twinPeaks",
    "Visitacion Valley":                  "ingleside",
    "West of Twin Peaks":                 "twinPeaks",
    "Western Addition":                   "hayesValley",
}

# The 20 app neighborhoods (for ordering output)
APP_IDS = [
    "presidio", "marina", "northBeach", "outerRichmond", "innerRichmond",
    "nobHill", "tenderloin", "sunset", "haight", "hayesValley",
    "soma", "twinPeaks", "castro", "mission", "potreroHill",
    "lakeMerced", "noeValley", "huntersPoint", "ingleside", "excelsior",
]


# ---------------------------------------------------------------------------
# DOWNLOAD
# ---------------------------------------------------------------------------

def download_geojson():
    print("Downloading GeoJSON...", file=sys.stderr)
    req = urllib.request.Request(GEOJSON_URL, headers={"User-Agent": "SFSunsetters/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    print(f"  Got {len(data.get('features', []))} features", file=sys.stderr)
    return data


# ---------------------------------------------------------------------------
# DETECT NEIGHBORHOOD NAME FIELD
# ---------------------------------------------------------------------------

def detect_name_field(feature):
    """Figure out which property contains the neighborhood name."""
    props = feature.get("properties", {})
    # Common field names in DataSF datasets
    for field in ["nhood", "name", "neighborhood", "neighbourhd", "NEIGHBORHOOD", "NAME"]:
        if field in props and props[field]:
            return field
    # Fallback: print all properties and pick the first string
    print(f"  Available properties: {list(props.keys())}", file=sys.stderr)
    for k, v in props.items():
        if isinstance(v, str) and len(v) > 2:
            return k
    raise ValueError(f"Cannot detect neighborhood name field. Properties: {props}")


# ---------------------------------------------------------------------------
# PROJECTION
# ---------------------------------------------------------------------------

def make_projector(all_geometries):
    """Build a projector from lat/lon to SVG coordinates."""
    cos_lat = math.cos(math.radians(CENTER_LAT))

    # Collect all coordinates for bounding box
    all_coords = []
    for geom in all_geometries:
        if geom.geom_type == "Polygon":
            all_coords.extend(geom.exterior.coords)
        elif geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                all_coords.extend(poly.exterior.coords)

    lons = [c[0] for c in all_coords]
    lats = [c[1] for c in all_coords]
    min_lon, max_lon = min(lons), max(lons)
    min_lat, max_lat = min(lats), max(lats)

    # Physical extents in km
    x_extent_km = (max_lon - min_lon) * cos_lat * 111.32
    y_extent_km = (max_lat - min_lat) * 110.57

    # Scale to fit SVG viewport
    scale = min(SVG_WIDTH / x_extent_km, SVG_HEIGHT / y_extent_km)
    x_offset = (SVG_WIDTH - x_extent_km * scale) / 2
    y_offset = (SVG_HEIGHT - y_extent_km * scale) / 2

    print(f"  Bounding box: lon [{min_lon:.4f}, {max_lon:.4f}], lat [{min_lat:.4f}, {max_lat:.4f}]", file=sys.stderr)
    print(f"  Physical extent: {x_extent_km:.1f} km x {y_extent_km:.1f} km", file=sys.stderr)
    print(f"  Scale: {scale:.2f} px/km", file=sys.stderr)

    def project(lon, lat):
        x = PADDING + x_offset + (lon - min_lon) * cos_lat * 111.32 * scale
        y = PADDING + y_offset + (max_lat - lat) * 110.57 * scale
        return (round(x, 1), round(y, 1))

    viewbox_w = SVG_WIDTH + PADDING * 2
    viewbox_h = SVG_HEIGHT + PADDING * 2

    return project, f"0 0 {viewbox_w} {viewbox_h}"


# ---------------------------------------------------------------------------
# SVG PATH GENERATION
# ---------------------------------------------------------------------------

def geom_to_svg_path(geom, project_fn):
    """Convert a Shapely geometry to an SVG path d string."""
    def ring_to_path(coords):
        projected = [project_fn(lon, lat) for lon, lat in coords]
        parts = [f"M{projected[0][0]},{projected[0][1]}"]
        for x, y in projected[1:]:
            parts.append(f"L{x},{y}")
        parts.append("Z")
        return "".join(parts)

    if geom.geom_type == "Polygon":
        return ring_to_path(geom.exterior.coords)
    elif geom.geom_type == "MultiPolygon":
        # Only keep the largest polygon (drop piers, islands, and fragments)
        largest = max(geom.geoms, key=lambda g: g.area)
        return ring_to_path(largest.exterior.coords)
    else:
        raise ValueError(f"Unsupported geometry type: {geom.geom_type}")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    # 1. Download
    data = download_geojson()
    features = data.get("features", [])
    if not features:
        print("ERROR: No features found in GeoJSON", file=sys.stderr)
        sys.exit(1)

    # 2. Detect name field
    name_field = detect_name_field(features[0])
    print(f"  Using name field: '{name_field}'", file=sys.stderr)

    # 3. Group features by app ID
    groups = {}  # app_id -> [geometry, ...]
    park_geom = None
    unmapped = []

    for feature in features:
        name = feature["properties"].get(name_field, "").strip()
        app_id = GEOJSON_TO_APP_ID.get(name)

        if app_id is None:
            unmapped.append(name)
            continue
        if app_id == "__EXCLUDE__":
            continue
        if app_id == "__PARK__":
            park_geom = shape(feature["geometry"])
            continue

        geom = shape(feature["geometry"])
        if not geom.is_valid:
            geom = geom.buffer(0)
        # For MultiPolygons, keep only the main body (drop piers/islands)
        if geom.geom_type == "MultiPolygon":
            geom = max(geom.geoms, key=lambda g: g.area)
        groups.setdefault(app_id, []).append(geom)

    if unmapped:
        print(f"  WARNING: unmapped neighborhoods: {unmapped}", file=sys.stderr)

    # Check coverage
    missing = [aid for aid in APP_IDS if aid not in groups]
    if missing:
        print(f"  WARNING: missing app IDs: {missing}", file=sys.stderr)

    print(f"  Mapped {sum(len(v) for v in groups.values())} features to {len(groups)} app neighborhoods", file=sys.stderr)

    # 4. Merge geometries per app ID
    merged = {}
    for app_id in APP_IDS:
        geoms = groups.get(app_id, [])
        if not geoms:
            continue
        union = unary_union(geoms)
        if not union.is_valid:
            union = union.buffer(0)
        merged[app_id] = union

    # 5. Build projector from all geometries
    all_geoms = list(merged.values())
    if park_geom:
        all_geoms.append(park_geom)
    project, viewbox = make_projector(all_geoms)

    # 6. Simplify and convert to SVG paths
    results = {}
    for app_id in APP_IDS:
        if app_id not in merged:
            continue
        geom = merged[app_id]
        simplified = geom.simplify(TOLERANCE, preserve_topology=True)
        if not simplified.is_valid:
            simplified = simplified.buffer(0)

        path_d = geom_to_svg_path(simplified, project)
        centroid = simplified.representative_point()  # guaranteed inside polygon
        cx, cy = project(centroid.x, centroid.y)

        # Count points
        if simplified.geom_type == "Polygon":
            npts = len(simplified.exterior.coords)
        else:
            npts = sum(len(p.exterior.coords) for p in simplified.geoms)

        results[app_id] = {
            "path": path_d,
            "centroid_x": cx,
            "centroid_y": cy,
            "num_points": npts,
        }
        print(f"  {app_id}: {npts} points, centroid ({cx}, {cy})", file=sys.stderr)

    # 7. SF outline from union of all
    all_union = unary_union(list(merged.values()))
    if park_geom:
        all_union = unary_union([all_union, park_geom])
    outline_simplified = all_union.simplify(OUTLINE_TOLERANCE, preserve_topology=True)
    if not outline_simplified.is_valid:
        outline_simplified = outline_simplified.buffer(0)
    # Keep only the main peninsula (largest polygon)
    if outline_simplified.geom_type == "MultiPolygon":
        outline_simplified = max(outline_simplified.geoms, key=lambda g: g.area)
    outline_path = geom_to_svg_path(outline_simplified, project)
    outline_npts = len(outline_simplified.exterior.coords)
    print(f"  SF_OUTLINE: {outline_npts} points", file=sys.stderr)

    # 8. Golden Gate Park
    ggp_path = ""
    ggp_centroid = None
    if park_geom:
        park_simplified = park_geom.simplify(TOLERANCE, preserve_topology=True)
        ggp_path = geom_to_svg_path(park_simplified, project)
        pc = park_simplified.representative_point()
        ggp_centroid = project(pc.x, pc.y)
        print(f"  Golden Gate Park: {len(park_simplified.exterior.coords)} points", file=sys.stderr)

    # 9. Golden Gate Bridge endpoints
    bridge_south = project(-122.4745, 37.8080)
    bridge_north = project(-122.4782, 37.8325)

    # 10. Output JavaScript
    print()
    print("// ============================================")
    print("// GENERATED BY scripts/generate_polygons.py")
    print("// Source: DataSF Analysis Neighborhoods (p5b7-5n3h)")
    print("// ============================================")
    print()
    print(f'// SVG viewBox: "{viewbox}"')
    print()
    print(f'const SF_OUTLINE = "{outline_path}";')
    print()

    if ggp_path:
        print(f'const GGP_PATH = "{ggp_path}";')
        if ggp_centroid:
            print(f'// GGP label centroid: ({ggp_centroid[0]}, {ggp_centroid[1]})')
        print()

    print(f'// Golden Gate Bridge line: x1={bridge_south[0]} y1={bridge_south[1]} x2={bridge_north[0]} y2={bridge_north[1]}')
    print()

    print("// Neighborhood paths and centroids:")
    print("// Paste these into NEIGHBORHOODS config, replacing the 'polygon' property")
    print()
    for app_id in APP_IDS:
        if app_id not in results:
            print(f"// WARNING: {app_id} has no data!")
            continue
        r = results[app_id]
        print(f'  // {app_id}: {r["num_points"]} points')
        print(f'  // centroid: {{x: {r["centroid_x"]}, y: {r["centroid_y"]}}}')
        print(f'  // path: "{r["path"]}"')
        print()

    # Total size estimate
    total_chars = sum(len(r["path"]) for r in results.values())
    print(f"// Total path data: {total_chars} characters ({total_chars/1024:.1f} KB)", file=sys.stderr)
    print(f"// Outline: {len(outline_path)} characters", file=sys.stderr)


if __name__ == "__main__":
    main()
