import tkinter as tk
import asynctkinter2 as atk


def main():
    root = tk.Tk()
    root_task = atk.start(async_main(root))
    root.protocol("WM_DELETE_WINDOW", lambda: (root_task.cancel(), root.destroy()))
    root.mainloop()


async def async_main(root: tk.Tk):
    root.title("Event Handling")
    root.geometry("800x400")
    label = tk.Label(root, font=(None, 40))
    label.pack(expand=True, fill="both")
    while True:
        label["text"] = "Click anywhere!"
        e = await atk.event(label, "<ButtonPress>")
        label["text"] = f"You clicked at pos ({e.x}, {e.y})"
        await atk.sleep(root, 1500)


if __name__ == "__main__":
    main()
