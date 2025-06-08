"""ErrorCacheTileLoader for tkmap: caches tile load errors to avoid repeated fetches."""

import logging

from .base import ImageOrException, TileCallback, TileLoader

logger = logging.getLogger(__name__)


class ErrorCacheTileLoader(TileLoader):
    """Tile loader that caches errors for failed tile loads."""

    def __init__(self, next_loader: TileLoader) -> None:
        """Initialize the error cache tile loader.

        Args:
            next_loader: The next tile loader in the chain.

        """
        self._next_loader = next_loader
        self._errored_tiles = set()

    def get_tile_async(
        self,
        z: int,
        x: int,
        y: int,
        callback: TileCallback,
    ) -> None:
        """Fetch a tile asynchronously, returning a cached error if present."""
        key = (z, x, y)
        if key in self._errored_tiles:
            callback(Exception("Tile previously errored"), z, x, y)
        else:

            def on_result(img: ImageOrException, z: int, x: int, y: int) -> None:
                if isinstance(img, Exception):
                    logger.log(
                        logging.ERROR,
                        "%s: Tile %d/%d/%d failed to load: %s",
                        type(self).__name__,
                        z,
                        x,
                        y,
                        img,
                    )
                    self._errored_tiles.add(key)
                callback(img, z, x, y)

            self._next_loader.get_tile_async(z, x, y, on_result)

    def clear(self) -> None:
        """Clear the error cache."""
        logger.log(logging.DEBUG, "%s: Clearing error cache.", type(self).__name__)
        self._errored_tiles.clear()
