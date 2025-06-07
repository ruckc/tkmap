import tkinter as tk
from typing import Any


class Layer:
    def __init__(self, visible: bool = True, name: str = "") -> None:
        self.visible: bool = visible
        self.name: str = name

    def draw(self, canvas: tk.Canvas, viewport: Any) -> None:
        """Draw the layer on the canvas using the viewport."""
        raise NotImplementedError

    def show(self) -> None:
        self.visible = True

    def hide(self) -> None:
        self.visible = False


class GroupLayer(Layer):
    def __init__(self, name: str = "Group", visible: bool = True) -> None:
        super().__init__(visible, name)
        self.layers: list[Layer] = []
        self._layer_dict: dict[str, Layer] = {}

    def add_layer(self, layer: Layer) -> None:
        self.layers.append(layer)
        self._layer_dict[layer.name] = layer

    def remove_layer(self, name: str) -> None:
        layer = self._layer_dict.pop(name, None)
        if layer:
            self.layers.remove(layer)

    def show_layer(self, name: str) -> None:
        if name in self._layer_dict:
            self._layer_dict[name].show()

    def hide_layer(self, name: str) -> None:
        if name in self._layer_dict:
            self._layer_dict[name].hide()

    def draw(self, canvas: tk.Canvas, viewport: Any) -> None:
        if not self.visible:
            return
        for layer in self.layers:
            layer.draw(canvas, viewport)
