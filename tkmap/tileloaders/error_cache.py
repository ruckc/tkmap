from .base import ImageOrException, TileCallback, TileLoader


class ErrorCacheTileLoader(TileLoader):
    def __init__(self, next_loader: TileLoader):
        self._next_loader = next_loader
        self._errored_tiles = set()

    def get_tile_async(
        self,
        z: int,
        x: int,
        y: int,
        callback: TileCallback,
    ) -> None:
        key = (z, x, y)
        if key in self._errored_tiles:
            callback(Exception("Tile previously errored"), z, x, y)
        else:

            def on_result(img: ImageOrException, z: int, x: int, y: int) -> None:
                if isinstance(img, Exception):
                    self._errored_tiles.add(key)
                callback(img, z, x, y)

            self._next_loader.get_tile_async(z, x, y, on_result)
