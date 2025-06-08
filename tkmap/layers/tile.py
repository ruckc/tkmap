"""TileLayer for tkmap: renders map tiles using a TileLoader on a Tkinter canvas."""

import tkinter as tk
from collections.abc import Callable

from tkmap.model import VisibleTile
from tkmap.tileloaders.base import TileLoader
from tkmap.viewport import Viewport

from .layer import Layer


class TileLayer(Layer):
    """A map layer for rendering raster map tiles."""

    def __init__(
        self,
        tile_loader: TileLoader,
        tile_size: int,
        photo_image_cls: Callable,
        name: str = "BaseMap",
        visible: bool = True,  # noqa: FBT001, FBT002
    ) -> None:
        """Initialize a TileLayer.

        Args:
            tile_loader: The tile loader to fetch tiles.
            tile_size: The size of each tile in pixels.
            photo_image_cls: The PhotoImage class to use for rendering.
            name: Name of the layer.
            visible: Whether the layer is visible.

        """
        super().__init__(visible, name)
        self.tile_loader = tile_loader
        self.tile_size = tile_size
        self.photo_image_cls = photo_image_cls
        self._tile_images = {}

    def draw(self, canvas: tk.Canvas, viewport: Viewport) -> None:
        """Draw the visible map tiles on the canvas using the viewport."""
        if not self.visible:
            return
        tiles = viewport.visible_area.tiles
        visible_keys = {(tile.z, tile.x, tile.y) for tile in tiles}
        self._tile_images = {
            k: v for k, v in self._tile_images.items() if k in visible_keys
        }
        zoom = viewport.zoom
        tile_size = self.tile_size
        n = 2**zoom
        world_px_width = tile_size * n
        for tile in tiles:

            def draw_image(
                img: object,
                z: int,
                x: int,
                y: int,
                tile: VisibleTile = tile,
            ) -> None:
                if img is not None and not isinstance(img, Exception):
                    photo = self.photo_image_cls(img)
                    self._tile_images[(z, x, y)] = photo
                    for offset in range(-1, 2):
                        sx = tile.screen.x + offset * world_px_width
                        if sx + tile_size > 0 and sx < canvas.winfo_width():
                            canvas.create_image(
                                sx,
                                tile.screen.y,
                                image=photo,
                                anchor=tk.NW,
                            )

            self.tile_loader.get_tile_async(tile.z, tile.x, tile.y, draw_image)
