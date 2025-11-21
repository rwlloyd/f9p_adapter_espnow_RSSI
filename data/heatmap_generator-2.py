# Script to generate a heatmap from averaged GPS RSSI data
# r.w.lloyd, Modified by ChatGPT to bin data, Nov 2025

import folium
from folium.plugins import HeatMap
import pandas as pd
import numpy as np
from pyproj import Transformer

# ------------------
# Load CSV
# ------------------
df = pd.read_csv("./csv/RIH-all.csv", header=None,
                 names=["rssi", "lat", "lon", "alt", "heading"])

df["lat"] = df["lat"].astype(float)
df["lon"] = df["lon"].astype(float)
df["rssi"] = df["rssi"].astype(float)

# ------------------
# Project WGS84 → Web Mercator (meters)
# ------------------
transformer_fwd = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
df["x"], df["y"] = transformer_fwd.transform(df["lon"].values, df["lat"].values)

# ------------------
# Grid parameters (adjust to taste)
# ------------------
cell_size_m = 5   # 30m grid cells   <<< CHANGE THIS IF YOU WANT
min_x, max_x = df["x"].min(), df["x"].max()
min_y, max_y = df["y"].min(), df["y"].max()

# ------------------
# Assign each point to a grid cell
# ------------------
df["gx"] = ((df["x"] - min_x) // cell_size_m).astype(int)
df["gy"] = ((df["y"] - min_y) // cell_size_m).astype(int)

# ------------------
# Aggregate: mean RSSI per grid cell
# ------------------
agg = df.groupby(["gx", "gy"]).agg(
    mean_rssi=("rssi", "mean"),
    count=("rssi", "size"),
    x_center=("x", "mean"),
    y_center=("y", "mean")
).reset_index()

# Optional: throw away cells with too few readings (reduces noise)
agg = agg[agg["count"] >= 2]

# ------------------
# Convert cell center positions back to lat/lon
# ------------------
transformer_inv = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
agg["lon"], agg["lat"] = transformer_inv.transform(
    agg["x_center"].values, agg["y_center"].values
)

# ------------------
# Convert RSSI to positive weight for Folium
# ------------------
# Example: RSSI -30 → weight 70; RSSI -80 → weight 20
agg["weight"] = agg["mean_rssi"] + 100

# ------------------
# Prepare heatmap data
# ------------------
heat_data = agg[["lat", "lon", "weight"]].values.tolist()

# ------------------
# Create map
# ------------------
m = folium.Map(location=[53.26831, -0.52984], zoom_start=15)

HeatMap(
    heat_data,
    radius=25,      # larger because data is now coarser
    blur=20,
    max_zoom=20,
    min_opacity=0.4
).add_to(m)

m.save("gps_heatmap-RIH-all-5m-averaged.html")
print("Saved to gps_heatmap-averaged.html")
