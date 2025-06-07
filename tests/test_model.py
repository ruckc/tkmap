import itertools

import pytest

from tkmap.model import (
    CenterTile,
    Dimensions,
    LonLat,
    ScreenPoint,
    TileCoord,
    TileInstance,
    VisbileMapArea,
    VisibleTile,
)
from tkmap.projection import Projection


def test_lonlat_properties():
    ll = LonLat(lon=10.0, lat=20.0)
    assert ll.lon == 10.0
    assert ll.lat == 20.0
    # __repr__ includes both lon and lat
    s = repr(ll)
    assert "LonLat" in s and "lon=10.0" in s and "lat=20.0" in s


@pytest.mark.parametrize(
    "lon,lat",
    list(
        itertools.product(
            range(-180, 181, 10),
            range(-80, 81, 10),
        )
    ),
)
def test_exhaustive_lonlat_properties(lon, lat):
    ll = LonLat(lon=lon, lat=lat)
    assert ll.lon == lon and ll.lat == lat
    s = repr(ll)
    assert "LonLat" in s and f"lon={lon}" in s and f"lat={lat}" in s


def test_tilecoord_properties():
    tc = TileCoord(z=3, xf=4.7, yf=5.2)
    assert tc.x == 4
    assert tc.y == 5
    projection = Projection()
    ll = tc.to_lonlat(projection)
    assert isinstance(ll.lon, float)
    assert isinstance(ll.lat, float)
    s = repr(tc)
    assert "TileCoord" in s and "xf=4.7" in s and "yf=5.2" in s


def test_screenpoint_to_tile():
    sp = ScreenPoint(x=512, y=768)
    tile = sp.to_tile(zoom=2, tile_size=256)
    assert isinstance(tile, TileCoord)
    assert tile.z == 2
    assert tile.xf == 2.0
    assert tile.yf == 3.0


def test_tileinstance_dataclass():
    tc = TileCoord(1, 2.0, 3.0)
    sp = ScreenPoint(10, 20)
    ti = TileInstance(tile=tc, screen=sp, item_id=42)
    assert ti.tile == tc
    assert ti.screen == sp
    assert ti.item_id == 42


def test_centertile_dataclass():
    ct = CenterTile(x=1.5, y=2.5)
    assert ct.x == 1.5 and ct.y == 2.5


def test_visibletile_dataclass():
    vt = VisibleTile(z=1, x=2, y=3, screen=ScreenPoint(100, 200))
    assert vt.z == 1 and vt.x == 2 and vt.y == 3
    assert vt.screen.x == 100 and vt.screen.y == 200


def test_lonlat_to_pixel_and_to_tile():
    ll = LonLat(lon=0, lat=0)
    projection = Projection()
    sp = ScreenPoint(
        *map(int, projection.lonlat_to_pixel(ll.lon, ll.lat, zoom=2, tile_size=256))
    )
    assert isinstance(sp, ScreenPoint)
    xf, yf = projection.lonlat_to_tile(ll.lon, ll.lat, zoom=2, tile_size=256)
    tile = TileCoord(z=2, xf=xf, yf=yf)
    assert isinstance(tile, TileCoord)
    assert tile.z == 2


def test_dimensions_dataclass():
    d = Dimensions(width=800, height=600)
    assert d.width == 800 and d.height == 600


def test_visiblemaparea_dataclass():
    ll1 = LonLat(0, 0)
    ll2 = LonLat(10, 10)
    projection = Projection()
    vma = VisbileMapArea(top_left=ll1, bottom_right=ll2, zoom=5, projection=projection)
    assert vma.top_left == ll1
    assert vma.bottom_right == ll2
    assert vma.zoom == 5


def test_lonlat_to_pixel_function():
    ll = LonLat(0, 0)
    projection = Projection()
    sp = ScreenPoint(
        *map(int, projection.lonlat_to_pixel(ll.lon, ll.lat, zoom=2, tile_size=256))
    )
    assert isinstance(sp, ScreenPoint)
    ll_north = LonLat(0, 90)
    sp_north = ScreenPoint(
        *map(int, projection.lonlat_to_pixel(ll_north.lon, ll_north.lat, 2))
    )
    assert sp_north.y <= 0  # North pole is above the map in Web Mercator
    ll_south = LonLat(0, -90)
    sp_south = ScreenPoint(
        *map(int, projection.lonlat_to_pixel(ll_south.lon, ll_south.lat, 2))
    )
    assert sp_south.y > 0


@pytest.mark.parametrize(
    "zoom,lon,lat",
    list(
        itertools.product(
            range(0, 20),
            range(-180, 181, 10),
            range(-80, 81, 10),
        )
    ),
)
def test_exhaustive_roundtrip_test_from_lonlat_to_tile_and_back(zoom, lon, lat):
    n = 2**zoom
    tile_size = 256
    lon_per_pixel = 360.0 / (n * tile_size)
    lat_per_pixel = 180.0 / (n * tile_size)
    tolerance_lon = lon_per_pixel * 2
    tolerance_lat = lat_per_pixel * 2
    ll = LonLat(lon=lon, lat=lat)
    projection = Projection()
    sp = ScreenPoint(
        *map(
            int,
            projection.lonlat_to_pixel(ll.lon, ll.lat, zoom=zoom, tile_size=tile_size),
        )
    )
    tile = TileCoord(z=zoom, xf=sp.x / tile_size, yf=sp.y / tile_size)
    ll_roundtrip = tile.to_lonlat(projection, tile_size)

    def lon_equiv(a, b, tol):
        return (a - b) % 360 < tol or (b - a) % 360 < tol

    assert lon_equiv(ll.lon, ll_roundtrip.lon, tolerance_lon), (
        f"Failed lon check for zoom={zoom}, lon={lon}, lat={lat} "
        f"with roundtrip {ll_roundtrip} with tolerance {tolerance_lon}"
    )
    assert ll.lat == pytest.approx(ll_roundtrip.lat, abs=tolerance_lat), (
        f"Failed lat check for zoom={zoom}, lon={lon}, lat={lat} "
        f"with roundtrip {ll_roundtrip} with tolerance {tolerance_lat}"
    )
