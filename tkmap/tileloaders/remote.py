import tkinter as tk
from io import BytesIO
from typing import Optional

import requests
from PIL import Image

from ..concurrency import AsyncThreadWorker
from .base import TileCallback, TileLoader

TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
FETCH_THREADPOOL_SIZE = 4


class RemoteTileLoader(TileLoader):
    def __init__(
        self,
        url: Optional[str] = TILE_URL,
        requests_session: Optional[requests.Session] = None,
    ):
        self.requests_session = requests_session or requests.Session()
        self.requests_session.headers.update({"User-Agent": "tkmap/1.0"})
        self.tile_url = url or TILE_URL
        self.async_worker = AsyncThreadWorker(FETCH_THREADPOOL_SIZE)
        self._pending = set()  # Track (z, x, y) keys currently queued

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
            try:
                resp = self.requests_session.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.content
                return Image.open(BytesIO(data)).convert("RGBA")
            except Exception as e:
                return e

        def on_result(result):
            self._pending.discard(key)
            callback(result, z, x, y)

        self.async_worker.submit(fetch, on_result)

    def start_fetch_queue_processing(self, root: tk.Tk, interval_ms: int) -> None:
        self.async_worker.start_processing(root, interval_ms)
