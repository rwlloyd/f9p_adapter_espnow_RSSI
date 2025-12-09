# Script to correct the values that are in a weird format straight out of the GPS in the CSV file
#r.w.lloyd Nov 2025

import csv

input_file = "go2-initial-walk.cap"
output_file = "go2-initial-walk.csv"

with open(input_file, "r") as f_in, open(output_file, "w", newline="") as f_out:
    reader = csv.reader(f_in)
    writer = csv.writer(f_out)

    for row in reader:
        if not row:
            continue

        # Parse raw columns
        rssi       = float(row[0])
        lat_raw    = float(row[1])
        lon_raw    = float(row[2])
        alt_raw    = float(row[3])
        heading    = float(row[4])

        # Apply corrections
        rssi_corrected = rssi  # Assuming RSSI is already correct
        lat_corrected = lat_raw / 10_000_000
        lon_corrected = lon_raw / 10_000_000
        alt_corrected = alt_raw / 1000
        heading_corrected = heading  # Assuming heading is already correct

        # Write corrected row
        writer.writerow([
            rssi,
            f"{lat_corrected:.7f}",
            f"{lon_corrected:.7f}",
            f"{alt_corrected:.3f}",
            f"{heading:.2f}"
        ])

print("Finished! Corrected file written to", output_file)
