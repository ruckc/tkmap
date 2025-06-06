import tkinter as tk
import unittest

from tkmap.map_widget import MapWidget


class TestMapWidget(unittest.TestCase):
    def test_init(self):
        root = tk.Tk()
        widget = MapWidget(root)
        self.assertIsInstance(widget, MapWidget)
        root.destroy()


if __name__ == "__main__":
    unittest.main()
