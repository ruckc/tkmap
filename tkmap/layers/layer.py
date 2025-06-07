class Layer:
    def __init__(self, visible: bool = True, name: str = ""):
        self.visible = visible
        self.name = name

    def draw(self, canvas, viewport):
        """Draw the layer on the canvas using the viewport."""
        raise NotImplementedError

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False


class GroupLayer(Layer):
    def __init__(self, name="Group", visible=True):
        super().__init__(visible, name)
        self.layers = []
        self._layer_dict = {}

    def add_layer(self, layer):
        self.layers.append(layer)
        self._layer_dict[layer.name] = layer

    def remove_layer(self, name):
        layer = self._layer_dict.pop(name, None)
        if layer:
            self.layers.remove(layer)

    def show_layer(self, name):
        if name in self._layer_dict:
            self._layer_dict[name].show()

    def hide_layer(self, name):
        if name in self._layer_dict:
            self._layer_dict[name].hide()

    def draw(self, canvas, viewport):
        if not self.visible:
            return
        for layer in self.layers:
            layer.draw(canvas, viewport)
