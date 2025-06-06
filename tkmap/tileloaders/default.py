import tkinter as tk
import urllib.parse
from pathlib import Path
from typing import Optional

import requests

from tkmap.tileloaders.error_cache import ErrorCacheTileLoader

from .base import TileCallback, UrlTileLoader
from .disk_cache import DiskCacheTileLoader
from .memory_cache import MemoryCacheTileLoader
from .remote import RemoteTileLoader

TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"


class DefaultTileLoader(UrlTileLoader):
    _base_cache_dir: Path

    def __init__(
        self,
        url: Optional[str] = TILE_URL,
        base_cache_dir: Path = Path(".tile_cache"),
        requests_session: Optional[requests.Session] = None,
    ):
        self.base_cache_dir = base_cache_dir

        self.remote_loader = RemoteTileLoader(
            url=url,
            requests_session=requests_session,
        )
        self.error_cache_loader = ErrorCacheTileLoader(
            next_loader=self.remote_loader,
        )
        self.disk_cache_loader = DiskCacheTileLoader(
            next_loader=self.error_cache_loader,
            cache_dir=self.cache_dir,
        )
        self.tile_loader = MemoryCacheTileLoader(next_loader=self.disk_cache_loader)

    def get_tile_async(
        self,
        z: int,
        x: int,
        y: int,
        callback: TileCallback,
    ) -> None:
        max_index = (1 << z) - 1
        if not (0 <= x <= max_index and 0 <= y <= max_index):
            callback(
                Exception(f"Tile coordinates out of bounds for zoom {z}: x={x}, y={y}"),
                z,
                x,
                y,
            )
            return
        self.tile_loader.get_tile_async(z, x, y, callback)

    def start_remote_fetch_queue_processing(
        self, root: tk.Tk | tk.Toplevel, interval_ms: int = 100
    ) -> None:
        self.remote_loader.start_fetch_queue_processing(root, interval_ms)

    def shutdown(self):
        self.remote_loader.async_worker.shutdown()

    @property
    def base_cache_dir(self) -> Path:
        """Get the directory where tiles are cached."""
        return self._base_cache_dir

    @base_cache_dir.setter
    def base_cache_dir(self, base_cache_dir: Path) -> None:
        """Set the base directory for tile caching."""
        self._base_cache_dir = base_cache_dir
        if hasattr(self, "disk_cache_loader"):
            self.disk_cache_loader.cache_dir = self.cache_dir

    @property
    def cache_dir(self) -> Path:
        """Get the current cache directory based on the tile URL."""
        return self.base_cache_dir / self.cache_dir_key

    @property
    def cache_dir_key(self) -> str:
        """Get the cache directory key based on the tile URL."""
        try:
            return urllib.parse.urlparse(self.tile_url).netloc
        except ValueError:
            print(f"Invalid tile URL {self.tile_url}, using 'unknown' as cache key.")
            return "unknown"

    @property
    def tile_url(self) -> str:
        """Get the current tile URL."""
        return self.remote_loader.tile_url

    @tile_url.setter
    def tile_url(self, url: str) -> None:
        """Set a new tile URL for the remote loader."""
        self.remote_loader.tile_url = url
        self.disk_cache_loader.cache_dir = self.cache_dir
        self.error_cache_loader.clear()
        self.tile_loader.clear()
