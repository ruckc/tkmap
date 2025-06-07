import tkinter as tk

from geojson import FeatureCollection
from PIL import Image, ImageDraw, ImageTk

from tkmap.viewport import Viewport

from .layer import Layer


class GeoJSONLayer(Layer):
    def __init__(
        self,
        name: str,
        data: FeatureCollection,
        visible: bool = True,
        style_func=None,
    ):
        super().__init__(visible, name)
        self.data = data  # User-defined GeoJSON data
        self.style_func = style_func or (lambda feature: {})

    def draw(self, canvas: tk.Canvas, viewport: Viewport):
        if not self.visible or self.data is None:
            return
        pixel_buffer = 20  # You can adjust this buffer as needed
        width = viewport.width
        height = viewport.height

        def in_viewport(sx, sy):
            return (
                -pixel_buffer <= sx <= width + pixel_buffer
                and -pixel_buffer <= sy <= height + pixel_buffer
            )

        for feature in self.data["features"]:
            self._draw_feature(canvas, viewport, feature, in_viewport, width, height)

    def _draw_feature(self, canvas, viewport, feature, in_viewport, width, height):
        geometry = feature["geometry"]
        style = self.style_func(feature)
        geom_type = geometry["type"]
        draw_methods = {
            "Point": self._draw_point,
            "LineString": self._draw_linestring,
            "Polygon": self._draw_polygon,
            "MultiPoint": self._draw_multipoint,
            "MultiLineString": self._draw_multilinestring,
            "MultiPolygon": self._draw_multipolygon,
            "GeometryCollection": self._draw_geometrycollection,
        }
        if geom_type in draw_methods:
            draw_methods[geom_type](
                canvas, viewport, geometry, style, in_viewport, feature, width, height
            )

    def _draw_multipoint(
        self, canvas, viewport, geometry, style, in_viewport, feature, width, height
    ):
        for point in geometry["coordinates"]:
            self._draw_point(
                canvas,
                viewport,
                {"type": "Point", "coordinates": point},
                style,
                in_viewport,
            )

    def _draw_multilinestring(
        self, canvas, viewport, geometry, style, in_viewport, feature, width, height
    ):
        for line in geometry["coordinates"]:
            self._draw_linestring(
                canvas,
                viewport,
                {"type": "LineString", "coordinates": line},
                style,
                in_viewport,
            )

    def _draw_multipolygon(
        self, canvas, viewport, geometry, style, in_viewport, feature, width, height
    ):
        for polygon in geometry["coordinates"]:
            self._draw_polygon(
                canvas,
                viewport,
                {"type": "Polygon", "coordinates": polygon},
                style,
                in_viewport,
            )

    def _draw_geometrycollection(
        self, canvas, viewport, geometry, style, in_viewport, feature, width, height
    ):
        for geom in geometry["geometries"]:
            self._draw_feature(
                canvas,
                viewport,
                {"geometry": geom, "type": "Feature"},
                in_viewport,
                width,
                height,
            )

    def _draw_point(self, canvas, viewport, geometry, style, in_viewport, *args):
        lon, lat = geometry["coordinates"]
        sx, sy = viewport.lonlat_to_screen(lon, lat)
        if not in_viewport(sx, sy):
            return
        r = style.get("radius", 5)
        fill = style.get("fill", "blue")
        outline = style.get("outline", "black")
        canvas.create_oval(sx - r, sy - r, sx + r, sy + r, fill=fill, outline=outline)

    def _draw_linestring(self, canvas, viewport, geometry, style, in_viewport, *args):
        coords = geometry["coordinates"]
        screen_coords = [viewport.lonlat_to_screen(lon, lat) for lon, lat in coords]
        if not any(in_viewport(sx, sy) for sx, sy in screen_coords):
            return
        flat = [coord for xy in screen_coords for coord in xy]
        width_ = style.get("width", 2)
        fill = style.get("fill", "black")
        canvas.create_line(*flat, fill=fill, width=width_)

    def _draw_polygon(self, canvas, viewport, geometry, style, in_viewport, *args):
        rings = geometry["coordinates"]
        if not rings:
            return
        has_holes = len(rings) > 1
        if not has_holes:
            exterior = rings[0]
            exterior_screen_coords = [
                viewport.lonlat_to_screen(lon, lat) for lon, lat in exterior
            ]
            if not any(in_viewport(sx, sy) for sx, sy in exterior_screen_coords):
                return
            exterior_flat = [coord for xy in exterior_screen_coords for coord in xy]
            fill = style.get("fill", "#3388ff")
            outline = style.get("outline", "black")
            width_ = style.get("width", 2)
            canvas.create_polygon(
                *exterior_flat, fill=fill, outline=outline, width=width_
            )
            return
        # --- Pillow rendering for polygons with holes ---

        width = viewport.width
        height = viewport.height
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img, "RGBA")
        # Convert all rings to screen coordinates
        screen_rings = []
        for ring in rings:
            screen_ring = [viewport.lonlat_to_screen(lon, lat) for lon, lat in ring]
            screen_rings.append(screen_ring)
        # Pillow expects (x, y) tuples
        exterior = screen_rings[0]
        holes = screen_rings[1:]
        fill = style.get("fill", "#3388ff")
        outline = style.get("outline", "black")
        width_ = style.get("width", 2)
        # Draw the polygon with holes using Pillow's "polygon" with holes
        draw.polygon(exterior, fill=fill, outline=outline)
        for hole in holes:
            draw.polygon(hole, fill=(0, 0, 0, 0))  # Transparent fill for holes
        # Draw outline for exterior and holes
        draw.line(exterior + [exterior[0]], fill=outline, width=width_)
        for hole in holes:
            draw.line(hole + [hole[0]], fill=outline, width=width_)
        # Convert Pillow image to Tkinter PhotoImage and draw on canvas
        tk_img = ImageTk.PhotoImage(img)
        canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
        # Prevent garbage collection
        if not hasattr(canvas, "_geojson_images"):
            canvas._geojson_images = []
        canvas._geojson_images.append(tk_img)
        # Add more geometry types as needed
