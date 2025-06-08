"""Data models for tkmap: tile coordinates, screen points, map dimensions, and more."""

import math
from dataclasses import dataclass

MIN_LATITUDE = -90
MAX_LATITUDE = 90


@dataclass(frozen=True)
class TileCoord:
    """Tile coordinate in XYZ tiling scheme, with floating point precision."""

    z: int
    xf: float
    yf: float

    @property
    def x(self) -> int:
        """Get the x coordinate as an integer."""
        return int(self.xf)

    @property
    def y(self) -> int:
        """Get the y coordinate as an integer."""
        return int(self.yf)

    @property
    def lat(self) -> float:
        """Latitude from tile coordinates using inverse Web Mercator projection."""
        n = math.pi - 2.0 * math.pi * self.yf / (2**self.z)
        return math.degrees(math.atan(math.sinh(n)))

    @property
    def lon(self) -> float:
        """Return the longitude from the tile coordinates, wrapped to [-180, 180)."""
        return ((self.xf / (2**self.z)) * 360 - 180 + 180) % 360 - 180

    @property
    def lonlat(self) -> "LonLat":
        """Longitude and latitude as a LonLat object."""
        return LonLat(lon=self.lon, lat=self.lat)

    def __repr__(self) -> str:
        """Return a string representation of the tile coordinate."""
        return (
            f"TileCoord(z={self.z}, xf={self.xf}, yf={self.yf}, "
            f"lon={self.lon}, lat={self.lat})"
        )


@dataclass(frozen=True)
class ScreenPoint:
    """A point on the screen in pixel coordinates."""

    x: int
    y: int

    def to_tile(self, zoom: int, tile_size: int = 256) -> TileCoord:
        """Convert screen coordinates to tile coordinates at a given zoom."""
        xf = self.x / tile_size
        yf = self.y / tile_size
        return TileCoord(z=zoom, xf=xf, yf=yf)


@dataclass(frozen=True)
class TileInstance:
    """A tile and its associated screen position and item ID."""

    tile: TileCoord
    screen: ScreenPoint
    item_id: int


@dataclass(frozen=True)
class CenterTile:
    """The center tile's floating point coordinates."""

    x: float
    y: float


@dataclass(frozen=True)
class VisibleTile:
    """A tile that is currently visible, with screen position."""

    z: int
    x: int
    y: int
    screen: ScreenPoint


@dataclass(frozen=True)
class LonLat:
    """A longitude/latitude pair."""

    lon: float
    lat: float

    def to_pixel(self, zoom: int, tile_size: int = 256) -> ScreenPoint:
        """Convert to screen pixel coordinates at a given zoom and tile size."""
        return lonlat_to_pixel(self, zoom, tile_size)

    def to_tile(self, zoom: int, tile_size: int = 256) -> TileCoord:
        """Convert to tile coordinates at a given zoom and tile size."""
        pixel = self.to_pixel(zoom, tile_size)
        return pixel.to_tile(zoom, tile_size)


@dataclass(frozen=True)
class Dimensions:
    """Width and height in pixels."""

    width: int
    height: int


@dataclass(frozen=True)
class VisbileMapArea:
    """Visible map area defined by top-left and bottom-right corners in LonLat."""

    top_left: LonLat
    bottom_right: LonLat
    zoom: int

    @property
    def tiles(self) -> list[VisibleTile]:
        """Return all visible tiles and their screen pixel positions.

        Includes duplicates if zoomed out far enough, and partially visible tiles.
        """
        tile_size = 256
        z = self.zoom
        n = 2**z
        # Get pixel coordinates for the corners
        top_left_px = self.top_left.to_pixel(z, tile_size)
        bottom_right_px = self.bottom_right.to_pixel(z, tile_size)
        # Compute tile x/y ranges (may be negative or > n if world repeats)
        x0 = int(top_left_px.x // tile_size)
        y0 = int(top_left_px.y // tile_size)
        x1 = int(bottom_right_px.x // tile_size)
        y1 = int(bottom_right_px.y // tile_size)
        tiles = []
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                # Wrap x for world repetition
                x_wrapped = x % n
                # y does not wrap (no vertical repetition)
                # Calculate tile's top-left pixel position
                tile_px_x = x * tile_size
                tile_px_y = y * tile_size
                # Screen position relative to top_left
                screen_x = tile_px_x - top_left_px.x
                screen_y = tile_px_y - top_left_px.y
                screen = ScreenPoint(int(screen_x), int(screen_y))
                tiles.append(VisibleTile(z=z, x=x_wrapped, y=y, screen=screen))
        return tiles


def lonlat_to_pixel(lonlat: LonLat, zoom: int, tile_size: int = 256) -> ScreenPoint:
    """Convert lon/lat to pixel coordinates at a given zoom."""
    n = 2.0**zoom
    pixel_x = int((lonlat.lon + 180.0) / 360.0 * n * tile_size)
    if lonlat.lat == MIN_LATITUDE:
        # Special case for the south pole to avoid division by zero
        pixel_y = int((1 - 0) * n * tile_size)
    elif lonlat.lat == MAX_LATITUDE:
        # Special case for the north pole to avoid division by zero
        pixel_y = 0
    else:
        sin_lat = math.sin(lonlat.lat * math.pi / 180)
        pixel_y = int(
            (0.5 - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi))
            * n
            * tile_size,
        )
    return ScreenPoint(pixel_x, pixel_y)


def pixel_to_tile(screen: ScreenPoint, zoom: int, tile_size: int = 256) -> TileCoord:
    """Convert pixel coordinates to lon/lat at a given zoom."""
    return TileCoord(z=zoom, xf=screen.x / tile_size, yf=screen.y / tile_size)
