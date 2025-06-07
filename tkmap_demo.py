# Demo app for tkmap
import logging
import signal
import tkinter as tk
from pathlib import Path

import requests
from platformdirs import user_cache_dir

from tkmap import LonLat, MapWidget
from tkmap.tileloaders.default import DefaultTileLoader


def main():
    # Configure logging for trace level
    logging.basicConfig(
        level=logging.DEBUG,  # Custom TRACE level
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logging.getLogger("PIL").setLevel(logging.INFO)  # Reduce PIL logging noise

    tile_loader = DefaultTileLoader(
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        base_cache_dir=Path(user_cache_dir("tkmap")) / "tilecache",
        requests_session=requests.Session(),
    )

    root = tk.Tk()
    # Allow Ctrl+C to exit the app cleanly
    signal.signal(signal.SIGINT, lambda sig, frame: root.destroy())
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

    # Now pack the map widget so it fills the space between toolbar and status bar
    map_widget = MapWidget(root, center=LonLat(0, 0), zoom=2, tile_loader=tile_loader)
    map_widget.pack(fill="both", expand=True)

    def update_location(event):
        location_var.set(f"Lat: {event.lonlat.lat:.6f}, Lon: {event.lonlat.lon:.6f}")

    def update_viewport(event):
        viewport_var.set(
            f"Viewport Center: {event.center.lat:.6f}, {event.center.lon:.6f}, "
            f"Zoom: {event.zoom}"
        )

    map_widget.on_mouse_moved(update_location)
    map_widget.on_viewport_change(update_viewport)

    address_var = tk.StringVar(value=tile_loader.tile_url)
    address_bar = tk.Entry(
        toolbar, textvariable=address_var, font=("Consolas", 10), width=60
    )
    address_bar.pack(side="left", fill="x", expand=True, padx=(2, 0), pady=2)

    def apply_address_change(event=None):
        # Changing the tile URL dynamically clears the various transient caches inside
        # the default loader
        tile_loader.tile_url = address_var.get()
        map_widget.redraw(flush=True)

    address_button = tk.Button(
        toolbar, text="Set Tile URL", command=apply_address_change
    )
    address_button.pack(side="left", padx=4, pady=2)

    address_bar.bind("<Return>", apply_address_change)

    # Explicitly set the close protocol to root.destroy to ensure clean exit
    root.protocol("WM_DELETE_WINDOW", root.destroy)

    # Start the remote fetch queue processing and ties it to the tkinter main loop
    # The interval_ms controls how often the queue is processed
    tile_loader.start_remote_fetch_queue_processing(
        root.winfo_toplevel(), interval_ms=40
    )
    root.mainloop()


if __name__ == "__main__":
    main()
