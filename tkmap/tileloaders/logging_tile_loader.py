"""LoggingTileLoader for tkmap: logs tile loading operations for debugging."""

import logging
import time

from .base import ImageOrException, TileCallback, TileLoader

logger = logging.getLogger(__name__)


class LoggingTileLoader(TileLoader):
    """A tile loader that logs tile requests and the time taken for each tile to load.

    Wraps any other tile loader.
    """

    def __init__(self, loader: TileLoader) -> None:
        """Initialize the LoggingTileLoader with a next loader.

        :param loader: The next tile loader to wrap.
        """
        self.loader = loader

    def get_tile_async(self, z: int, x: int, y: int, callback: TileCallback) -> None:
        """Fetch a tile asynchronously and log the request and timing."""
        request_time = time.time()

        def wrapped_callback(img: ImageOrException, z: int, x: int, y: int) -> None:
            elapsed = time.time() - request_time
            logger.log(
                logging.DEBUG,
                "[%s] Tile z=%d, x=%d, y=%d loaded in %.3fs",
                type(self.loader).__name__,
                z,
                x,
                y,
                elapsed,
            )
            callback(img, z, x, y)

        self.loader.get_tile_async(z, x, y, wrapped_callback)
