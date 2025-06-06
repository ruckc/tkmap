import math
from unittest.mock import MagicMock

import pytest

from tkmap.model import Dimensions, LonLat, VisbileMapArea
from tkmap.viewport import Viewport


def test_viewport_init_and_properties():
    center = LonLat(10, 20)
    zoom = 5
    window_size = Dimensions(800, 600)
    vp = Viewport(center, zoom, window_size)
    assert vp.center == center
    assert vp.zoom == zoom
    assert vp.window_size == window_size


def test_viewport_setters():
    center = LonLat(0, 0)
    window_size = Dimensions(400, 300)
    vp = Viewport(center, 2, window_size)
    new_center = LonLat(5, 5)
    vp.center = new_center
    assert vp.center == new_center
    vp.zoom = 7
    assert vp.zoom == 7
    new_size = Dimensions(1000, 800)
    vp.window_size = new_size
    assert vp.window_size == new_size


def test_viewport_zoom_in_out():
    vp = Viewport(LonLat(0, 0), 10, Dimensions(100, 100))
    vp.zoom_in()
    assert vp.zoom == 11
    vp.zoom_out()
    assert vp.zoom == 10
    vp.zoom_to(LonLat(1, 2), 3)
    assert vp.center == LonLat(1, 2)
    assert vp.zoom == 3


def test_viewport_visible_area():
    center = LonLat(0, 0)
    window_size = Dimensions(256, 256)
    vp = Viewport(center, 0, window_size)
    area = vp.visible_area
    assert isinstance(area, VisbileMapArea)
    assert area.zoom == 0
    # The visible area should be symmetric around the center
    assert area.top_left.lon < center.lon < area.bottom_right.lon
    assert area.bottom_right.lat < center.lat < area.top_left.lat


def test_viewport_update_triggers_redraw_and_event():
    center = LonLat(0, 0)
    window_size = Dimensions(100, 100)
    redraw_called = {}

    def redraw():
        redraw_called["called"] = True

    event_manager = MagicMock()
    vp = Viewport(center, 1, window_size, redraw=redraw, event_manager=event_manager)
    vp.update(center=LonLat(1, 1), zoom=2, window_size=Dimensions(200, 200))
    assert redraw_called.get("called")
    event_manager.trigger_viewport_change.assert_called_once_with(
        center=LonLat(1, 1), zoom=2, screen=Dimensions(200, 200)
    )


def test_viewport_zoom_clamping():
    vp = Viewport(LonLat(0, 0), 10, Dimensions(100, 100))
    vp.zoom = -5
    assert vp.zoom == 0
    vp.zoom = 25
    assert vp.zoom == 19


def test_visible_area_web_mercator_math():
    def pixel_y_to_lat(pixel_y, zoom, tile_size=256):
        n = 2**zoom
        y = pixel_y / (tile_size * n)
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y)))
        return math.degrees(lat_rad)

    def pixel_x_to_lon(pixel_x, zoom, tile_size=256):
        n = 2**zoom
        return (pixel_x / (tile_size * n)) * 360.0 - 180.0

    # Center at (0, 0), zoom 0, window 256x256, tile_size=256
    center = LonLat(0, 0)
    window_size = Dimensions(256, 256)
    tile_size = 256
    zoom = 0
    vp = Viewport(center, zoom, window_size, tile_size=tile_size)
    area = vp.visible_area
    n = 2**zoom
    # Center pixel coordinates
    center_siny = math.sin(math.radians(center.lat))
    center_x = (center.lon + 180.0) / 360.0 * tile_size * n
    center_y = (
        (0.5 - math.log((1 + center_siny) / (1 - center_siny)) / (4 * math.pi))
        * tile_size
        * n
    )
    # Window in pixels
    half_width = window_size.width / 2
    half_height = window_size.height / 2
    left_pixel_x = center_x - half_width
    right_pixel_x = center_x + half_width
    top_pixel_y = center_y - half_height
    bottom_pixel_y = center_y + half_height
    expected_left = pixel_x_to_lon(left_pixel_x, zoom, tile_size)
    expected_right = pixel_x_to_lon(right_pixel_x, zoom, tile_size)
    expected_top = pixel_y_to_lat(top_pixel_y, zoom, tile_size)
    expected_bottom = pixel_y_to_lat(bottom_pixel_y, zoom, tile_size)
    assert area.top_left.lon == pytest.approx(expected_left)
    assert area.top_left.lat == pytest.approx(expected_top)
    assert area.bottom_right.lon == pytest.approx(expected_right)
    assert area.bottom_right.lat == pytest.approx(expected_bottom)

    # Test at zoom 2, window 512x512
    center = LonLat(10, 20)
    window_size = Dimensions(512, 512)
    zoom = 2
    vp = Viewport(center, zoom, window_size, tile_size=tile_size)
    area = vp.visible_area
    n = 2**zoom
    center_siny = math.sin(math.radians(center.lat))
    center_x = (center.lon + 180.0) / 360.0 * tile_size * n
    center_y = (
        (0.5 - math.log((1 + center_siny) / (1 - center_siny)) / (4 * math.pi))
        * tile_size
        * n
    )
    half_width = window_size.width / 2
    half_height = window_size.height / 2
    left_pixel_x = center_x - half_width
    right_pixel_x = center_x + half_width
    top_pixel_y = center_y - half_height
    bottom_pixel_y = center_y + half_height
    expected_left = pixel_x_to_lon(left_pixel_x, zoom, tile_size)
    expected_right = pixel_x_to_lon(right_pixel_x, zoom, tile_size)
    expected_top = pixel_y_to_lat(top_pixel_y, zoom, tile_size)
    expected_bottom = pixel_y_to_lat(bottom_pixel_y, zoom, tile_size)
    assert area.top_left.lon == pytest.approx(expected_left)
    assert area.top_left.lat == pytest.approx(expected_top)
    assert area.bottom_right.lon == pytest.approx(expected_right)
    assert area.bottom_right.lat == pytest.approx(expected_bottom)
