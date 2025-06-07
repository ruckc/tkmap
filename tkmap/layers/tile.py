import logging
import tkinter as tk
from typing import Any

from PIL import ImageTk

from tkmap.tileloaders.base import ImageOrException

from .layer import Layer

logger = logging.getLogger(__name__)


class TileLayer(Layer):
    def __init__(
        self,
        tile_loader: Any,
        tile_size: int,
        name: str = "BaseMap",
        visible: bool = True,
    ) -> None:
        super().__init__(visible, name)
        self.tile_loader: Any = tile_loader
        self.tile_size: int = tile_size
        self._tile_images: dict[tuple[int, int, int], ImageTk.PhotoImage] = {}

    def draw(self, canvas: tk.Canvas, viewport: Any) -> None:
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
        canvas_width = canvas.winfo_width()
        for tile in tiles:

            def draw_image(
                img: ImageOrException, z: int, x: int, y: int, tile=tile
            ) -> None:
                if img is not None and not isinstance(img, Exception):
                    photo = ImageTk.PhotoImage(img)
                    self._tile_images[(z, x, y)] = photo
                    for offset in range(-1, 2):
                        sx = tile.screen.x + offset * world_px_width
                        if sx + tile_size > 0 and sx < canvas_width:
                            canvas.create_image(
                                sx,
                                tile.screen.y,
                                image=photo,
                                anchor=tk.NW,
                            )

            self.tile_loader.get_tile_async(tile.z, tile.x, tile.y, draw_image)
