# tkmap

A Tkinter-based interactive map widget for Python, supporting OpenStreetMap and custom tile sources. Easily embed a map in your Tkinter GUI, handle user interaction, and respond to map events.

## Features
- Fast, smooth map panning and zooming
- Customizable tile sources (e.g., OpenStreetMap)
- Mouse and viewport event handling
- Simple integration with Tkinter applications

## Installation
Install via pip (after cloning or when available on PyPI):

```sh
pip install tkmap
```

## Minimal Example
This example launches a Tkinter window with an interactive OpenStreetMap viewer:

```python
import tkinter as tk
from pathlib import Path
import requests
from platformdirs import user_cache_dir
from tkmap import LonLat, MapWidget
from tkmap.tileloaders.default import DefaultTileLoader

def main():
    tile_loader = DefaultTileLoader(
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        base_cache_dir=Path(user_cache_dir("tkmap")) / "tile_cache",
        requests_session=requests.Session(),
    )
    root = tk.Tk()
    root.geometry("800x600")
    root.title("tkmap OpenStreetMap Demo")
    map_widget = MapWidget(
        root,
        center=LonLat(0, 0),
        zoom=2,
        tile_loader=tile_loader,
    )
    map_widget.pack(fill="both", expand=True)
    tile_loader.start_remote_fetch_queue_processing(root.winfo_toplevel(), interval_ms=100)
    root.mainloop()

if __name__ == "__main__":
    main()
```

## Handling Events
You can respond to mouse movement and viewport changes using event callbacks:

```python
from tkmap.events import MouseMovedEvent, ViewportChangeEvent

# ... (setup code as above)

def on_mouse_moved(event: MouseMovedEvent):
    print(f"Mouse at lat={event.lonlat.lat:.6f}, lon={event.lonlat.lon:.6f}")

def on_viewport_changed(event: ViewportChangeEvent):
    print(f"Viewport center: {event.center.lat:.6f}, {event.center.lon:.6f}, zoom={event.zoom}")

map_widget.on_mouse_moved(on_mouse_moved)
map_widget.on_viewport_change(on_viewport_changed)
```

## License
Apache-2.0
