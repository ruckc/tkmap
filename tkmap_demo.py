# Demo app for tkmap
import tkinter as tk

from tkmap import LonLat, MapWidget


def main():
    root = tk.Tk()
    root.geometry("800x600")
    root.title("tkmap OpenStreetMap Demo")
    map_widget = MapWidget(root, center=LonLat(0, 0), zoom=2)
    map_widget.pack(fill="both", expand=True)

    # Add a status bar with two labels (left: location, right: viewport)
    status_frame = tk.Frame(root, relief="sunken", bd=1)
    status_frame.pack(side="bottom", fill="x")
    location_var = tk.StringVar()
    viewport_var = tk.StringVar()
    location_label = tk.Label(status_frame, textvariable=location_var, anchor="w")
    location_label.pack(side="left", fill="x", expand=True)
    viewport_label = tk.Label(status_frame, textvariable=viewport_var, anchor="e")
    viewport_label.pack(side="right")

    def update_location(event):
        location_var.set(f"Lat: {event.lonlat.lat:.6f}, Lon: {event.lonlat.lon:.6f}")

    def update_viewport(event):
        viewport_var.set(
            f"Viewport Center: {event.center.lat:.6f}, {event.center.lon:.6f}, "
            f"Zoom: {event.zoom}"
        )

    map_widget.on_mouse_moved(update_location)
    map_widget.on_viewport_change(update_viewport)

    # Explicitly set the close protocol to root.destroy to ensure clean exit
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()
