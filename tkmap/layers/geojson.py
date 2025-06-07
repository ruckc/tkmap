import tkinter as tk
from typing import Any, Callable, Optional

from .layer import Layer


class GeoJSONLayer(Layer):
    def __init__(
        self,
        name: str,
        data: Any,  # FeatureCollection
        visible: bool = True,
        style_func: Optional[Callable[[Any], dict]] = None,
    ) -> None:
        super().__init__(visible, name)
        self.data: Any = data  # User-defined GeoJSON data
        self.style_func: Callable[[Any], dict] = style_func or (lambda feature: {})

    def draw(self, canvas: tk.Canvas, viewport: Any) -> None:
        if not self.visible or self.data is None:
            return
        pixel_buffer = 20  # You can adjust this buffer as needed
        width = viewport.width
        height = viewport.height

        def in_viewport(sx: int, sy: int) -> bool:
            return (
                -pixel_buffer <= sx <= width + pixel_buffer
                and -pixel_buffer <= sy <= height + pixel_buffer
            )

        for feature in self.data["features"]:
            self._draw_feature(canvas, viewport, feature, in_viewport, width, height)

    def _draw_feature(
        self,
        canvas: tk.Canvas,
        viewport: Any,
        feature: Any,
        in_viewport: Callable[[int, int], bool],
        width: int,
        height: int,
    ) -> None:
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
        self,
        canvas: tk.Canvas,
        viewport: Any,
        geometry: dict,
        style: dict,
        in_viewport: Callable[[int, int], bool],
        feature: Any,
        width: int,
        height: int,
    ) -> None:
        for point in geometry["coordinates"]:
            self._draw_point(
                canvas,
                viewport,
                {"type": "Point", "coordinates": point},
                style,
                in_viewport,
            )

    def _draw_multilinestring(
        self,
        canvas: tk.Canvas,
        viewport: Any,
        geometry: dict,
        style: dict,
        in_viewport: Callable[[int, int], bool],
        feature: Any,
        width: int,
        height: int,
    ) -> None:
        for line in geometry["coordinates"]:
            self._draw_linestring(
                canvas,
                viewport,
                {"type": "LineString", "coordinates": line},
                style,
                in_viewport,
            )

    def _draw_multipolygon(
        self,
        canvas: tk.Canvas,
        viewport: Any,
        geometry: dict,
        style: dict,
        in_viewport: Callable[[int, int], bool],
        feature: Any,
        width: int,
        height: int,
    ) -> None:
        for polygon in geometry["coordinates"]:
            self._draw_polygon(
                canvas,
                viewport,
                {"type": "Polygon", "coordinates": polygon},
                style,
                in_viewport,
            )

    def _draw_geometrycollection(
        self,
        canvas: tk.Canvas,
        viewport: Any,
        geometry: dict,
        style: dict,
        in_viewport: Callable[[int, int], bool],
        feature: Any,
        width: int,
        height: int,
    ) -> None:
        for geom in geometry["geometries"]:
            self._draw_feature(
                canvas,
                viewport,
                {"geometry": geom, "type": "Feature"},
                in_viewport,
                width,
                height,
            )

    def _draw_point(
        self,
        canvas: tk.Canvas,
        viewport: Any,
        geometry: dict,
        style: dict,
        in_viewport: Callable[[int, int], bool],
        *args: Any,
    ) -> None:
        lon, lat = geometry["coordinates"]
        sx, sy = viewport.lonlat_to_screen(lon, lat)
        if not in_viewport(sx, sy):
            return
        r = style.get("radius", 5)
        fill = style.get("fill", "blue")
        outline = style.get("outline", "black")
        canvas.create_oval(sx - r, sy - r, sx + r, sy + r, fill=fill, outline=outline)

    def _draw_linestring(
        self,
        canvas: tk.Canvas,
        viewport: Any,
        geometry: dict,
        style: dict,
        in_viewport: Callable[[int, int], bool],
        *args: Any,
    ) -> None:
        coords = geometry["coordinates"]
        screen_coords = [viewport.lonlat_to_screen(lon, lat) for lon, lat in coords]
        if not any(in_viewport(sx, sy) for sx, sy in screen_coords):
            return
        flat = [coord for xy in screen_coords for coord in xy]
        width_ = style.get("width", 2)
        fill = style.get("fill", "black")
        canvas.create_line(*flat, fill=fill, width=width_)

    def _draw_polygon(
        self,
        canvas: tk.Canvas,
        viewport: Any,
        geometry: dict,
        style: dict,
        in_viewport: Callable[[int, int], bool],
        *args: Any,
    ) -> None:
        rings = geometry["coordinates"]
        if not rings:
            return
        has_holes = len(rings) > 1
        if has_holes:
            print("Polygons with holes are not fully supported in Tkinter Canvas.")

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
        canvas.create_polygon(*exterior_flat, fill=fill, outline=outline, width=width_)
