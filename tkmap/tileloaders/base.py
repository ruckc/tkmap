"""Base classes and protocols for tile loading in tkmap."""

import logging
from abc import ABC, abstractmethod
from typing import Protocol

from PIL import Image

ImageOrException = Image.Image | Exception | None


logger = logging.getLogger(__name__)


class TileCallback(Protocol):
    """Handle the loaded tile image or error."""

    def __call__(self, img: ImageOrException, z: int, x: int, y: int) -> None:
        """Handle the loaded tile image or error."""


class TileLoader(ABC):
    """Abstract base class for all tile loaders."""

    log_requests: bool
    tile_size: int

    @abstractmethod
    def get_tile_async(
        self,
        z: int,
        x: int,
        y: int,
        callback: TileCallback,
    ) -> None:
        """Fetch a tile asynchronously and call the callback with the result."""


class UrlTileLoader(TileLoader):
    """Abstract base class for tile loaders that use a URL template."""

    @property
    @abstractmethod
    def tile_url(self) -> str:
        """Return the tile URL template."""

    @tile_url.setter
    @abstractmethod
    def tile_url(self, url: str) -> None:
        """Set the tile URL template."""


class ChainedTileLoader(TileLoader):
    """Tile loader that chains to a next loader for cache/memory layers."""

    _next_loader: TileLoader

    def __init__(self, next_loader: TileLoader) -> None:
        """Initialize the chained tile loader with a next loader."""
        self._next_loader = next_loader

    @abstractmethod
    def _get_tile_async(
        self,
        z: int,
        x: int,
        y: int,
        callback: TileCallback,
    ) -> None:
        """Fetch a tile from this loader's cache or storage asynchronously."""

    @abstractmethod
    def _has_tile(self, z: int, x: int, y: int) -> bool:
        """Return True if the tile is present in this loader's cache/storage."""

    @abstractmethod
    def _save_tile(self, z: int, x: int, y: int, img: Image.Image) -> None:
        """Save a tile image to this loader's cache/storage."""

    def get_tile_async(
        self,
        z: int,
        x: int,
        y: int,
        callback: TileCallback,
    ) -> None:
        """Fetch a tile, using this loader or the next loader if not present."""
        if self._has_tile(z, x, y):
            # print(f"{type(self).__name__}: Tile {z}/{x}/{y} found in cache.")
            self._get_tile_async(z, x, y, callback)
        else:
            # print(
            #     f"{type(self).__name__}: Tile {z}/{x}/{y} not found, fetching from"
            #     " next loader."
            # )

            def save_and_callback(
                img: ImageOrException,
                z: int = z,
                x: int = x,
                y: int = y,
            ) -> None:
                if isinstance(img, Exception):
                    logger.log(
                        logging.ERROR,
                        "%s: Error loading tile %d/%d/%d: %s",
                        type(self).__name__,
                        z,
                        x,
                        y,
                        img,
                    )
                # else:
                # print(
                #     f"{type(self).__name__}: Successfully loaded tile {z}/{x}/{y}"
                # )
                if img is not None and not isinstance(img, Exception):
                    self._save_tile(z, x, y, img)
                callback(img, z, x, y)

            self._next_loader.get_tile_async(z, x, y, save_and_callback)
