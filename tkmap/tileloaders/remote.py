import tkinter as tk
from io import BytesIO
from typing import Optional

import requests
from PIL import Image

from ..concurrency import AsyncThreadWorker
from .base import TileCallback, UrlTileLoader

TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
FETCH_THREADPOOL_SIZE = 4


class RemoteTileLoader(UrlTileLoader):
    def __init__(
        self,
        url: Optional[str] = TILE_URL,
        requests_session: Optional[requests.Session] = None,
    ):
        self.requests_session = requests_session or requests.Session()
        self.requests_session.headers.update({"User-Agent": "tkmap/1.0"})
        self._tile_url = url or TILE_URL
        self.async_worker = AsyncThreadWorker(FETCH_THREADPOOL_SIZE)
        self._pending = set()  # Track (z, x, y) keys currently queued

    @property
    def tile_url(self) -> str:
        return self._tile_url

    @tile_url.setter
    def tile_url(self, url: str) -> None:
        """Set the tile URL template."""
        self._tile_url = url

    def get_tile_async(
        self,
        z: int,
        x: int,
        y: int,
        callback: TileCallback,
    ) -> None:
        key = (z, x, y)
        if key in self._pending:
            return  # Already queued
        self._pending.add(key)

        def fetch():
            url = self.tile_url.format(z=z, x=x, y=y)
            print(f"[RemoteTileLoader]: Fetching tile {z}/{x}/{y} from {url}")
            try:
                resp = self.requests_session.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.content
                return Image.open(BytesIO(data)).convert("RGBA")
            except Exception as e:
                print(
                    f"RemoteTileLoader[]]: Error fetching tile {z}/{x}/{y} from"
                    f"{url}: {e}"
                )
                return e

        def on_result(result):
            self._pending.discard(key)
            callback(result, z, x, y)

        self.async_worker.submit(fetch, on_result)

    def start_fetch_queue_processing(
        self, root: tk.Tk | tk.Toplevel, interval_ms: int
    ) -> None:
        self.async_worker.start_processing(root, interval_ms)
