import time

from .base import TileCallback, TileLoader


class LoggingTileLoader(TileLoader):
    """
    A tile loader that logs tile requests and the time taken for each tile to load.
    Wraps any other tile loader.
    """

    def __init__(self, loader: TileLoader):
        """
        Initialize the LoggingTileLoader with a next loader.

        :param loader: The next tile loader to wrap.
        """
        self.loader = loader

    def get_tile_async(self, z: int, x: int, y: int, callback: TileCallback) -> None:
        request_time = time.time()

        def wrapped_callback(img, z, x, y):
            elapsed = time.time() - request_time
            print(
                f"[LoggingTileLoader] Tile z={z}, x={x}, y={y} loaded in {elapsed:.3f}s"
            )
            callback(img, z, x, y)

        self.loader.get_tile_async(z, x, y, wrapped_callback)
