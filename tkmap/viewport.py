"""Viewport logic for tkmap: handles map window, zoom, and coordinate transforms."""

import math
from collections.abc import Callable

from tkmap.events import MapWidgetEventManager
from tkmap.model import Dimensions, LonLat, ScreenPoint, VisbileMapArea


class Viewport:
    """A class representing the viewport of the map widget."""

    # ruff: noqa: PLR0913
    def __init__(
        self,
        center: LonLat,
        zoom: int,
        window_size: Dimensions,
        tile_size: int = 256,
        redraw: Callable[[], None] | None = None,
        event_manager: MapWidgetEventManager | None = None,
    ) -> None:
        """Initialize a Viewport.

        Args:
            center: The center of the viewport as a LonLat.
            zoom: The zoom level.
            window_size: The window size in pixels.
            tile_size: The size of each tile in pixels (default 256).
            redraw: Optional callback to trigger a redraw.
            event_manager: Optional event manager for viewport events.

        """
        self._center = center
        self._zoom = zoom
        self._tile_size = tile_size
        self._window_size = window_size
        self._redraw = redraw
        self._event_manager = event_manager

    @property
    def width(self) -> int:
        """Get the width of the viewport window."""
        return self.window_size.width

    @property
    def height(self) -> int:
        """Get the height of the viewport window."""
        return self.window_size.height

    @property
    def center(self) -> LonLat:
        """Get the center of the viewport."""
        return self._center

    @property
    def zoom(self) -> int:
        """Get the zoom level of the viewport."""
        return self._zoom

    @property
    def window_size(self) -> Dimensions:
        """Get the size of the viewport window."""
        return self._window_size

    @center.setter
    def center(self, value: LonLat) -> None:
        """Set the center of the viewport and trigger a redraw."""
        self.update(center=value)

    @zoom.setter
    def zoom(self, value: int) -> None:
        """Set the zoom level of the viewport and trigger a redraw."""
        self.update(zoom=value)

    def zoom_to(self, center: LonLat, zoom: int) -> None:
        """Set the viewport to a specific center and zoom level."""
        self.update(center=center, zoom=zoom)

    def zoom_in(self) -> None:
        """Increase the zoom level by 1 and trigger a redraw."""
        self.update(zoom=self.zoom + 1)

    def zoom_out(self) -> None:
        """Decrease the zoom level by 1 and trigger a redraw."""
        self.update(zoom=self.zoom - 1)

    @window_size.setter
    def window_size(self, value: Dimensions) -> None:
        """Set the size of the viewport window and trigger a redraw."""
        self.update(window_size=value)

    @property
    def visible_area(self) -> VisbileMapArea:
        """Calculate the visible area of the map based on the current viewport.

        Uses Web Mercator math for latitude and longitude bounds.
        """

        def pixel_y_to_lat(pixel_y: float, zoom: int, tile_size: int = 256) -> float:
            n = 2**zoom
            y = pixel_y / (tile_size * n)
            lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y)))
            return math.degrees(lat_rad)

        n = 2**self.zoom
        tile_size = self._tile_size
        # Center pixel coordinates
        center_x = (self.center.lon + 180.0) / 360.0 * tile_size * n
        center_siny = math.sin(math.radians(self.center.lat))
        center_y = (
            (0.5 - math.log((1 + center_siny) / (1 - center_siny)) / (4 * math.pi))
            * tile_size
            * n
        )
        # Window in pixels
        half_width = self.window_size.width / 2
        half_height = self.window_size.height / 2
        # Pixel coordinates for corners
        left_pixel_x = center_x - half_width
        right_pixel_x = center_x + half_width
        top_pixel_y = center_y - half_height
        bottom_pixel_y = center_y + half_height
        # Convert back to lon/lat
        left = (left_pixel_x / (tile_size * n)) * 360.0 - 180.0
        right = (right_pixel_x / (tile_size * n)) * 360.0 - 180.0
        top = pixel_y_to_lat(top_pixel_y, self.zoom, tile_size)
        bottom = pixel_y_to_lat(bottom_pixel_y, self.zoom, tile_size)
        return VisbileMapArea(
            top_left=LonLat(left, top),
            bottom_right=LonLat(right, bottom),
            zoom=self.zoom,
        )

    def update(
        self,
        center: LonLat | None = None,
        zoom: int | None = None,
        window_size: Dimensions | None = None,
    ) -> None:
        """Update the viewport with new center, zoom, and window size."""
        if center:
            self._center = center
        if window_size:
            self._window_size = window_size
        if zoom:
            new_zoom = zoom if zoom is not None else self.zoom
            self._zoom = max(0, min(19, new_zoom))

        if self._redraw:
            self._redraw()
        if self._event_manager:
            self._event_manager.trigger_viewport_change(
                center=self.center,
                zoom=self.zoom,
                screen=self.window_size,
            )

    def screen_to_lonlat(self, screen: ScreenPoint) -> LonLat:
        """Convert a screen point (relative to the widget) to a LonLat.

        Uses the current viewport center, zoom, window size, and tile size.
        """
        zoom = self.zoom
        tile_size = self._tile_size
        n = 2.0**zoom
        center = self.center
        window_size = self.window_size
        center_px = center.to_pixel(zoom, tile_size)
        global_px_x = center_px.x - window_size.width // 2 + screen.x
        global_px_y = center_px.y - window_size.height // 2 + screen.y
        lon = (global_px_x / (tile_size * n)) * 360.0 - 180.0
        y = global_px_y / (tile_size * n)
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y)))
        lat = math.degrees(lat_rad)
        return LonLat(lon, lat)

    def lonlat_to_screen(self, lon: float, lat: float) -> ScreenPoint:
        """Convert longitude and latitude to screen (pixel) coordinates.

        Uses the current viewport.
        """
        # Use the same math as in visible_area and screen_to_lonlat, but in reverse
        zoom = self.zoom
        tile_size = self._tile_size
        n = 2.0**zoom
        # Convert lon/lat to global pixel coordinates
        center = self.center
        window_size = self.window_size
        center_px = center.to_pixel(zoom, tile_size)
        pixel_x = int((lon + 180.0) / 360.0 * n * tile_size)
        sin_lat = math.sin(lat * math.pi / 180)
        pixel_y = int(
            (0.5 - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi))
            * n
            * tile_size,
        )
        # Convert global pixel coordinates to screen coordinates
        # relative to the viewport
        screen_x = pixel_x - (center_px.x - window_size.width // 2)
        screen_y = pixel_y - (center_px.y - window_size.height // 2)
        return ScreenPoint(screen_x, screen_y)
