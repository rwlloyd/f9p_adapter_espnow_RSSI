import pandas as pd
import folium

# Load CSV
df = pd.read_csv("./csv/RIH-all.csv", header=None, names=["rssi", "lat_raw", "lon_raw", "alt_raw", "heading"])

# Convert to proper lat/lon/alt
df["lat"] = df["lat_raw"]
df["lon"] = df["lon_raw"]
df["alt"] = df["alt_raw"] # if in millimetres, otherwise adjust as needed

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
        popup=f"RSSI: {row['rssi']}<br>Heading: {row['heading']}°<br>Alt: {row['alt']:.2f} m"
    ).add_to(m)

m.save("gps_signal_map-RIH-all-20251121.html")
print("✅ Map saved as gps_signal_map.html — open it in your browser!")
