from dataclasses import dataclass

from tkmap.projection import Projection


@dataclass(frozen=True)
class TileCoord:
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

    def to_lonlat(self, projection: Projection, tile_size: int = 256) -> "LonLat":
        lon, lat = projection.tile_to_lonlat(self.xf, self.yf, self.z, tile_size)
        return LonLat(lon=lon, lat=lat)

    def __repr__(self) -> str:
        return f"TileCoord(z={self.z}, xf={self.xf}, yf={self.yf})"


@dataclass(frozen=True)
class ScreenPoint:
    x: int
    y: int

    def to_tile(self, zoom: int, tile_size: int = 256) -> TileCoord:
        """Convert screen coordinates to tile coordinates at a given zoom."""
        xf = self.x / tile_size
        yf = self.y / tile_size
        return TileCoord(z=zoom, xf=xf, yf=yf)


@dataclass(frozen=True)
class TileInstance:
    tile: TileCoord
    screen: ScreenPoint
    item_id: int


@dataclass(frozen=True)
class CenterTile:
    x: float
    y: float


@dataclass(frozen=True)
class VisibleTile:
    z: int
    x: int
    y: int
    screen: ScreenPoint


@dataclass(frozen=True)
class LonLat:
    lon: float
    lat: float


@dataclass(frozen=True)
class Dimensions:
    width: int
    height: int


@dataclass(frozen=True)
class VisbileMapArea:
    top_left: LonLat
    bottom_right: LonLat
    zoom: int
    projection: Projection

    @property
    def tiles(self) -> list["VisibleTile"]:
        """
        List all visible tiles (including duplicates if zoomed out far enough),
        and their screen pixel positions (including partially visible tiles).
        """
        tile_size = 256
        z = self.zoom
        n = 2**z
        top_left_px = ScreenPoint(
            *map(
                int,
                self.projection.lonlat_to_pixel(
                    self.top_left.lon, self.top_left.lat, z, tile_size
                ),
            )
        )
        bottom_right_px = ScreenPoint(
            *map(
                int,
                self.projection.lonlat_to_pixel(
                    self.bottom_right.lon, self.bottom_right.lat, z, tile_size
                ),
            )
        )
        x0 = int(top_left_px.x // tile_size)
        y0 = int(top_left_px.y // tile_size)
        x1 = int(bottom_right_px.x // tile_size)
        y1 = int(bottom_right_px.y // tile_size)
        tiles = []
        for y in range(y0, y1 + 1):
            if x1 >= x0:
                x_range = range(x0, x1 + 1)
            else:
                # Wrap around antimeridian
                x_range = list(range(x0, n)) + list(range(0, x1 + 1))
            for x in x_range:
                x_wrapped = x % n
                tile_px_x = x * tile_size
                tile_px_y = y * tile_size
                screen_x = tile_px_x - top_left_px.x
                screen_y = tile_px_y - top_left_px.y
                # Do NOT wrap screen_x here; let drawing code handle wrapping
                screen = ScreenPoint(int(screen_x), int(screen_y))
                tiles.append(VisibleTile(z=z, x=x_wrapped, y=y, screen=screen))
        return tiles
