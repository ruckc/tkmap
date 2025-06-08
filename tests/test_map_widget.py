# ruff: noqa: D100,D101,D103,D107
import tkinter as tk
from typing import Any

from tkmap.map_widget import MapWidget


class NotAMapWidgetError(TypeError):
    def __init__(self, widget: Any) -> None:  # noqa: ANN401
        msg = f"{widget!r} is not an instance of MapWidget"
        super().__init__(msg)


def test_map_widget_init() -> None:
    root = tk.Tk()
    widget = MapWidget(root)
    if not isinstance(widget, MapWidget):
        raise NotAMapWidgetError(widget)
    root.destroy()
