import math

from pyproj import Transformer


class Projection:
    """
    Abstraction for coordinate projection using pyproj.
    Supports transforming between EPSG:4326 (WGS84) and any target CRS
    (e.g., EPSG:3857). Also provides pixel/tile conversion utilities for
    map rendering.
    """

    def __init__(self, crs: str = "EPSG:3857"):
        self.crs = crs
        self._to_proj = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        self._from_proj = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)

    def to_projected(self, lon: float, lat: float):
        """
        Transform lon/lat (EPSG:4326) to projected coordinates (x, y) in the target CRS.
        """
        return self._to_proj.transform(lon, lat)

    def from_projected(self, x: float, y: float):
        """
        Transform projected coordinates (x, y) in the target CRS to lon/lat (EPSG:4326).
        """
        return self._from_proj.transform(x, y)

    def projected_to_pixel(
        self, x: float, y: float, zoom: int, tile_size: int = 256
    ) -> tuple[float, float]:
        """
        Convert projected coordinates to pixel coordinates at a given zoom.
        Only valid for projections with meters as units (e.g., EPSG:3857).
        """
        initial_resolution = 2 * math.pi * 6378137 / tile_size
        resolution = initial_resolution / (2**zoom)
        px = (x + math.pi * 6378137) / resolution
        py = (math.pi * 6378137 - y) / resolution
        return px, py

    def pixel_to_projected(
        self, px: float, py: float, zoom: int, tile_size: int = 256
    ) -> tuple[float, float]:
        """
        Convert pixel coordinates to projected coordinates at a given zoom.
        Only valid for projections with meters as units (e.g., EPSG:3857).
        """
        initial_resolution = 2 * math.pi * 6378137 / tile_size
        resolution = initial_resolution / (2**zoom)
        x = px * resolution - math.pi * 6378137
        y = math.pi * 6378137 - py * resolution
        return x, y

    def lonlat_to_pixel(
        self, lon: float, lat: float, zoom: int, tile_size: int = 256
    ) -> tuple[float, float]:
        """
        Convert lon/lat to pixel coordinates at a given zoom using the
        projection.
        """
        x, y = self.to_projected(lon, lat)
        return self.projected_to_pixel(x, y, zoom, tile_size)

    def pixel_to_lonlat(
        self, px: float, py: float, zoom: int, tile_size: int = 256
    ) -> tuple[float, float]:
        """
        Convert pixel coordinates to lon/lat at a given zoom using the
        projection.
        """
        x, y = self.pixel_to_projected(px, py, zoom, tile_size)
        return self.from_projected(x, y)

    def lonlat_to_tile(
        self, lon: float, lat: float, zoom: int, tile_size: int = 256
    ) -> tuple[float, float]:
        """
        Convert lon/lat to fractional tile coordinates at a given zoom.
        """
        px, py = self.lonlat_to_pixel(lon, lat, zoom, tile_size)
        return px / tile_size, py / tile_size

    def tile_to_lonlat(
        self, xf: float, yf: float, zoom: int, tile_size: int = 256
    ) -> tuple[float, float]:
        """
        Convert fractional tile coordinates to lon/lat at a given zoom.
        """
        px = xf * tile_size
        py = yf * tile_size
        return self.pixel_to_lonlat(px, py, zoom, tile_size)
