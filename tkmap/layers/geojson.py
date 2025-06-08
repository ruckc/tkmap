"""GeoJSONLayer for tkmap: render GeoJSON features on a Tkinter map widget."""

import logging
import tkinter as tk
from collections.abc import Callable

from geojson import FeatureCollection

from tkmap.viewport import Viewport

from .layer import Layer

logger = logging.getLogger(__name__)


class GeoJSONLayer(Layer):
    """A map layer for rendering GeoJSON data on a Tkinter canvas."""

    def __init__(
        self,
        name: str,
        data: FeatureCollection,
        visible: bool = True,  # noqa: FBT001, FBT002
        style_func: Callable[[dict], dict] = lambda _: {},
    ) -> None:
        """Initialize a GeoJSONLayer.

        Args:
            name: Name of the layer.
            data: GeoJSON FeatureCollection.
            visible: Whether the layer is visible.
            style_func: Function to style features.

        """
        super().__init__(visible, name)
        self.data = data  # User-defined GeoJSON data
        self.style_func = style_func

    def draw(self, canvas: tk.Canvas, viewport: Viewport) -> None:
        """Draw the GeoJSON features on the canvas using the viewport."""
        if not self.visible or self.data is None:
            return
        pixel_buffer = 20  # You can adjust this buffer as needed
        width = viewport.width
        height = viewport.height

        def in_viewport(sx: float, sy: float) -> bool:
            return (
                -pixel_buffer <= sx <= width + pixel_buffer
                and -pixel_buffer <= sy <= height + pixel_buffer
            )

        for feature in self.data["features"]:
            self._draw_feature(canvas, viewport, feature, in_viewport, width, height)

    # ruff: noqa: PLR0913
    def _draw_feature(
        self,
        canvas: tk.Canvas,
        viewport: Viewport,
        feature: dict,
        in_viewport: Callable[[float, float], bool],
        width: int,
        height: int,
    ) -> None:
        """Draw a single GeoJSON feature on the canvas."""
        geometry = feature["geometry"]
        style = self.style_func(feature)
        geom_type = geometry["type"]
        draw_methods: dict[
            str,
            Callable[
                [
                    tk.Canvas,
                    Viewport,
                    dict,
                    dict,
                    Callable[[float, float], bool],
                ],
                None,
            ],
        ] = {
            "Point": self._draw_point,
            "LineString": self._draw_linestring,
            "Polygon": self._draw_polygon,
            "MultiPoint": self._draw_multipoint,
            "MultiLineString": self._draw_multilinestring,
            "MultiPolygon": self._draw_multipolygon,
        }
        if geom_type in draw_methods:
            if geom_type == "GeometryCollection":
                self._draw_geometrycollection(
                    canvas,
                    viewport,
                    geometry,
                    style,
                    in_viewport,
                    feature,
                    width,
                    height,
                )
            else:
                draw_methods[geom_type](
                    canvas,
                    viewport,
                    geometry,
                    style,
                    in_viewport,
                )

    def _draw_multipoint(
        self,
        canvas: tk.Canvas,
        viewport: Viewport,
        geometry: dict,
        style: dict,
        in_viewport: Callable[[float, float], bool],
    ) -> None:
        """Draw a MultiPoint geometry."""
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
        viewport: Viewport,
        geometry: dict,
        style: dict,
        in_viewport: Callable[[float, float], bool],
    ) -> None:
        """Draw a MultiLineString geometry."""
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
        viewport: Viewport,
        geometry: dict,
        style: dict,
        in_viewport: Callable[[float, float], bool],
    ) -> None:
        """Draw a MultiPolygon geometry."""
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
        viewport: Viewport,
        geometry: dict,
        _style: dict,
        in_viewport: Callable[[float, float], bool],
        _feature: dict,
        width: int,
        height: int,
    ) -> None:
        """Draw a GeometryCollection geometry."""
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
        viewport: Viewport,
        geometry: dict,
        style: dict,
        in_viewport: Callable[[float, float], bool],
    ) -> None:
        """Draw a Point geometry."""
        lon, lat = geometry["coordinates"]
        sp = viewport.lonlat_to_screen(lon, lat)
        if not in_viewport(sp.x, sp.y):
            return
        r = style.get("radius", 5)
        fill = style.get("fill", "blue")
        outline = style.get("outline", "black")
        canvas.create_oval(
            sp.x - r,
            sp.y - r,
            sp.x + r,
            sp.y + r,
            fill=fill,
            outline=outline,
        )

    def _draw_linestring(
        self,
        canvas: tk.Canvas,
        viewport: Viewport,
        geometry: dict,
        style: dict,
        in_viewport: Callable[[float, float], bool],
    ) -> None:
        """Draw a LineString geometry."""
        coords = geometry["coordinates"]
        screen_coords = [viewport.lonlat_to_screen(lon, lat) for lon, lat in coords]
        if not any(in_viewport(sc.x, sc.y) for sc in screen_coords):
            return
        flat = [coord for sc in screen_coords for coord in (sc.x, sc.y)]
        width_ = style.get("width", 2)
        fill = style.get("fill", "black")
        canvas.create_line(*flat, fill=fill, width=width_)

    def _draw_polygon(
        self,
        canvas: tk.Canvas,
        viewport: Viewport,
        geometry: dict,
        style: dict,
        in_viewport: Callable[[float, float], bool],
    ) -> None:
        """Draw a Polygon geometry."""
        rings = geometry["coordinates"]
        if not rings:
            return
        has_holes = len(rings) > 1
        if has_holes:
            logger.warning(
                "Polygons with holes are not supported due to tkinter canvas "
                "limitations.",
            )

        exterior = rings[0]
        exterior_screen_coords = [
            viewport.lonlat_to_screen(lon, lat) for lon, lat in exterior
        ]
        if not any(in_viewport(sc.x, sc.y) for sc in exterior_screen_coords):
            return
        exterior_flat = [
            coord for sc in exterior_screen_coords for coord in (sc.x, sc.y)
        ]
        fill = style.get("fill", "#3388ff")
        outline = style.get("outline", "black")
        width_ = style.get("width", 2)
        canvas.create_polygon(*exterior_flat, fill=fill, outline=outline, width=width_)
        return
