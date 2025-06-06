from abc import ABC
from dataclasses import dataclass
from typing import Callable

from .model import Dimensions, LonLat, ScreenPoint


class Event(ABC):
    pass


@dataclass(frozen=True)
class MouseMovedEvent(Event):
    screen: ScreenPoint
    lonlat: LonLat


@dataclass(frozen=True)
class ViewportChangeEvent(Event):
    window_size: Dimensions
    center: LonLat
    zoom: int


class MapWidgetEventManager:
    _mouse_moved: list[Callable[[MouseMovedEvent], None]]
    _viewport_change: list[Callable[[ViewportChangeEvent], None]]

    def __init__(self):
        self._mouse_moved = []
        self._viewport_change = []

    def on_mouse_moved(self, callback: Callable[[MouseMovedEvent], None]) -> None:
        """Register a callback for mouse moved events."""
        print("Registering mouse moved callback", callback)
        self._mouse_moved.append(callback)

    def on_viewport_change(
        self, callback: Callable[[ViewportChangeEvent], None]
    ) -> None:
        """Register a callback for viewport change events."""
        print("Registering viewport change callback", callback)
        self._viewport_change.append(callback)

    def trigger_mouse_moved(self, event: MouseMovedEvent) -> None:
        for callback in self._mouse_moved:
            callback(event)

    def trigger_viewport_change(
        self, center: LonLat, zoom: int, screen: Dimensions
    ) -> None:
        for callback in self._viewport_change:
            callback(
                ViewportChangeEvent(
                    window_size=Dimensions(0, 0),
                    center=center,
                    zoom=zoom,
                )
            )
