import tkinter as tk
import asynctkinter2 as atk


def main():
    root = tk.Tk()
    root_task = atk.start(async_main(root))
    root.protocol("WM_DELETE_WINDOW", lambda: (root_task.cancel(), root.destroy()))
    root.mainloop()


async def async_main(root: tk.Tk):
    root.title("Filtering Event")
    root.geometry("900x400")
    label = tk.Label(root, font=(None, 40))
    label.pack(expand=True, fill="both")
    while True:
        label["text"] = "Press the left mouse button"
        await atk.event(label, "<ButtonPress-1>")
        label["text"] = "One more time"
        await atk.event(label, "<ButtonPress>", filter=lambda e: e.num == 1)
        label["text"] = "Nice!"

        await atk.sleep(root, 1500)

        label["text"] = "Press the right mouse button"
        await atk.event(label, "<ButtonPress-3>")
        label["text"] = "One more time"
        await atk.event(label, "<ButtonPress>", filter=lambda e: e.num == 3)
        label["text"] = "Great!"

        await atk.sleep(root, 1500)


if __name__ == "__main__":
    main()
