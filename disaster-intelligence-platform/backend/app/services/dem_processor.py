"""
DEM (Digital Elevation Model) processing service
Uses SRTM 30m data for real elevation, slope, and low-lying index per ward
"""
import os
import logging
import math
from typing import Dict, Optional, Tuple
from datetime import datetime

from app.db.config import settings

logger = logging.getLogger(__name__)

# Try importing raster processing libraries
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import rasterio
    from rasterio.mask import mask as rasterio_mask
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False


class DEMProcessor:
    """
    SRTM DEM processor for computing per-ward terrain statistics
    
    Computes:
    - Mean elevation (m)
    - Mean slope (degrees) 
    - Min/max elevation
    - Low-lying index (0-1, higher = more low-lying relative to city)
    
    Falls back to realistic estimated values if DEM file not available.
    """

    def __init__(self, dem_path: str = None):
        self.dem_path = dem_path or os.path.join(settings.SRTM_DATA_DIR, "pune_dem.tif")
        self.dem_data = None
        self.dem_transform = None
        self.dem_crs = None
        self.city_stats = None

    def load_dem(self) -> bool:
        """Load DEM raster if available"""
        if not HAS_RASTERIO or not HAS_NUMPY:
            logger.warning("rasterio/numpy not available, using fallback elevation data")
            return False

        if not os.path.exists(self.dem_path):
            logger.warning(f"DEM file not found at {self.dem_path}, using fallback data")
            return False

        try:
            with rasterio.open(self.dem_path) as src:
                self.dem_data = src.read(1)
                self.dem_transform = src.transform
                self.dem_crs = src.crs
                self.dem_nodata = src.nodata or -9999

                # Compute city-wide stats for normalization
                valid = self.dem_data[self.dem_data != self.dem_nodata]
                self.city_stats = {
                    "min": float(np.min(valid)),
                    "max": float(np.max(valid)),
                    "mean": float(np.mean(valid)),
                    "std": float(np.std(valid)),
                }
                logger.info(f"DEM loaded: {self.dem_data.shape}, elevation range: {self.city_stats['min']:.0f}-{self.city_stats['max']:.0f}m")
                return True

        except Exception as e:
            logger.error(f"Failed to load DEM: {e}")
            return False

    def compute_ward_stats(self, centroid_lat: float, centroid_lon: float,
                            ward_name: str = "", geometry=None) -> Dict:
        """
        Compute DEM statistics for a ward

        If DEM is loaded: extract from raster using ward geometry or centroid buffer
        Otherwise: use realistic estimated values based on Pune's topography
        """
        if self.dem_data is not None and HAS_NUMPY:
            return self._compute_from_raster(centroid_lat, centroid_lon, geometry)
        else:
            return self._estimate_from_topography(centroid_lat, centroid_lon, ward_name)

    def _compute_from_raster(self, lat: float, lon: float, geometry=None) -> Dict:
        """Extract elevation stats from DEM raster"""
        try:
            import numpy as np

            if geometry is not None:
                # Use actual ward polygon to mask raster
                with rasterio.open(self.dem_path) as src:
                    out_image, _ = rasterio_mask(src, [geometry], crop=True)
                    valid = out_image[0][out_image[0] != self.dem_nodata]
            else:
                # Use centroid + buffer (approx 1km radius)
                row, col = self._latlon_to_pixel(lat, lon)
                buffer_px = 33  # ~1km at 30m resolution
                r_min = max(0, row - buffer_px)
                r_max = min(self.dem_data.shape[0], row + buffer_px)
                c_min = max(0, col - buffer_px)
                c_max = min(self.dem_data.shape[1], col + buffer_px)

                patch = self.dem_data[r_min:r_max, c_min:c_max]
                valid = patch[patch != self.dem_nodata]

            if len(valid) == 0:
                return self._estimate_from_topography(lat, lon, "")

            mean_elev = float(np.mean(valid))
            min_elev = float(np.min(valid))
            max_elev = float(np.max(valid))

            # Compute slope from elevation gradient
            slope = self._compute_slope(valid, lat, lon) if len(valid) > 4 else 2.0

            # Low-lying index (relative to city)
            if self.city_stats:
                city_range = self.city_stats["max"] - self.city_stats["min"]
                if city_range > 0:
                    low_lying_index = 1.0 - (mean_elev - self.city_stats["min"]) / city_range
                else:
                    low_lying_index = 0.5
            else:
                low_lying_index = 0.5

            return {
                "elevation_m": round(mean_elev, 1),
                "min_elevation_m": round(min_elev, 1),
                "max_elevation_m": round(max_elev, 1),
                "mean_slope": round(slope, 2),
                "low_lying_index": round(max(0, min(1, low_lying_index)), 3),
                "source": "srtm_dem",
                "computed_at": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Raster extraction failed: {e}")
            return self._estimate_from_topography(lat, lon, "")

    def _estimate_from_topography(self, lat: float, lon: float, ward_name: str) -> Dict:
        """
        Estimate elevation from Pune's known topography.
        Pune slopes from west (Sahyadri foothills, ~650m) to east (plains, ~530m).
        River areas (Mutha/Mula confluence) are lower.
        """
        # Base elevation model for Pune (west-to-east gradient)
        # Pune center: ~18.52°N, 73.86°E, ~560m ASL
        base_elevation = 560.0

        # West-east gradient: ~120m drop over 20km
        lon_offset = lon - 73.86
        elevation_gradient = -120 * (lon_offset / 0.18)  # 0.18° ≈ 20km at this latitude
        elevation = base_elevation + elevation_gradient

        # River valley depression (Mula-Mutha confluence area)
        river_lat, river_lon = 18.51, 73.85
        dist_to_river = math.sqrt((lat - river_lat) ** 2 + (lon - river_lon) ** 2)
        if dist_to_river < 0.05:  # ~5km
            elevation -= 20 * (1 - dist_to_river / 0.05)

        # Hill areas (Vetal, Sinhagad, Parvati hills)
        hills = [
            (18.508, 73.825, 30),   # Vetal tekdi
            (18.523, 73.838, 15),   # Parvati hill
            (18.497, 73.832, 20),   # Law College hill
        ]
        for h_lat, h_lon, h_gain in hills:
            dist = math.sqrt((lat - h_lat) ** 2 + (lon - h_lon) ** 2)
            if dist < 0.03:
                elevation += h_gain * (1 - dist / 0.03)

        elevation = max(530, min(680, elevation))

        # Slope estimate: steeper near hills, flat in plains
        mean_slope = 2.0 + abs(elevation - 560) / 30

        # Low-lying index (lower elevation relative to city range 530-680)
        low_lying_index = 1.0 - (elevation - 530) / 150

        return {
            "elevation_m": round(elevation, 1),
            "min_elevation_m": round(elevation - 10, 1),
            "max_elevation_m": round(elevation + 15, 1),
            "mean_slope": round(mean_slope, 2),
            "low_lying_index": round(max(0, min(1, low_lying_index)), 3),
            "source": "topographic_model",
            "computed_at": datetime.now().isoformat(),
        }

    def _latlon_to_pixel(self, lat: float, lon: float) -> Tuple[int, int]:
        """Convert lat/lon to raster pixel coordinates"""
        if self.dem_transform is None:
            return 0, 0
        col = int((lon - self.dem_transform.c) / self.dem_transform.a)
        row = int((lat - self.dem_transform.f) / self.dem_transform.e)
        return row, col

    def _compute_slope(self, elevation_patch, lat: float, lon: float) -> float:
        """Compute mean slope from elevation patch"""
        try:
            import numpy as np
            # Reshape to 2D if needed
            side = int(np.sqrt(len(elevation_patch)))
            if side < 3:
                return 2.0
            grid = elevation_patch[:side * side].reshape(side, side)

            # Gradient in x and y (30m cell size)
            cell_size = 30.0
            dy, dx = np.gradient(grid, cell_size)
            slope_rad = np.arctan(np.sqrt(dx ** 2 + dy ** 2))
            slope_deg = np.degrees(slope_rad)
            return float(np.mean(slope_deg))
        except Exception:
            return 2.0

    @staticmethod
    def get_srtm_download_command() -> str:
        """Get command to download SRTM data for Pune"""
        return """
# Download SRTM 30m DEM for Pune area (Tile N18E073)
# Option 1: Using earthdata (requires free account at https://urs.earthdata.nasa.gov)
mkdir -p data/srtm
wget -O data/srtm/N18E073.hgt.zip \\
  "https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/N18E073.SRTMGL1.hgt.zip"
unzip data/srtm/N18E073.hgt.zip -d data/srtm/

# Option 2: Using opentopography.org (no account needed)
# Download from: https://portal.opentopography.org/raster?opentopoID=OTSRTM.082015.4326.1

# Convert to GeoTIFF
gdal_translate -of GTiff data/srtm/N18E073.hgt data/srtm/pune_dem.tif
"""


# Global instance
dem_processor = DEMProcessor()
