import tkinter as tk
from pathlib import Path
from typing import Optional

import requests

from tkmap.tileloaders.logging_tile_loader import LoggingTileLoader

from .base import TileCallback, TileLoader
from .disk_cache import DiskCacheTileLoader
from .error_cache import ErrorCacheTileLoader
from .memory_cache import MemoryCacheTileLoader
from .remote import RemoteTileLoader

TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"


class DefaultTileLoader(TileLoader):
    def __init__(
        self,
        url: Optional[str] = TILE_URL,
        cache_dir: Path = Path(".tile_cache"),
        requests_session: Optional[requests.Session] = None,
    ):
        self.remote_loader = RemoteTileLoader(
            url=url,
            requests_session=requests_session,
        )
        self.tile_loader = LoggingTileLoader(
            MemoryCacheTileLoader(
                next_loader=DiskCacheTileLoader(
                    ErrorCacheTileLoader(self.remote_loader),
                    cache_dir=cache_dir,
                ),
            )
        )

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
        self, root: tk.Tk, interval_ms: int = 100
    ) -> None:
        self.remote_loader.start_fetch_queue_processing(root, interval_ms)

    def shutdown(self):
        self.remote_loader.async_worker.shutdown()
