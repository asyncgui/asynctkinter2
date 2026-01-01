import tkinter as tk
import requests
import asynctkinter2 as atk


def main():
    root = tk.Tk()
    root_task = atk.start(async_main(root))
    root.protocol("WM_DELETE_WINDOW", lambda: (root_task.cancel(), root.destroy()))
    root.mainloop()


async def async_main(root: tk.Tk):
    root.title("HTTP Request")
    root.geometry("1000x400")
    label = tk.Label(root, text="Press to start a HTTP request", font=(None, 40))
    label.pack(expand=True)
    await atk.event(root, "<ButtonPress>")
    label["text"] = "waiting for the server to respond..."
    res = await atk.run_in_thread(
        root,
        lambda: requests.get("https://httpbin.org/delay/2"),
        daemon=True,
        polling_interval_ms=200,
    )
    label["text"] = res.json()["headers"]["User-Agent"]


if __name__ == "__main__":
    main()
