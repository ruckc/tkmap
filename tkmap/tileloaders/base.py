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


class UrlTileLoader(TileLoader):
    @property
    @abstractmethod
    def tile_url(self) -> str:
        pass

    @tile_url.setter
    @abstractmethod
    def tile_url(self, url: str) -> None:
        """Set the tile URL template."""
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
            # print(f"{type(self).__name__}: Tile {z}/{x}/{y} found in cache.")
            self._get_tile_async(z, x, y, callback)
        else:
            # print(
            #     f"{type(self).__name__}: Tile {z}/{x}/{y} not found, fetching from"
            #     " next loader."
            # )

            def save_and_callback(img, z=z, x=x, y=y):
                if isinstance(img, Exception):
                    print(
                        f"{type(self).__name__}: Error loading tile {z}/{x}/{y}: {img}"
                    )
                # else:
                # print(
                #     f"{type(self).__name__}: Successfully loaded tile {z}/{x}/{y}"
                # )
                if img is not None and not isinstance(img, Exception):
                    self._save_tile(z, x, y, img)
                callback(img, z, x, y)

            self._next_loader.get_tile_async(z, x, y, save_and_callback)
