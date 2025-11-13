import pandas as pd
import folium
import numpy as np

# WGS84 constants
a = 6378137.0          # semi-major axis (m)
e_sq = 6.69437999014e-3  # first eccentricity squared

def ecef_to_lla(x, y, z):
    """Convert ECEF (x, y, z) to latitude, longitude, altitude (WGS84)."""
    b = np.sqrt(a**2 * (1 - e_sq))
    ep = np.sqrt((a**2 - b**2) / b**2)
    p = np.sqrt(x**2 + y**2)
    th = np.arctan2(a * z, b * p)
    lon = np.arctan2(y, x)
    lat = np.arctan2((z + ep**2 * b * np.sin(th)**3),
                     (p - e_sq * a * np.cos(th)**3))
    N = a / np.sqrt(1 - e_sq * np.sin(lat)**2)
    alt = p / np.cos(lat) - N
    lat = np.degrees(lat)
    lon = np.degrees(lon)
    return lat, lon, alt

# Load CSV
df = pd.read_csv("20251113.csv", header=None, names=["rssi", "x", "y", "z", "heading"])

# Convert ECEF to LLA
latitudes, longitudes, altitudes = [], [], []
for _, row in df.iterrows():
    lat, lon, alt = ecef_to_lla(row["x"], row["y"], row["z"])
    latitudes.append(lat)
    longitudes.append(lon)
    altitudes.append(alt)

df["lat"] = latitudes
df["lon"] = longitudes
df["alt"] = altitudes

# Make Folium map centered on average point
m = folium.Map(location=[df["lat"].mean(), df["lon"].mean()], zoom_start=17)

# Normalize RSSI for color mapping
rssi_min, rssi_max = df["rssi"].min(), df["rssi"].max()

for _, row in df.iterrows():
    norm_rssi = (row["rssi"] - rssi_min) / (rssi_max - rssi_min)
    # Map RSSI to a red→green gradient
    r = int(255 * (1 - norm_rssi))
    g = int(255 * norm_rssi)
    color = f"#{r:02x}{g:02x}00"

    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=5,
        color=color,
        fill=True,
        fill_opacity=0.8,
        popup=f"RSSI: {row['rssi']}<br>Heading: {row['heading']}°"
    ).add_to(m)

m.save("gps_signal_map.html")
print("✅ Map saved as gps_signal_map.html — open it in your browser!")
