"""Event classes and event manager for tkmap map widget interactions."""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass

from .model import Dimensions, LonLat, ScreenPoint

logger = logging.getLogger(__name__)


class Event(ABC):
    """Base class for all tkmap events."""

    @abstractmethod
    def __repr__(self) -> str:
        """Return a string representation of the event."""


@dataclass(frozen=True)
class MouseMovedEvent(Event):
    """Event representing a mouse movement over the map widget."""

    screen: ScreenPoint
    lonlat: LonLat

    def __repr__(self) -> str:
        """Return a string representation of the mouse moved event."""
        return f"MouseMovedEvent(screen={self.screen}, lonlat={self.lonlat})"


@dataclass(frozen=True)
class ViewportChangeEvent(Event):
    """Event representing a change in the map viewport."""

    window_size: Dimensions
    center: LonLat
    zoom: int

    def __repr__(self) -> str:
        """Return a string representation of the viewport change event."""
        return (
            f"ViewportChangeEvent(size={self.window_size}, "
            f"center={self.center}, zoom={self.zoom})"
        )


class MapWidgetEventManager:
    """Manages event callbacks for mouse movement and viewport changes in MapWidget."""

    _mouse_moved: list[Callable[[MouseMovedEvent], None]]
    _viewport_change: list[Callable[[ViewportChangeEvent], None]]

    def __init__(self) -> None:
        """Initialize the event manager with empty callback lists."""
        self._mouse_moved = []
        self._viewport_change = []

    def on_mouse_moved(self, callback: Callable[[MouseMovedEvent], None]) -> None:
        """Register a callback for mouse moved events."""
        logger.log(logging.DEBUG, "Registering mouse moved callback %s", callback)
        self._mouse_moved.append(callback)

    def on_viewport_change(
        self,
        callback: Callable[[ViewportChangeEvent], None],
    ) -> None:
        """Register a callback for viewport change events."""
        logger.log(logging.DEBUG, "Registering viewport change callback %s", callback)
        self._viewport_change.append(callback)

    def trigger_mouse_moved(self, event: MouseMovedEvent) -> None:
        """Trigger all registered mouse moved callbacks with the given event."""
        for callback in self._mouse_moved:
            callback(event)

    def trigger_viewport_change(
        self,
        center: LonLat,
        zoom: int,
        screen: Dimensions,
    ) -> None:
        """Trigger all viewport change callbacks with the given parameters."""
        for callback in self._viewport_change:
            callback(
                ViewportChangeEvent(
                    window_size=screen,
                    center=center,
                    zoom=zoom,
                ),
            )
