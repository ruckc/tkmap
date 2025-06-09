"""Minimal Demo application for tkmap.

This script launches a Tkinter-based GUI that displays an interactive
OpenStreetMap viewer using the tkmap library. It demonstrates how to use
MapWidget, tile loading, and event handling for mouse movement and viewport
changes.
"""

import signal
import tkinter as tk
from pathlib import Path

import requests
from platformdirs import user_cache_dir

from tkmap import LonLat, MapWidget
from tkmap.tileloaders.default import DefaultTileLoader


def main() -> None:
    """Launch the tkmap OpenStreetMap demo application.

    Sets up the Tkinter window, toolbar, status bar, and the MapWidget.
    Handles tile loading, address bar for changing tile URL, and updates
    status bar with mouse and viewport events.
    """
    tile_loader = DefaultTileLoader(
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        base_cache_dir=Path(user_cache_dir("tkmap")) / "tile_cache",
        requests_session=requests.Session(),
    )

    root = tk.Tk()
    # Allow Ctrl+C to exit the app cleanly
    signal.signal(signal.SIGINT, lambda *_: root.destroy())
    root.geometry("800x600")
    root.title("tkmap OpenStreetMap Demo")

    # Now pack the map widget so it fills the space between toolbar and status bar
    map_widget = MapWidget(
        root,
        center=LonLat(0, 0),
        zoom=2,
        tile_loader=tile_loader,
    )  # type: ignore[parent]
    map_widget.pack(fill="both", expand=True)

    # Start the remote fetch queue processing and ties it to the tkinter main loop
    # The interval_ms controls how often the queue is processed
    tile_loader.start_remote_fetch_queue_processing(
        root.winfo_toplevel(),
        interval_ms=100,
    )
    root.mainloop()


if __name__ == "__main__":
    main()
