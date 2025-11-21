# Script to generate a kriging-smoothed heatmap from GPS RSSI data
# r.w.lloyd, updated with kriging by ChatGPT, Nov 2025

import folium
from folium.plugins import HeatMap
import pandas as pd
import numpy as np
from pyproj import Transformer
from pykrige.ok import OrdinaryKriging

# -----------------------------
# Load CSV
# -----------------------------
df = pd.read_csv("./csv/RIH-all.csv", header=None,
                 names=["rssi", "lat", "lon", "alt", "heading"])

df["lat"] = df["lat"].astype(float)
df["lon"] = df["lon"].astype(float)
df["rssi"] = df["rssi"].astype(float)

# -----------------------------
# Project WGS84 -> Web Mercator (meters)
# -----------------------------
transformer_fwd = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
df["x"], df["y"] = transformer_fwd.transform(df["lon"].values, df["lat"].values)

x = df["x"].values
y = df["y"].values
z = df["rssi"].values

print(f"Loaded {len(df)} points for kriging...")

# -----------------------------
# Build Kriging Model
# -----------------------------
# Other valid variogram models: 'sperical', 'exponential', 'gaussian', 'linear', 'power'
OK = OrdinaryKriging(
    x, y, z,
    variogram_model="spherical",
    verbose=False,
    enable_plotting=False,
)

# -----------------------------
# Create interpolation grid (meters)
# -----------------------------
# Grid resolution controls smoothness: 30–150m depending on dataset
grid_res = 30  # meters

grid_x = np.arange(np.min(x), np.max(x), grid_res)
grid_y = np.arange(np.min(y), np.max(y), grid_res)

gridx, gridy = np.meshgrid(grid_x, grid_y)

print(f"Grid size: {len(grid_x)} x {len(grid_y)} = {gridx.size} cells")

# -----------------------------
# Perform kriging interpolation
# -----------------------------
z_pred, ss = OK.execute("grid", grid_x, grid_y)

# Flatten arrays for conversion back to lat/lon
flat_x = gridx.flatten()
flat_y = gridy.flatten()
flat_pred = z_pred.flatten()

# -----------------------------
# Convert grid back to lat/lon
# -----------------------------
transformer_inv = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
flat_lon, flat_lat = transformer_inv.transform(flat_x, flat_y)

# -----------------------------
# Build heatmap data (lat, lon, weight)
# -----------------------------
heatmap_data = []
for la, lo, sig in zip(flat_lat, flat_lon, flat_pred):
    # Convert RSSI (negative) to a positive Folium weight
    weight = sig + 100
    heatmap_data.append([la, lo, weight])

print(f"Generated {len(heatmap_data)} kriged points for heatmap")

# -----------------------------
# Create Folium Map
# -----------------------------
# Hardcoded centre (because folium freaks out if coordinate precision is too high)
m = folium.Map(location=[53.26831, -0.52984], zoom_start=15)

HeatMap(
    heatmap_data,
    radius=20,        # grid is coarse, so use bigger radius
    blur=15,
    min_opacity=0.35,
    max_zoom=20
).add_to(m)

m.save("gps_heatmap_30m_spherical_kriging.html")
print("Saved: gps_heatmap_kriging.html")
