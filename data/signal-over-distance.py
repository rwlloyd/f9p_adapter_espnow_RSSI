import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import radians, sin, cos, sqrt, atan2

# ---------------------------------------------------------
# USER SETTINGS
# ---------------------------------------------------------
csv_file = "./csv/RIH-all.csv"

# Set your base station location
BASE_LAT = 53.268339893585555    # <-- update these
BASE_LON = -0.5298533178776605     # <-- update these

# ---------------------------------------------------------
# FUNCTIONS
# ---------------------------------------------------------

# Haversine distance in meters
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lon2 - lon1)

    a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlambda/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1-a))

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
# Assumes columns: RSSI, lat, lon, alt, heading  (like your earlier sample)
df = pd.read_csv(csv_file, header=None, names=["rssi","lat","lon","alt","heading"])

# ---------------------------------------------------------
# COMPUTE DISTANCE FROM BASE
# ---------------------------------------------------------
df["distance_m"] = df.apply(lambda row: 
    haversine(BASE_LAT, BASE_LON, row["lat"], row["lon"]), axis=1)

# ---------------------------------------------------------
# PLOT: Signal Strength vs Distance
# ---------------------------------------------------------
plt.figure(figsize=(10,6))
plt.scatter(df["distance_m"], df["rssi"], s=12)
plt.xlabel("Distance from base station (meters)")
plt.ylabel("Signal Strength (RSSI)")
plt.title("RSSI vs Distance from Base Station")
plt.grid(True)
plt.show()