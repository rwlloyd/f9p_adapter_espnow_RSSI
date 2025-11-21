"""
GSTools-based Ordinary Kriging heatmap generator for RoboShepherd
Compatible with NumPy 2+ (uses gstools, which supports newer numpy)

Usage (example):
    python heatmap_gstools.py --csv ./csv/RIH-all.csv --out gps_heatmap_gstools.html --grid 30

Outputs: a Folium HTML heatmap file (kriged RSSI -> positive weights).

Dependencies (also provided in requirements.txt):
    gstools, pyproj, pandas, folium, numpy

Notes:
- The script projects lat/lon -> WebMercator (EPSG:3857) for metric kriging.
- It attempts to estimate a variogram automatically and fit a model. If that fails,
  it falls back to reasonable defaults.
- The script includes compatibility fallbacks for different gstools versions.
"""

import argparse
import sys
import numpy as np
import pandas as pd
from pyproj import Transformer
import folium
from folium.plugins import HeatMap

# Try to import gstools and provide clear error if missing
try:
    import gstools as gs
except Exception:
    print("Error importing gstools. Please install it: pip install gstools")
    raise


def load_csv(path):
    # Try to detect columns similarly to existing scripts: expect rssi, lat, lon
    df = pd.read_csv(path, header=None)
    # Common patterns: some CSVs in this repo appear to have columns: rssi, lat, lon, alt, heading
    if df.shape[1] >= 3:
        df = df.iloc[:, :5]
        df.columns = ["rssi", "lat", "lon", "alt", "heading"][: df.shape[1]]
    else:
        raise ValueError("CSV must contain at least three columns: rssi, lat, lon")

    df = df.dropna(subset=["rssi", "lat", "lon"])  # drop incomplete rows
    df["lat"] = df["lat"].astype(float)
    df["lon"] = df["lon"].astype(float)
    df["rssi"] = df["rssi"].astype(float)
    return df


def project_to_meters(df):
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
    xs, ys = transformer.transform(df["lon"].values, df["lat"].values)
    return np.asarray(xs), np.asarray(ys)


def build_grid(x, y, grid_res_m):
    minx, maxx = np.min(x), np.max(x)
    miny, maxy = np.min(y), np.max(y)
    # pad slightly to avoid edge clipping
    padx = grid_res_m * 1
    pady = grid_res_m * 1
    gx = np.arange(minx - padx, maxx + padx + 1e-6, grid_res_m)
    gy = np.arange(miny - pady, maxy + pady + 1e-6, grid_res_m)
    gridx, gridy = np.meshgrid(gx, gy)
    return gx, gy, gridx, gridy


def fit_variogram(x, y, vals, max_dist=None, bin_num=15):
    # Estimate empirical variogram with fallbacks for different gstools versions
    coords = (x, y)
    if max_dist is None:
        # max distance: half of diagonal
        max_dist = np.hypot(x.max() - x.min(), y.max() - y.min()) / 2.0
    try:
        print("Estimating empirical variogram...")
        # gstools API changed over versions; try a few common call signatures
        bins = None
        vario = None
        called = False
        # Try named kw first
        try:
            bins, vario = gs.vario_estimate(coords, vals, max_dist=max_dist, bin_num=bin_num)
            called = True
        except TypeError:
            try:
                bins, vario = gs.vario_estimate(coords, vals, max_dist=max_dist, bins=bin_num)
                called = True
            except TypeError:
                try:
                    # positional fallback
                    bins, vario = gs.vario_estimate(coords, vals, bin_num)
                    called = True
                except Exception:
                    # give up; let outer except handle
                    called = False

        if not called:
            raise RuntimeError("vario_estimate call failed for available gstools API")

        # Try to fit a model automatically
        print("Fitting variogram model...")
        try:
            fit = gs.vario_fit(bins, vario)
        except Exception:
            # some gstools versions use different fit helpers; try building a reasonable model
            fit = None

        # vario_fit may return a CovModel instance (depending on gstools version) or parameters
        if fit is not None and isinstance(fit, gs.CovModel):
            model = fit
        else:
            # If vario_fit returned parameters or failed, derive a fallback from empirical variogram
            sill = float(np.nanmax(vario)) if vario is not None else float(np.nanvar(vals))
            rng = float(bins[np.nanargmax(vario)]) if (vario is not None and np.any(~np.isnan(vario))) else max_dist / 3.0
            model = gs.Exponential(dim=2, var=sill, len_scale=max(rng, 1.0))
        print("Variogram fit done.")
        return model
    except Exception as e:
        print("Variogram estimation/fit failed, falling back to default model. Error:", e)
        # Fallback: use exponential with variance from data and length scale ~ 1/5 of diagonal
        sill = np.nanvar(vals)
        diag = np.hypot(x.max() - x.min(), y.max() - y.min())
        length = max(diag / 5.0, 1.0)
        model = gs.Exponential(dim=2, var=float(sill), len_scale=float(length))
        print(f"Fallback model: Exponential var={sill:.2f} len_scale={length:.1f}")
        return model


def krige_with_gstools(model, x, y, vals, gx, gy, gridx, gridy):
    # Try SRF conditional simulation / kriging pathway, with several calling patterns
    cond_pos = np.column_stack((x, y))
    try:
        print("Attempting SRF conditional kriging (gstools.SRF)...")
        srf = gs.SRF(model, mean=float(np.nanmean(vals)))
        # Try several calling conventions for SRF.structured / SRF.__call__
        try:
            field = srf.structured([gx, gy], cond_pos=cond_pos, cond_val=vals, mode="conditional")
        except TypeError:
            try:
                field = srf.structured([gx, gy], cond_pos=cond_pos, cond_val=vals)
            except TypeError:
                # Some versions expect cond_pos/cond_val as separate positional args
                field = srf.structured([gx, gy], cond_pos, vals)
        print("SRF conditional kriging success.")
        return np.asarray(field)
    except Exception as e1:
        print("SRF conditional kriging failed:", e1)
        # Try alternative SRF call without explicit mode
        try:
            print("Attempting SRF.structured with default mode...")
            srf = gs.SRF(model, mean=float(np.nanmean(vals)))
            try:
                field = srf.structured([gx, gy], cond_pos=cond_pos, cond_val=vals)
            except TypeError:
                field = srf.structured([gx, gy], cond_pos, vals)
            print("SRF structured (default) success.")
            return np.asarray(field)
        except Exception as e2:
            print("SRF fallback also failed:", e2)

    # Try krige.Ordinary interface
    try:
        print("Attempting krige.Ordinary interface...")
        ok = gs.krige.Ordinary(model, cond_pos=cond_pos, cond_val=vals)
        # Call kriging on the grid. Some gstools versions accept a tuple of 1D axes, others expect meshgrids.
        try:
            res = ok((gx, gy))
        except Exception:
            # try passing meshgrid arrays
            res = ok((gridx, gridy))
        # res may be field or (field, var). Handle both.
        if isinstance(res, tuple) and len(res) == 2:
            field, var = res
        else:
            field = res
        field = np.asarray(field)
        # Ensure field has shape (ny, nx). If shapes mismatch, try reshape or transpose.
        ny, nx = len(gy), len(gx)
        if field.shape != (ny, nx):
            # If it's a flat array with correct number of elements, reshape it
            if field.ndim == 1 and field.size == ny * nx:
                field = field.reshape((ny, nx))
            # Try transposing
            elif field.T.shape == (ny, nx):
                field = field.T
            else:
                print(f"Warning: kriging result shape {field.shape} doesn't match expected {(ny,nx)}")
        print("krige.Ordinary success.")
        return field
    except Exception as e3:
        print("krige.Ordinary failed:", e3)

    raise RuntimeError("All gstools kriging attempts failed. Please check your gstools version and API; see script notes.")


def to_latlon(xs, ys):
    transformer_inv = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
    lons, lats = transformer_inv.transform(xs, ys)
    return lats, lons


def grid_to_heatmap_data(field, gridx, gridy):
    # field shape expected (ny, nx); gridx, gridy are structured arrays
    flat_x = gridx.flatten()
    flat_y = gridy.flatten()
    flat_val = np.asarray(field).flatten()
    # Convert RSSI (negative typical) to positive folium weight scale
    # We'll rescale linearly so that weights are in [0, 1]
    # But keep values consistent: assume RSSI in range [-120, -20]
    v = flat_val
    # Clip extreme values
    v_clipped = np.clip(v, -140.0, -10.0)
    # Map to 0..1
    weights = (v_clipped - (-140.0)) / (130.0)
    weights = np.nan_to_num(weights, nan=0.0)
    return flat_x, flat_y, weights


def create_folium_map(lat_center, lon_center, heatmap_data, out_html, radius=15, blur=12, satellite=False):
    # Base map (OpenStreetMap). Add satellite tiles as an optional toggleable layer.
    m = folium.Map(location=[lat_center, lon_center], zoom_start=15, tiles="OpenStreetMap", control_scale=True)

    if satellite:
        # Esri World Imagery (satellite) - commonly available and free for light use
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Esri",
            name="Esri.WorldImagery",
            overlay=False,
            control=True,
        ).add_to(m)

    # Put heatmap into a FeatureGroup so it can be toggled in the layer control
    fg = folium.FeatureGroup(name="Kriged RSSI Heatmap", overlay=True, show=True)
    HeatMap(heatmap_data, radius=radius, blur=blur, min_opacity=0.25, max_zoom=20).add_to(fg)
    fg.add_to(m)

    folium.LayerControl().add_to(m)
    m.save(out_html)


def main():
    parser = argparse.ArgumentParser(description="GSTools kriging heatmap generator")
    parser.add_argument("--csv", "-c", default="./csv/RIH-all.csv", help="input csv file (rssi,lat,lon,...")
    parser.add_argument("--out", "-o", default="gps_heatmap_gstools.html", help="output html file")
    parser.add_argument("--grid", "-g", default=30, type=float, help="grid spacing in meters (default: 30)")
    parser.add_argument("--radius", default=20, type=int, help="Folium HeatMap point radius")
    parser.add_argument("--satellite", action="store_true", help="Add Esri satellite tiles as a toggleable layer")
    args = parser.parse_args()

    df = load_csv(args.csv)
    print(f"Loaded {len(df)} input rows from {args.csv}")

    x, y = project_to_meters(df)
    vals = df["rssi"].values

    gx, gy, gridx, gridy = build_grid(x, y, grid_res_m=float(args.grid))
    print(f"Grid constructed: {len(gx)} x {len(gy)} -> {gridx.size} cells")

    # Fit variogram / covariance model
    model = fit_variogram(x, y, vals, max_dist=None, bin_num=20)

    # Perform kriging (gstools)
    field = krige_with_gstools(model, x, y, vals, gx, gy, gridx, gridy)

    # Convert grid XY back to lat/lon
    flat_x = gridx.flatten()
    flat_y = gridy.flatten()
    lats, lons = to_latlon(flat_x, flat_y)

    # Build heatmap weights (0..1)
    _, _, weights = grid_to_heatmap_data(field, gridx, gridy)

    heatmap_data = [[float(lat), float(lon), float(w)] for lat, lon, w in zip(lats, lons, weights) if w > 0]
    print(f"Prepared {len(heatmap_data)} weighted points for folium heatmap")

    # Center map at median GPS point
    lat_c = float(df["lat"].median())
    lon_c = float(df["lon"].median())

    create_folium_map(lat_c, lon_c, heatmap_data, args.out, radius=args.radius, satellite=args.satellite)
    print(f"Saved kriged folium heatmap to: {args.out}")


if __name__ == "__main__":
    main()
