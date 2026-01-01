'''
* Same as painter1.py except this one can handle multiple mouse buttons simultaneously.
'''
import tkinter as tk
import asynctkinter2 as atk

from painter1 import draw_oval, draw_rect


def main():
    root = tk.Tk()
    root_task = atk.start(async_main(root))
    root.protocol("WM_DELETE_WINDOW", lambda: (root_task.cancel(), root.destroy()))
    root.mainloop()


async def async_main(root: tk.Tk):
    root.title("Painter")
    root.geometry("800x800")
    canvas = tk.Canvas(root, bg="white")
    canvas.pack(expand=True, fill="both")

    button2command = {
        1: draw_rect,
        3: draw_oval,
    }
    async with atk.open_nursery() as nursery:
        while True:
            e_press = await atk.event(canvas, "<ButtonPress>")
            command = button2command.get(e_press.num)
            if command is not None:
                nursery.start(command(canvas, e_press))


if __name__ == "__main__":
    main()
