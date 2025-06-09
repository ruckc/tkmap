"""Demo application for tkmap.

This script launches a Tkinter-based GUI that displays an interactive
OpenStreetMap viewer using the tkmap library. It demonstrates how to use
MapWidget, tile loading, and event handling for mouse movement and viewport
changes.
"""

import logging
import signal
import tkinter as tk
from pathlib import Path

import requests
from platformdirs import user_cache_dir

from tkmap import LonLat, MapWidget
from tkmap.events import MouseMovedEvent, ViewportChangeEvent
from tkmap.tileloaders.default import DefaultTileLoader

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("PIL").setLevel(logging.WARNING)


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

    # Add a toolbar frame at the top for the address bar and button
    toolbar = tk.Frame(root)
    toolbar.pack(side="top", fill="x")

    # Add a status bar with two labels (left: location, right: viewport)
    status_frame = tk.Frame(root, relief="sunken", bd=1)
    status_frame.pack(side="bottom", fill="x")
    location_var = tk.StringVar()
    viewport_var = tk.StringVar()
    location_label = tk.Label(status_frame, textvariable=location_var, anchor="w")
    location_label.pack(side="left", fill="x", expand=True)
    viewport_label = tk.Label(status_frame, textvariable=viewport_var, anchor="e")
    viewport_label.pack(side="right")

    main_frame = tk.Frame(root)
    main_frame.pack(fill="both", expand=True)

    # Now pack the map widget so it fills the space between toolbar and status bar
    map_widget = MapWidget(
        main_frame,
        center=LonLat(0, 0),
        zoom=2,
        tile_loader=tile_loader,
    )  # type: ignore[parent]
    map_widget.pack(fill="both", expand=True)

    def update_location(event: MouseMovedEvent) -> None:
        """Update the status bar with the current mouse latitude and longitude."""
        location_var.set(f"Lat: {event.lonlat.lat:.6f}, Lon: {event.lonlat.lon:.6f}")

    def update_viewport(event: ViewportChangeEvent) -> None:
        """Update the status bar with the current viewport center and zoom."""
        viewport_var.set(
            f"Viewport Center: {event.center.lat:.6f}, {event.center.lon:.6f}, "
            f"Zoom: {event.zoom}",
        )

    map_widget.on_mouse_moved(update_location)
    map_widget.on_viewport_change(update_viewport)

    address_var = tk.StringVar(value=tile_loader.tile_url)
    address_bar = tk.Entry(
        toolbar,
        textvariable=address_var,
        font=("Consolas", 10),
        width=60,
    )
    address_bar.pack(side="left", fill="x", expand=True, padx=(2, 0), pady=2)

    def apply_address_change(_: object = None) -> None:
        """Apply a new tile URL from the address bar and refresh the map."""
        # Changing the tile URL dynamically clears the various transient caches inside
        # the default loader
        tile_loader.tile_url = address_var.get()
        map_widget.redraw(flush=True)

    address_button = tk.Button(
        toolbar,
        text="Set Tile URL",
        command=apply_address_change,
    )
    address_button.pack(side="left", padx=4, pady=2)

    address_bar.bind("<Return>", apply_address_change)

    # Explicitly set the close protocol to root.destroy to ensure clean exit
    root.protocol("WM_DELETE_WINDOW", root.destroy)

    # Start the remote fetch queue processing and ties it to the tkinter main loop
    # The interval_ms controls how often the queue is processed
    tile_loader.start_remote_fetch_queue_processing(
        root.winfo_toplevel(),
        interval_ms=100,
    )
    root.mainloop()


if __name__ == "__main__":
    main()
