from functools import partial
import tkinter as tk
import asynctkinter2 as atk


def main():
    root = tk.Tk()
    root_task = atk.start(async_main(root))
    root.protocol("WM_DELETE_WINDOW", lambda: (root_task.cancel(), root.destroy()))
    root.mainloop()


async def async_main(root: tk.Tk):
    sleep = partial(atk.sleep, root)
    root.title("Animation")
    root.geometry("800x200")
    label = tk.Label(root, text="Hello", font=(None, 80))
    label.pack(expand=True, fill="both")
    await sleep(2000)
    while True:
        label["text"] = "Do"
        await sleep(500)
        label["text"] = "You"
        await sleep(500)
        label["text"] = "Like"
        await sleep(500)
        label["text"] = "Tkinter?"
        await sleep(2000)
        label["text"] = "Answer me!"
        await sleep(2000)


if __name__ == "__main__":
    main()
