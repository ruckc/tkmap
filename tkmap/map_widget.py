import math
import sys
import tkinter as tk
from pathlib import Path
from typing import Any, Optional

import requests
from PIL.ImageTk import PhotoImage
from platformdirs import user_cache_dir

from tkmap.model import Dimensions, LonLat, ScreenPoint

from .events import MapWidgetEventManager, MouseMovedEvent
from .layers import GroupLayer, Layer, TileLayer
from .tileloaders import DefaultTileLoader, TileLoader
from .viewport import Viewport


class MapWidget(tk.Canvas):
    """A Tkinter widget for displaying a map with tiles."""

    def __init__(
        self,
        parent: tk.Misc,
        center: LonLat = LonLat(0, 0),
        zoom: int = 1,
        tile_size: int = 256,
        tile_loader: Optional[TileLoader] = None,
        **kwargs: Any,
    ):
        super().__init__(parent, **kwargs)
        self._tile_loader = tile_loader or DefaultTileLoader(
            url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            base_cache_dir=Path(user_cache_dir("tkmap")) / "tile_cache",
            requests_session=requests.Session(),
        )
        self._event_manager = MapWidgetEventManager()
        self._tile_size = tile_size
        self._viewport = Viewport(
            LonLat(0, 0),
            1,
            Dimensions(800, 600),
            self._tile_size,
            self.redraw,
            self._event_manager,
        )
        self._root_layer = GroupLayer(name="Root")
        self._setup_layers()
        self._setup_event_bindings()
        self._setup_method_bindings()

        self._viewport.update(
            center=center,
            zoom=zoom,
            window_size=Dimensions(self.winfo_reqwidth(), self.winfo_reqheight()),
        )

        self._drag_start: Optional[ScreenPoint] = None

    def _setup_layers(self):
        base_layer = TileLayer(
            tile_loader=self._tile_loader,
            tile_size=self._tile_size,
            photo_image_cls=PhotoImage,
            name="BaseMap",
        )
        self._root_layer.add_layer(base_layer)

    def add_layer(self, layer: Layer):
        self._root_layer.add_layer(layer)

    def remove_layer(self, name: str):
        self._root_layer.remove_layer(name)

    def show_layer(self, name: str):
        self._root_layer.show_layer(name)
        self.redraw(flush=True)

    def hide_layer(self, name: str):
        self._root_layer.hide_layer(name)
        self.redraw(flush=True)

    def _setup_event_bindings(self) -> None:
        # zoom
        self.bind("<MouseWheel>", self._mouse_zoom)
        if sys.platform == "linux":
            # Linux uses Button-4 and Button-5 for mouse wheel events
            self.bind("<Button-4>", self._mouse_zoom_linux)
            self.bind("<Button-5>", self._mouse_zoom_linux)

        # mouse movement
        self.bind("<Motion>", self._mouse_moved)

        # resizing the widget
        self.bind(
            "<Configure>",
            lambda event: self._viewport.update(
                window_size=Dimensions(event.width, event.height)
            ),
        )

        # panning start & end
        self.bind("<B1-Motion>", self._drag)
        self.bind("<ButtonRelease-1>", self._drag_end)

    def _drag(self, event: tk.Event) -> None:
        """Handle mouse click events for panning."""
        if self._drag_start is None:
            self._drag_start = ScreenPoint(event.x, event.y)
        else:
            dx = event.x - self._drag_start.x
            dy = event.y - self._drag_start.y
            # Convert center to pixel coordinates
            center = self._viewport.center
            zoom = self._viewport.zoom
            tile_size = self._tile_size
            center_px = center.to_pixel(zoom, tile_size)
            # Subtract drag delta
            new_center_px = ScreenPoint(center_px.x - dx, center_px.y - dy)
            # Convert back to lon/lat

            n = 2.0**zoom
            lon = (new_center_px.x / (tile_size * n)) * 360.0 - 180.0
            y = new_center_px.y / (tile_size * n)
            lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y)))
            lat = math.degrees(lat_rad)
            new_center = LonLat(lon, lat)
            self._viewport.update(center=new_center)
            self._drag_start = ScreenPoint(event.x, event.y)

    def _drag_end(self, event: tk.Event) -> None:
        """Handle mouse release events to stop panning."""
        self._drag_start = None

    def _setup_method_bindings(self) -> None:
        # Bind the event manager handler registration methods to the widget
        self.on_mouse_moved = self._event_manager.on_mouse_moved
        self.on_viewport_change = self._event_manager.on_viewport_change

        self.zoom_to = self._viewport.zoom_to
        self.zoom_in = self._viewport.zoom_in
        self.zoom_out = self._viewport.zoom_out

    def _mouse_moved(self, event: tk.Event) -> None:
        """Handle mouse movement events."""
        # Convert screen coordinates to lon/lat using viewport math

        sp = ScreenPoint(event.x, event.y)
        self._event_manager.trigger_mouse_moved(
            MouseMovedEvent(screen=sp, lonlat=self._viewport.screen_to_lonlat(sp))
        )

    def _mouse_zoom(self, event: tk.Event) -> None:
        """Handle mouse wheel zoom events."""
        if event.delta > 0:
            self._viewport.zoom_in()
        elif event.delta < 0:
            self._viewport.zoom_out()

    def _mouse_zoom_linux(self, event: tk.Event) -> None:
        """Handle mouse wheel zoom events on Linux."""
        if event.num == 4:
            self._viewport.zoom_in()
        elif event.num == 5:
            self._viewport.zoom_out()

    def redraw(self, flush: bool = False) -> None:
        """Redraw all visible layers."""
        if flush:
            self.delete("all")
        self._root_layer.draw(self, self._viewport)
