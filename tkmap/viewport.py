import math
from typing import Callable, Optional

from tkmap.events import MapWidgetEventManager
from tkmap.model import Dimensions, LonLat, ScreenPoint, VisbileMapArea
from tkmap.projection import Projection


class Viewport:
    """A class representing the viewport of the map widget."""

    def __init__(
        self,
        center: LonLat,
        zoom: int,
        window_size: Dimensions,
        tile_size: int = 256,
        redraw: Optional[Callable[[], None]] = None,
        event_manager: Optional[MapWidgetEventManager] = None,
        projection: Optional[Projection] = None,
    ):
        self._center = center
        self._zoom = zoom
        self._tile_size = tile_size
        self._window_size = window_size
        self._redraw = redraw
        self._event_manager = event_manager
        self._projection = projection or Projection("EPSG:3857")

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
        """
        Calculate the visible area of the map based on the current viewport.
        Uses the current projection for latitude and longitude bounds.
        """
        # Project center to projected coordinates
        center_x, center_y = self._projection.to_projected(
            self.center.lon, self.center.lat
        )
        # Calculate scale (meters per pixel) at current zoom
        initial_resolution = 2 * math.pi * 6378137 / self._tile_size
        resolution = initial_resolution / (2**self.zoom)
        half_width = self.window_size.width / 2 * resolution
        half_height = self.window_size.height / 2 * resolution
        # Corners in projected coordinates
        left_x = center_x - half_width
        right_x = center_x + half_width
        top_y = center_y + half_height
        bottom_y = center_y - half_height
        # Convert back to lon/lat
        left, top = self._projection.from_projected(left_x, top_y)
        right, bottom = self._projection.from_projected(right_x, bottom_y)
        return VisbileMapArea(
            top_left=LonLat(left, top),
            bottom_right=LonLat(right, bottom),
            zoom=self.zoom,
            projection=self._projection,
        )

    def update(
        self,
        center: Optional[LonLat] = None,
        zoom: Optional[int] = None,
        window_size: Optional[Dimensions] = None,
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
                center=self.center, zoom=self.zoom, screen=self.window_size
            )

    def lonlat_to_screen(self, lonlat: LonLat) -> ScreenPoint:
        """
        Convert a LonLat to screen coordinates using the current projection,
        center, zoom, and window size.
        """
        # Project center and target point
        center_x, center_y = self._projection.to_projected(
            self.center.lon, self.center.lat
        )
        point_x, point_y = self._projection.to_projected(lonlat.lon, lonlat.lat)
        # Calculate scale (meters per pixel) at current zoom for Web Mercator
        initial_resolution = 2 * math.pi * 6378137 / self._tile_size
        resolution = initial_resolution / (2**self.zoom)
        dx = (point_x - center_x) / resolution + self.window_size.width / 2
        dy = (center_y - point_y) / resolution + self.window_size.height / 2
        return ScreenPoint(int(dx), int(dy))

    def screen_to_lonlat(self, screen: ScreenPoint) -> LonLat:
        """
        Convert a screen point (relative to the widget) to a LonLat using the
        current projection, center, zoom, and window size.
        """
        center_x, center_y = self._projection.to_projected(
            self.center.lon, self.center.lat
        )
        initial_resolution = 2 * math.pi * 6378137 / self._tile_size
        resolution = initial_resolution / (2**self.zoom)
        x = center_x + (screen.x - self.window_size.width / 2) * resolution
        y = center_y - (screen.y - self.window_size.height / 2) * resolution
        lon, lat = self._projection.from_projected(x, y)
        return LonLat(lon, lat)

    @property
    def projection(self) -> Projection:
        return self._projection

    @projection.setter
    def projection(self, value: Projection) -> None:
        self._projection = value
        if self._redraw:
            self._redraw()
