'''
asyncgui 0.11.1 or later is required to run this example.
'''

import tkinter as tk
import requests
import asynctkinter2 as atk
from progress_spinner import run_progress_spinner


def main():
    root = tk.Tk()
    root_task = atk.start(async_main(root))
    root.protocol("WM_DELETE_WINDOW", lambda: (root_task.cancel(), root.destroy()))
    root.mainloop()


async def async_main(root: tk.Tk):
    root.title("HTTP request + loading animation")
    root.geometry("720x480")

    label = tk.Label(root, text="HTTP requests", font=(None, 30))
    label.pack(pady=20, side="top")
    button = tk.Button(root, text="start", font=(None, 30))
    button.pack(pady=20, side="bottom")
    canvas = tk.Canvas(root, bg=root.cget("bg"), height=200, width=200)
    canvas.pack(expand=True)

    await atk.event(button, "<ButtonPress>")
    button["text"] = "cancel"

    async with atk.open_nursery() as nursery:
        cancel_tracker = nursery.start(atk.event(button, "<ButtonPress>"), daemon=True, close_on_finish=True)
        nursery.start(run_progress_spinner(
            canvas,
            line_width=(lw := 20),
            bbox=(lw, lw, canvas.winfo_width() - lw, canvas.winfo_height() - lw),
        ), daemon=True)
        with requests.Session() as session:
            label["text"] = "first request..."
            await atk.run_in_thread(
                root.after,
                lambda: session.get("https://httpbin.org/delay/2"),
                daemon=True,
                polling_interval_ms=400,
            )
            label["text"] = "second request..."
            await atk.run_in_thread(
                root.after,
                lambda: session.get("https://httpbin.org/delay/2"),
                daemon=True,
                polling_interval_ms=400,
            )

    label["text"] = "cancelled" if cancel_tracker.finished else "completed"
    button["text"] = "close"
    await atk.event(button, "<ButtonPress>")
    root.destroy()


if __name__ == "__main__":
    main()
