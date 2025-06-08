"""DiskCacheTileLoader for tkmap: disk-based tile caching backend."""

import logging
from pathlib import Path

from PIL import Image

from .base import ChainedTileLoader, TileCallback, TileLoader

logger = logging.getLogger(__name__)


class DiskCacheTileLoader(ChainedTileLoader):
    """Tile loader that caches tiles on disk."""

    def __init__(
        self,
        next_loader: TileLoader,
        cache_dir: Path,
    ) -> None:
        """Initialize the disk cache tile loader.

        Args:
            next_loader: The next tile loader in the chain.
            cache_dir: Directory for tile cache.

        """
        super().__init__(next_loader)
        self.cache_dir = cache_dir

    @property
    def cache_dir(self) -> Path:
        """Return the directory where tiles are cached."""
        return self._cache_dir

    @cache_dir.setter
    def cache_dir(self, cache_dir: Path) -> None:
        """Set the directory where tiles will be cached."""
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        logger.log(
            logging.INFO,
            "%s: Cache directory set to %s",
            type(self).__name__,
            self._cache_dir,
        )

    def _get_tile_path(self, z: int, x: int, y: int) -> Path:
        """Return the file path for a tile on disk."""
        return self.cache_dir / str(z) / str(x) / f"{y}.png"

    def _has_tile(self, z: int, x: int, y: int) -> bool:
        """Return True if the tile exists on disk."""
        return self._get_tile_path(z, x, y).exists()

    def _get_tile_async(
        self,
        z: int,
        x: int,
        y: int,
        callback: TileCallback,
    ) -> None:
        """Fetch a tile from disk asynchronously."""
        tile_path = self._get_tile_path(z, x, y)
        if not tile_path.exists():
            callback(None, z, x, y)
            return
        try:
            img = Image.open(tile_path).convert("RGBA")
            callback(img, z, x, y)
        except (OSError, ValueError) as e:
            callback(e, z, x, y)

    def _save_tile(self, z: int, x: int, y: int, img: Image.Image) -> None:
        """Save a tile image to disk."""
        tile_path = self._get_tile_path(z, x, y)
        tile_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            img.save(tile_path, format="PNG")
        except (OSError, ValueError) as e:
            logger.log(
                logging.ERROR,
                "%s: Failed to save tile %d/%d/%d: %s",
                type(self).__name__,
                z,
                x,
                y,
                e,
            )
