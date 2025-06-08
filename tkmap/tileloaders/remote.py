"""RemoteTileLoader for tkmap: fetches map tiles from remote servers."""

import logging
import tkinter as tk
from io import BytesIO

import requests
from PIL import Image

from tkmap.concurrency import AsyncThreadWorker
from tkmap.tileloaders.base import TileCallback, UrlTileLoader

logger = logging.getLogger(__name__)

TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
FETCH_THREADPOOL_SIZE = 4


class RemoteTileLoader(UrlTileLoader):
    """Tile loader that fetches tiles from a remote server using HTTP."""

    def __init__(
        self,
        url: str | None = TILE_URL,
        requests_session: requests.Session | None = None,
    ) -> None:
        """Initialize the remote tile loader.

        Args:
            url: Tile URL template.
            requests_session: Optional requests session.

        """
        self.requests_session = requests_session or requests.Session()
        self.requests_session.headers.update({"User-Agent": "tkmap/1.0"})
        self._tile_url = url or TILE_URL
        self.async_worker = AsyncThreadWorker(FETCH_THREADPOOL_SIZE)
        self._pending = set()  # Track (z, x, y) keys currently queued

    @property
    def tile_url(self) -> str:
        """Return the tile URL template."""
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
        """Fetch a tile asynchronously from the remote server."""
        key = (z, x, y)
        if key in self._pending:
            return  # Already queued
        self._pending.add(key)

        def fetch() -> Image.Image | Exception:
            url = self.tile_url.format(z=z, x=x, y=y)
            logger.log(
                logging.DEBUG,
                "[RemoteTileLoader]: Fetching tile %d/%d/%d from %s",
                z,
                x,
                y,
                url,
            )
            try:
                resp = self.requests_session.get(url, timeout=10)
                resp.raise_for_status()
                data = resp.content
                return Image.open(BytesIO(data)).convert("RGBA")
            except (requests.RequestException, OSError, ValueError) as e:
                logger.log(
                    logging.ERROR,
                    "RemoteTileLoader[]]: Error fetching tile %d/%d/%d from %s: %s",
                    z,
                    x,
                    y,
                    url,
                    e,
                )
                return e

        def on_result(result: Image.Image | Exception) -> None:
            self._pending.discard(key)
            callback(result, z, x, y)

        self.async_worker.submit(fetch, on_result)

    def start_fetch_queue_processing(
        self,
        root: tk.Tk | tk.Toplevel,
        interval_ms: int,
    ) -> None:
        """Start the fetch queue processing loop."""
        self.async_worker.start_processing(root, interval_ms)
