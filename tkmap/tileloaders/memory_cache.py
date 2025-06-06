from collections import OrderedDict

from PIL import Image

from .base import ChainedTileLoader, TileCallback


class MemoryCacheTileLoader(ChainedTileLoader):
    def __init__(
        self,
        next_loader,
        max_cache_size: int = 256,
    ):
        super().__init__(next_loader)
        self.max_cache_size = max_cache_size
        self._lru_cache = OrderedDict()  # key: (z, x, y), value: tk.PhotoImage

    def _get_key(self, z: int, x: int, y: int) -> tuple[int, int, int]:
        return (z, x, y)

    def _has_tile(self, z: int, x: int, y: int) -> bool:
        return self._get_key(z, x, y) in self._lru_cache

    def _save_tile(self, z: int, x: int, y: int, img: Image.Image) -> None:
        self._lru_cache[self._get_key(z, x, y)] = img
        # Maintain LRU cache size
        if len(self._lru_cache) > self.max_cache_size:
            self._lru_cache.popitem(last=False)

    def _get_tile_async(
        self,
        z: int,
        x: int,
        y: int,
        callback: TileCallback,
    ) -> None:
        key = self._get_key(z, x, y)
        if key in self._lru_cache:
            img = self._lru_cache[key]
            if img is not None:
                # Move to end to mark as recently used
                self._lru_cache.move_to_end(key)
            callback(img, z, x, y)
        else:
            callback(None, z, x, y)
