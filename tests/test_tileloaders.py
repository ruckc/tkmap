import tempfile
import unittest
from pathlib import Path

import PIL.Image

from tkmap.tileloaders.base import ChainedTileLoader, TileLoader
from tkmap.tileloaders.disk_cache import DiskCacheTileLoader
from tkmap.tileloaders.error_cache import ErrorCacheTileLoader
from tkmap.tileloaders.memory_cache import MemoryCacheTileLoader


class DummyLoader(TileLoader):
    def __init__(self):
        self.calls = []
        self.should_error = False
        self.img = PIL.Image.new("RGBA", (1, 1), (255, 0, 0, 255))  # Dummy image

    def get_tile_async(self, z, x, y, callback):
        self.calls.append((z, x, y))
        if self.should_error:
            callback(Exception("fail"), z, x, y)
        else:
            callback(self.img, z, x, y)


class DummyChainedLoader(ChainedTileLoader):
    def __init__(self, next_loader):
        super().__init__(next_loader)
        self._tiles = {}

    def _has_tile(self, z, x, y):
        return (z, x, y) in self._tiles

    def _get_tile_async(self, z, x, y, callback):
        callback(self._tiles.get((z, x, y)), z, x, y)

    def _save_tile(self, z, x, y, img):
        self._tiles[(z, x, y)] = img


class TestErrorCacheTileLoader(unittest.TestCase):
    def test_error_caching(self):
        dummy = DummyLoader()
        loader = ErrorCacheTileLoader(dummy)
        dummy.should_error = True
        results = []
        loader.get_tile_async(1, 2, 3, lambda res, z, x, y: results.append(res))
        loader.get_tile_async(1, 2, 3, lambda res, z, x, y: results.append(res))
        self.assertIsInstance(results[0], Exception)
        self.assertIsInstance(results[1], Exception)
        self.assertEqual(str(results[1]), "Tile previously errored")


class TestDiskCacheTileLoader(unittest.TestCase):
    def test_disk_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            dummy = DummyLoader()
            loader = DiskCacheTileLoader(dummy, Path(tmpdir))
            img = PIL.Image.new("RGBA", (1, 1), (0, 255, 0, 255))
            loader._save_tile(1, 2, 3, img)
            self.assertTrue(loader._has_tile(1, 2, 3))
            called = []
            loader._get_tile_async(1, 2, 3, lambda res, z, x, y: called.append(res))
            self.assertIsInstance(called[0], PIL.Image.Image)

    def test_disk_cache_public_api(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # This loader always returns a new image and counts calls
            class CountingLoader(TileLoader):
                def __init__(self):
                    self.calls = 0

                def get_tile_async(self, z, x, y, callback):
                    self.calls += 1
                    img = PIL.Image.new("RGBA", (1, 1), (self.calls, 0, 0, 255))
                    callback(img, z, x, y)

            counting = CountingLoader()
            loader = DiskCacheTileLoader(counting, Path(tmpdir))
            called = []
            # First call: should hit CountingLoader
            loader.get_tile_async(1, 2, 3, lambda res, z, x, y: called.append(res))
            self.assertEqual(counting.calls, 1)
            # Second call: should hit disk cache, not CountingLoader
            loader.get_tile_async(1, 2, 3, lambda res, z, x, y: called.append(res))
            self.assertEqual(counting.calls, 1)
            self.assertIsInstance(called[0], PIL.Image.Image)
            self.assertIsInstance(called[1], PIL.Image.Image)
            # The images should be identical (from cache)
            self.assertEqual(list(called[0].getdata()), list(called[1].getdata()))


class TestMemoryCacheTileLoader(unittest.TestCase):
    def test_memory_cache(self):
        dummy = DummyLoader()
        loader = MemoryCacheTileLoader(dummy, max_cache_size=2)
        img1 = PIL.Image.new("RGBA", (1, 1), (1, 2, 3, 255))
        img2 = PIL.Image.new("RGBA", (1, 1), (4, 5, 6, 255))
        img3 = PIL.Image.new("RGBA", (1, 1), (7, 8, 9, 255))
        loader._save_tile(1, 2, 3, img1)
        loader._save_tile(1, 2, 4, img2)
        loader._save_tile(1, 2, 5, img3)
        self.assertFalse(loader._has_tile(1, 2, 3))  # LRU evicted
        self.assertTrue(loader._has_tile(1, 2, 4))
        self.assertTrue(loader._has_tile(1, 2, 5))
        called = []
        loader._get_tile_async(1, 2, 4, lambda res, z, x, y: called.append(res))
        self.assertIsInstance(called[0], PIL.Image.Image)

    def test_memory_cache_public_api(self):
        # This loader always returns a new image and counts calls
        class CountingLoader(TileLoader):
            def __init__(self):
                self.calls = 0

            def get_tile_async(self, z, x, y, callback):
                self.calls += 1
                img = PIL.Image.new("RGBA", (1, 1), (self.calls, 0, 0, 255))
                callback(img, z, x, y)

        counting = CountingLoader()
        loader = MemoryCacheTileLoader(counting, max_cache_size=2)
        called = []
        # First call: should hit CountingLoader
        loader.get_tile_async(1, 2, 3, lambda res, z, x, y: called.append(res))
        self.assertEqual(counting.calls, 1)
        # Second call: should hit memory cache, not CountingLoader
        loader.get_tile_async(1, 2, 3, lambda res, z, x, y: called.append(res))
        self.assertEqual(counting.calls, 1)
        self.assertIsInstance(called[0], PIL.Image.Image)
        self.assertIsInstance(called[1], PIL.Image.Image)
        self.assertEqual(list(called[0].getdata()), list(called[1].getdata()))
        # Add more tiles to evict the first one
        loader.get_tile_async(1, 2, 4, lambda *_: None)
        loader.get_tile_async(1, 2, 5, lambda *_: None)
        # Now the first tile should be evicted,
        # so a new call should hit CountingLoader again
        loader.get_tile_async(1, 2, 3, lambda res, z, x, y: called.append(res))
        self.assertEqual(len(loader._lru_cache), 2)


class TestChainedTileLoader(unittest.TestCase):
    def test_chain_calls_next(self):
        class DummyNext(TileLoader):
            def get_tile_async(self, z, x, y, callback):
                img = PIL.Image.new("RGBA", (1, 1), (123, 123, 123, 255))
                callback(img, z, x, y)

        next_loader = DummyNext()
        loader = DummyChainedLoader(next_loader)
        called = []
        loader.get_tile_async(1, 2, 3, lambda res, z, x, y: called.append(res))
        self.assertIsInstance(called[0], PIL.Image.Image)
        # Now save a tile and test it is returned directly
        img2 = PIL.Image.new("RGBA", (1, 1), (200, 200, 200, 255))
        loader._save_tile(1, 2, 3, img2)
        called2 = []
        loader.get_tile_async(1, 2, 3, lambda res, z, x, y: called2.append(res))
        self.assertIs(called2[0], img2)

    def test_chain_caching(self):
        class CountingNext(TileLoader):
            def __init__(self):
                self.calls = 0
                self.img = PIL.Image.new("RGBA", (1, 1), (123, 123, 123, 255))
            def get_tile_async(self, z, x, y, callback):
                self.calls += 1
                callback(self.img, z, x, y)

        next_loader = CountingNext()
        loader = DummyChainedLoader(next_loader)
        called = []
        # First call: should call next_loader
        loader.get_tile_async(1, 2, 3, lambda res, z, x, y: called.append(res))
        self.assertIsInstance(called[0], PIL.Image.Image)
        self.assertEqual(next_loader.calls, 1)
        # Second call: should come from cache, not call next_loader
        called2 = []
        loader.get_tile_async(1, 2, 3, lambda res, z, x, y: called2.append(res))
        self.assertIs(called2[0], called[0])
        self.assertEqual(next_loader.calls, 1)


if __name__ == "__main__":
    unittest.main()
