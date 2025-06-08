"""tkmap.tileloaders package: tile loading and caching backends for map tiles."""

from .base import ChainedTileLoader, TileLoader
from .default import DefaultTileLoader
from .disk_cache import DiskCacheTileLoader
from .error_cache import ErrorCacheTileLoader
from .memory_cache import MemoryCacheTileLoader
from .remote import RemoteTileLoader

__all__ = [
    "ChainedTileLoader",
    "DefaultTileLoader",
    "DiskCacheTileLoader",
    "ErrorCacheTileLoader",
    "MemoryCacheTileLoader",
    "RemoteTileLoader",
    "TileLoader",
]
