from pathlib import Path

from PIL import Image

from .base import ChainedTileLoader, TileCallback


class DiskCacheTileLoader(ChainedTileLoader):
    def __init__(
        self,
        next_loader,
        cache_dir: Path,
    ):
        super().__init__(next_loader)
        self.cache_dir = cache_dir

    @property
    def cache_dir(self) -> Path:
        """Get the directory where tiles are cached."""
        return self._cache_dir

    @cache_dir.setter
    def cache_dir(self, cache_dir: Path) -> None:
        """Set the directory where tiles will be cached."""
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"{type(self).__name__}: Cache directory set to {self._cache_dir}")

    def _get_tile_path(self, z: int, x: int, y: int) -> Path:
        return self.cache_dir / str(z) / str(x) / f"{y}.png"

    def _has_tile(self, z: int, x: int, y: int) -> bool:
        return self._get_tile_path(z, x, y).exists()

    def _get_tile_async(
        self,
        z: int,
        x: int,
        y: int,
        callback: TileCallback,
    ) -> None:
        tile_path = self._get_tile_path(z, x, y)
        if not tile_path.exists():
            callback(None, z, x, y)
            return
        try:
            img = Image.open(tile_path).convert("RGBA")
            callback(img, z, x, y)
        except Exception as e:
            callback(e, z, x, y)

    def _save_tile(self, z: int, x: int, y: int, img: Image.Image) -> None:
        tile_path = self._get_tile_path(z, x, y)
        tile_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            img.save(tile_path, format="PNG")
        except Exception as e:
            print(f"{type(self).__name__}: Failed to save tile {z}/{x}/{y}: {e}")
