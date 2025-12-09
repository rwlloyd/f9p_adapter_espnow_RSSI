import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from math import radians, sin, cos, sqrt, atan2, degrees
from mpl_toolkits.mplot3d import Axes3D

# ---------------------------------------------------------
# USER SETTINGS
# ---------------------------------------------------------

csv_file = "./csv/RIH-all.csv"

# Set your base station location
BASE_LAT = 53.268339893585555    # <-- update these
BASE_LON = -0.5298533178776605     # <-- update these

# Slicing
ANGLE_STEP = 5
SLICE_HALF_WIDTH = ANGLE_STEP / 2  # ± degrees around each central slice

# Smoothing options
USE_MOVING_AVERAGE = False
USE_SAVGOL = True          # toggle smoothing on/off
MOVING_AVG_WINDOW = 5      # points
SAVGOL_WINDOW = 11         # must be odd
SAVGOL_POLY = 3

# ---------------------------------------------------------
# FUNCTIONS
# ---------------------------------------------------------

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)
    a = sin(dphi/2)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1-a))

def bearing(lat1, lon1, lat2, lon2):
    phi1, phi2 = radians(lat1), radians(lat2)
    dlon = radians(lon2 - lon1)
    x = sin(dlon) * cos(phi2)
    y = cos(phi1)*sin(phi2) - sin(phi1)*cos(phi2)*cos(dlon)
    return (degrees(atan2(x, y)) + 360) % 360

def angle_diff(a, b):
    d = abs(a - b) % 360
    return min(d, 360 - d)

def moving_average(x, w):
    return np.convolve(x, np.ones(w), "same") / w

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

df = pd.read_csv(csv_file, header=None,
                 names=["rssi", "lat", "lon", "alt", "heading"])

# ---------------------------------------------------------
# DISTANCE & BEARING
# ---------------------------------------------------------

df["distance_m"] = df.apply(lambda r:
    haversine(BASE_LAT, BASE_LON, r["lat"], r["lon"]), axis=1)

df["bearing_deg"] = df.apply(lambda r:
    bearing(BASE_LAT, BASE_LON, r["lat"], r["lon"]), axis=1)

# ---------------------------------------------------------
# 3D STACKED PLOT
# ---------------------------------------------------------

fig = plt.figure(figsize=(14, 10))
ax = fig.add_subplot(111, projection='3d')

angle_bins = np.arange(0, 360, ANGLE_STEP)

for a in angle_bins:
    slice_df = df[df["bearing_deg"].apply(
        lambda b: angle_diff(b, a) <= SLICE_HALF_WIDTH
    )]

    if len(slice_df) < 3:
        continue

    slice_df = slice_df.sort_values("distance_m")

    distances = slice_df["distance_m"].values
    rssi_raw = slice_df["rssi"].values

    # --------------------------
    # Apply smoothing if enabled
    # --------------------------
    if USE_MOVING_AVERAGE:
        rssi_smoothed = moving_average(rssi_raw, MOVING_AVG_WINDOW)
    elif USE_SAVGOL:
        # Ensure valid window
        w = min(SAVGOL_WINDOW, len(rssi_raw) - (len(rssi_raw)+1)%2)
        w = max(w, 5)  # ensure >=5
        if w % 2 == 0:
            w += 1
        rssi_smoothed = savgol_filter(rssi_raw, w, SAVGOL_POLY)
    else:
        rssi_smoothed = rssi_raw

    # plot (distance, heading, smoothed RSSI)
    ax.plot(distances, [a]*len(distances), rssi_smoothed, linewidth=1.0)

ax.set_xlabel("Distance (m)")
ax.set_ylabel("Heading (deg)")
ax.set_zlabel("RSSI (dBm)")
ax.set_title("Stacked Radial RSSI Profiles (Every 5°) — With Optional Smoothing")

plt.tight_layout()
plt.show()
