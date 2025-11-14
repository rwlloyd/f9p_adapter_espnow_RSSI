#Script to generate a heatmap from corrected GPS RSSI data
# r.w.lloyd, Nov 2025

import folium
from folium.plugins import HeatMap
import pandas as pd

# Load CSV
df = pd.read_csv("20251113-all_fixed.csv", header=None,
                 names=["rssi", "lat", "lon", "alt", "heading"])

# Ensure correct data types
df["lat"] = df["lat"].astype(float)
df["lon"] = df["lon"].astype(float)
df["rssi"] = df["rssi"].astype(float)

# rssi is negative (e.g., -30 dBm). HeatMap expects positive weights.
# Convert RSSI to a positive scale: stronger signal → bigger number.
df["weight"] = 100 + df["rssi"]   # invert the scale

# Build heatmap data: [lat, lon, weight]
heat_data = df[["lat", "lon", "weight"]].values.tolist()

# Center map on the average of your data
# m = folium.Map(location=[df["lat"].mean(), df["lon"].mean()], zoom_start=10)
m = folium.Map(location=[53.26831, -0.52984], zoom_start=15)  ## Hardcoded because folium cant handle too high an accuracy

# Add heatmap
HeatMap(
    heat_data,
    radius=20,
    blur=18,
    max_zoom=17,
    min_opacity=0.3
).add_to(m)

m.save("gps_heatmap-all.html")
print("Saved to gps_heatmap.html")

