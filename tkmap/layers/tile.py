import tkinter as tk

from .layer import Layer


class TileLayer(Layer):
    def __init__(
        self, tile_loader, tile_size, photo_image_cls, name="BaseMap", visible=True
    ):
        super().__init__(visible, name)
        self.tile_loader = tile_loader
        self.tile_size = tile_size
        self.photo_image_cls = photo_image_cls
        self._tile_images = {}

    def draw(self, canvas, viewport):
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

            def draw_image(img, z, x, y, tile=tile):
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
