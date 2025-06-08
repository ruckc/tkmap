"""MemoryCacheTileLoader for tkmap: in-memory LRU tile cache backend."""

import logging
from collections import OrderedDict

from PIL import Image

from .base import ChainedTileLoader, TileCallback, TileLoader

logger = logging.getLogger(__name__)


class MemoryCacheTileLoader(ChainedTileLoader):
    """Tile loader that caches tiles in memory using LRU strategy."""

    def __init__(
        self,
        next_loader: TileLoader,
        max_cache_size: int = 256,
    ) -> None:
        """Initialize the memory cache tile loader.

        Args:
            next_loader: The next tile loader in the chain.
            max_cache_size: Maximum number of tiles to cache in memory.

        """
        super().__init__(next_loader)
        self.max_cache_size = max_cache_size
        self._lru_cache = OrderedDict()  # key: (z, x, y), value: tk.PhotoImage

    def _get_key(self, z: int, x: int, y: int) -> tuple[int, int, int]:
        """Return the cache key for a tile."""
        return (z, x, y)

    def _has_tile(self, z: int, x: int, y: int) -> bool:
        """Return True if the tile is present in memory cache."""
        return self._get_key(z, x, y) in self._lru_cache

    def _save_tile(self, z: int, x: int, y: int, img: Image.Image) -> None:
        """Save a tile image to memory cache."""
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
        """Fetch a tile from memory cache asynchronously."""
        key = self._get_key(z, x, y)
        if key in self._lru_cache:
            img = self._lru_cache[key]
            if img is not None:
                # Move to end to mark as recently used
                self._lru_cache.move_to_end(key)
            callback(img, z, x, y)
        else:
            callback(None, z, x, y)

    def clear(self) -> None:
        """Clear the memory cache."""
        logger.log(logging.DEBUG, "%s: Clearing memory cache.", type(self).__name__)
        self._lru_cache.clear()
