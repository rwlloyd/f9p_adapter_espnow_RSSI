import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import radians, sin, cos, sqrt, atan2, degrees

# ---------------------------------------------------------
# USER SETTINGS
# ---------------------------------------------------------

csv_file = "./csv/RIH-all.csv"

# Base station coordinates
BASE_LAT = 53.268339893585555    # <-- update these
BASE_LON = -0.5298533178776605     # <-- update these

# Radial slice direction
TARGET_HEADING = 180       # degrees (0=north, 90=east)
HEADING_TOLERANCE = 2     # degrees each side

# ---------------------------------------------------------
# FUNCTIONS
# ---------------------------------------------------------

# Haversine distance in meters
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)

    a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlambda/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1-a))

# Bearing from base station to a point
def bearing(lat1, lon1, lat2, lon2):
    phi1, phi2 = radians(lat1), radians(lat2)
    dlon = radians(lon2 - lon1)

    x = sin(dlon) * cos(phi2)
    y = cos(phi1)*sin(phi2) - sin(phi1)*cos(phi2)*cos(dlon)

    brng = atan2(x, y)
    brng = (degrees(brng) + 360) % 360
    return brng

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

df = pd.read_csv(csv_file, header=None, names=["rssi", "lat", "lon", "alt", "heading"])

# ---------------------------------------------------------
# COMPUTE DISTANCE & BEARING FROM BASE
# ---------------------------------------------------------

df["distance_m"] = df.apply(lambda row:
    haversine(BASE_LAT, BASE_LON, row["lat"], row["lon"]), axis=1)

df["bearing_deg"] = df.apply(lambda row:
    bearing(BASE_LAT, BASE_LON, row["lat"], row["lon"]), axis=1)

# ---------------------------------------------------------
# FILTER POINTS ALONG THE DESIRED HEADING
# ---------------------------------------------------------

def angle_diff(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)

df_slice = df[df["bearing_deg"].apply(lambda b:
    angle_diff(b, TARGET_HEADING) <= HEADING_TOLERANCE)]

# ---------------------------------------------------------
# PLOT SLICE
# ---------------------------------------------------------

plt.figure(figsize=(10,6))
plt.scatter(df_slice["distance_m"], df_slice["rssi"], s=15)
plt.xlabel("Distance from base (m)")
plt.ylabel("Signal Strength (RSSI)")
plt.title(f"RSSI vs Distance Along {TARGET_HEADING}° ± {HEADING_TOLERANCE}°")
plt.grid(True)
plt.show()

# If you want to print number of points found:
print(f"Points in radial slice: {len(df_slice)}")
