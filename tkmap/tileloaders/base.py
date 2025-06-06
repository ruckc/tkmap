from abc import ABC, abstractmethod
from typing import Optional, Protocol

from PIL import Image

ImageOrException = Optional[Image.Image | Exception]


class TileCallback(Protocol):
    def __call__(self, img: ImageOrException, z: int, x: int, y: int) -> None:
        """Callback to handle the loaded tile image or error."""
        pass


class TileLoader(ABC):
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
        pass


class ChainedTileLoader(TileLoader):
    _next_loader: TileLoader

    def __init__(self, next_loader: TileLoader):
        self._next_loader = next_loader

    @abstractmethod
    def _get_tile_async(
        self,
        z: int,
        x: int,
        y: int,
        callback: TileCallback,
    ) -> None:
        pass

    @abstractmethod
    def _has_tile(self, z: int, x: int, y: int) -> bool:
        pass

    @abstractmethod
    def _save_tile(self, z: int, x: int, y: int, img: Image.Image) -> None:
        pass

    def get_tile_async(
        self,
        z: int,
        x: int,
        y: int,
        callback: TileCallback,
    ) -> None:
        if self._has_tile(z, x, y):
            self._get_tile_async(z, x, y, callback)
        else:

            def save_and_callback(img, z=z, x=x, y=y):
                if img is not None and not isinstance(img, Exception):
                    self._save_tile(z, x, y, img)
                callback(img, z, x, y)

            self._next_loader.get_tile_async(z, x, y, save_and_callback)
