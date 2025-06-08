"""Layer base classes for tkmap: abstract Layer, GroupLayer, and helpers."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import tkinter as tk

    from tkmap.viewport import Viewport


class Layer:
    """Base class for all map layers."""

    def __init__(self, visible: bool = True, name: str = "") -> None:  # noqa: FBT001, FBT002
        """Initialize a Layer.

        Args:
            visible: Whether the layer is visible.
            name: Name of the layer.

        """
        self.visible = visible
        self.name = name

    def draw(self, canvas: "tk.Canvas", viewport: "Viewport") -> None:
        """Draw the layer on the canvas using the viewport."""
        raise NotImplementedError

    def show(self) -> None:
        """Show the layer."""
        self.visible = True

    def hide(self) -> None:
        """Hide the layer."""
        self.visible = False


class GroupLayer(Layer):
    """A layer that groups multiple sub-layers for collective control."""

    def __init__(self, name: str = "Group", visible: bool = True) -> None:  # noqa: FBT001, FBT002
        """Initialize a GroupLayer.

        Args:
            name: Name of the group layer.
            visible: Whether the group is visible.

        """
        super().__init__(visible, name)
        self.layers = []
        self._layer_dict = {}

    def add_layer(self, layer: Layer) -> None:
        """Add a sub-layer to the group."""
        self.layers.append(layer)
        self._layer_dict[layer.name] = layer

    def remove_layer(self, name: str) -> None:
        """Remove a sub-layer from the group by name."""
        layer = self._layer_dict.pop(name, None)
        if layer:
            self.layers.remove(layer)

    def show_layer(self, name: str) -> None:
        """Show a sub-layer by name."""
        if name in self._layer_dict:
            self._layer_dict[name].show()

    def hide_layer(self, name: str) -> None:
        """Hide a sub-layer by name."""
        if name in self._layer_dict:
            self._layer_dict[name].hide()

    def draw(self, canvas: "tk.Canvas", viewport: "Viewport") -> None:
        """Draw all visible sub-layers in the group."""
        if not self.visible:
            return
        for layer in self.layers:
            layer.draw(canvas, viewport)
