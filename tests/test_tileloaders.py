# ruff: noqa: D100,D101,D102,D103,D107,S101,PLR2004,SLF001,ARG005
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any

import PIL.Image

from tkmap.tileloaders.base import ChainedTileLoader, ImageOrException, TileLoader
from tkmap.tileloaders.disk_cache import DiskCacheTileLoader
from tkmap.tileloaders.error_cache import ErrorCacheTileLoader
from tkmap.tileloaders.memory_cache import MemoryCacheTileLoader


class DummyLoader(TileLoader):
    def __init__(self) -> None:
        self.calls: list[tuple[int, int, int]] = []
        self.should_error: bool = False
        self.img: PIL.Image.Image = PIL.Image.new(
            "RGBA",
            (1, 1),
            (255, 0, 0, 255),
        )  # Dummy image

    def get_tile_async(
        self,
        z: int,
        x: int,
        y: int,
        callback: Callable[[Any, int, int, int], None],
    ) -> None:
        self.calls.append((z, x, y))
        if self.should_error:
            callback(Exception("fail"), z, x, y)
        else:
            callback(self.img, z, x, y)


class DummyChainedLoader(ChainedTileLoader):
    def __init__(self, next_loader: TileLoader) -> None:
        super().__init__(next_loader)
        self._tiles: dict[tuple[int, int, int], PIL.Image.Image] = {}

    def _has_tile(self, z: int, x: int, y: int) -> bool:
        return (z, x, y) in self._tiles

    def _get_tile_async(
        self,
        z: int,
        x: int,
        y: int,
        callback: Callable[[Any, int, int, int], None],
    ) -> None:
        callback(self._tiles.get((z, x, y)), z, x, y)

    def _save_tile(
        self,
        z: int,
        x: int,
        y: int,
        img: PIL.Image.Image,
    ) -> None:
        self._tiles[(z, x, y)] = img


class TestErrorCacheTileLoader:
    def test_error_caching(self) -> None:
        dummy = DummyLoader()
        loader = ErrorCacheTileLoader(dummy)
        dummy.should_error = True
        imgults = []
        loader.get_tile_async(1, 2, 3, lambda img, z, x, y: imgults.append(img))
        loader.get_tile_async(1, 2, 3, lambda img, z, x, y: imgults.append(img))
        assert isinstance(imgults[0], Exception)
        assert isinstance(imgults[1], Exception)
        assert str(imgults[1]) == "Tile previously errored"


class TestDiskCacheTileLoader:
    def test_disk_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dummy = DummyLoader()
            loader = DiskCacheTileLoader(dummy, Path(tmpdir))
            img = PIL.Image.new("RGBA", (1, 1), (0, 255, 0, 255))
            loader._save_tile(1, 2, 3, img)
            assert loader._has_tile(1, 2, 3)
            called = []
            loader._get_tile_async(1, 2, 3, lambda img, z, x, y: called.append(img))
            assert isinstance(called[0], PIL.Image.Image)

    def test_disk_cache_public_api(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            # This loader always returns a new image and counts calls
            class CountingLoader(TileLoader):
                def __init__(self) -> None:
                    self.calls = 0

                def get_tile_async(
                    self,
                    z: int,
                    x: int,
                    y: int,
                    callback: Callable[[Any, int, int, int], None],
                ) -> None:
                    self.calls += 1
                    img = PIL.Image.new(
                        "RGBA",
                        (1, 1),
                        (self.calls, 0, 0, 255),
                    )
                    callback(img, z, x, y)

            counting = CountingLoader()
            loader = DiskCacheTileLoader(counting, Path(tmpdir))
            called = []
            # First call: should hit CountingLoader
            loader.get_tile_async(1, 2, 3, lambda img, z, x, y: called.append(img))
            assert counting.calls == 1
            # Second call: should hit disk cache, not CountingLoader
            loader.get_tile_async(1, 2, 3, lambda img, z, x, y: called.append(img))
            assert counting.calls == 1
            assert isinstance(called[0], PIL.Image.Image)
            assert isinstance(called[1], PIL.Image.Image)
            # The images should be identical (from cache)
            assert list(called[0].getdata()) == list(called[1].getdata())


class TestMemoryCacheTileLoader:
    def test_memory_cache(self) -> None:
        dummy = DummyLoader()
        loader = MemoryCacheTileLoader(dummy, max_cache_size=2)
        img1 = PIL.Image.new("RGBA", (1, 1), (1, 2, 3, 255))
        img2 = PIL.Image.new("RGBA", (1, 1), (4, 5, 6, 255))
        img3 = PIL.Image.new("RGBA", (1, 1), (7, 8, 9, 255))
        loader._save_tile(1, 2, 3, img1)
        loader._save_tile(1, 2, 4, img2)
        loader._save_tile(1, 2, 5, img3)
        assert not loader._has_tile(1, 2, 3)  # LRU evicted
        assert loader._has_tile(1, 2, 4)
        assert loader._has_tile(1, 2, 5)
        called = []
        loader._get_tile_async(1, 2, 4, lambda img, z, x, y: called.append(img))
        assert isinstance(called[0], PIL.Image.Image)

    def test_memory_cache_public_api(self) -> None:
        # This loader always returns a new image and counts calls
        class CountingLoader(TileLoader):
            def __init__(self) -> None:
                self.calls = 0

            def get_tile_async(
                self,
                z: int,
                x: int,
                y: int,
                callback: Callable[[Any, int, int, int], None],
            ) -> None:
                self.calls += 1
                img = PIL.Image.new("RGBA", (1, 1), (self.calls, 0, 0, 255))
                callback(img, z, x, y)

        counting = CountingLoader()
        loader = MemoryCacheTileLoader(counting, max_cache_size=2)
        called = []
        # First call: should hit CountingLoader
        loader.get_tile_async(1, 2, 3, lambda img, z, x, y: called.append(img))
        assert counting.calls == 1
        # Second call: should hit memory cache, not CountingLoader
        loader.get_tile_async(1, 2, 3, lambda img, z, x, y: called.append(img))
        assert counting.calls == 1
        assert isinstance(called[0], PIL.Image.Image)
        assert isinstance(called[1], PIL.Image.Image)
        assert list(called[0].getdata()) == list(called[1].getdata())
        # Add more tiles to evict the first one
        loader.get_tile_async(1, 2, 4, lambda img, z, x, y: called.append(img))
        loader.get_tile_async(1, 2, 5, lambda img, z, x, y: called.append(img))
        # Now the first tile should be evicted,
        # so a new call should hit CountingLoader again
        loader.get_tile_async(1, 2, 3, lambda img, z, x, y: called.append(img))
        assert len(loader._lru_cache) == 2


class TestChainedTileLoader:
    def test_chain_calls_next(self) -> None:
        class DummyNext(TileLoader):
            def get_tile_async(
                self,
                z: int,
                x: int,
                y: int,
                callback: Callable[[ImageOrException, int, int, int], None],
            ) -> None:
                img = PIL.Image.new("RGBA", (1, 1), (123, 123, 123, 255))
                callback(img, z, x, y)

        next_loader = DummyNext()
        loader = DummyChainedLoader(next_loader)
        called = []
        loader.get_tile_async(1, 2, 3, lambda img, z, x, y: called.append(img))
        assert isinstance(called[0], PIL.Image.Image)
        # Now save a tile and test it is returned directly
        img2 = PIL.Image.new("RGBA", (1, 1), (200, 200, 200, 255))
        loader._save_tile(1, 2, 3, img2)
        called2 = []
        loader.get_tile_async(1, 2, 3, lambda img, z, x, y: called2.append(img))
        assert called2[0] is img2

    def test_chain_caching(self) -> None:
        class CountingNext(TileLoader):
            def __init__(self) -> None:
                self.calls = 0
                self.img = PIL.Image.new("RGBA", (1, 1), (123, 123, 123, 255))

            def get_tile_async(
                self,
                z: int,
                x: int,
                y: int,
                callback: Callable[[ImageOrException, int, int, int], None],
            ) -> None:
                self.calls += 1
                callback(self.img, z, x, y)

        next_loader = CountingNext()
        loader = DummyChainedLoader(next_loader)
        called = []
        # First call: should call next_loader
        loader.get_tile_async(1, 2, 3, lambda img, z, x, y: called.append(img))
        assert isinstance(called[0], PIL.Image.Image)
        assert next_loader.calls == 1
        # Second call: should come from cache, not call next_loader
        called2 = []
        loader.get_tile_async(1, 2, 3, lambda img, z, x, y: called2.append(img))
        assert called2[0] is called[0]
        assert next_loader.calls == 1


if __name__ == "__main__":
    unittest.main()
