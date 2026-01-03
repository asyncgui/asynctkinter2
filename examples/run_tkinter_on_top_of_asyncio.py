'''
asyncioのメインループ上でtkinterを動かす例。
'''

from contextlib import ExitStack
from functools import partial
import asyncio
import tkinter as tk
import asynctkinter2 as atk


async def main(*, fps=30):
    root = tk.Tk()
    root.title("Run tkinter on top of asyncio")
    root.geometry("800x400")
    label = tk.Label(root, text="--", font=(None, 80), name="top_label")
    label.pack(expand=True, fill="both")
    label = tk.Label(root, text="--", font=(None, 80), name="bottom_label")
    label.pack(expand=True, fill="both")
    del label

    with ExitStack() as stack:
        defer = stack.callback
        defer(root.destroy)

        # asynctkinter2
        task = atk.start(asynctkinter_anim(root))
        defer(task.cancel)
        del task

        # asyncio
        root.protocol("WM_DELETE_WINDOW", asyncio.current_task().cancel)
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(asyncio_anim(root))
                sleep_duration = 1.0 / fps
                sleep = asyncio.sleep
                update = root.update
                while True:
                    update()
                    await sleep(sleep_duration)
        except asyncio.CancelledError:
            # It seems okay to suppress a CancelledError.
            # https://docs.python.org/3.10/library/asyncio-task.html#asyncio.Task.cancel
            pass


async def asyncio_anim(root: tk.Tk):
    sleep = asyncio.sleep
    label = root.children["bottom_label"]
    await sleep(2)
    while True:
        label["text"] = "This"
        await sleep(0.4)
        label["text"] = "label"
        await sleep(0.4)
        label["text"] = "is"
        await sleep(0.4)
        label["text"] = "animated"
        await sleep(0.4)
        label["text"] = "with"
        await sleep(0.4)
        label["text"] = "asyncio."
        await sleep(2)


async def asynctkinter_anim(root: tk.Tk):
    sleep = partial(atk.sleep, root)
    label = root.children["top_label"]
    await sleep(1000)
    while True:
        label["text"] = "This"
        await sleep(500)
        label["text"] = "label"
        await sleep(500)
        label["text"] = "is"
        await sleep(500)
        label["text"] = "animated"
        await sleep(500)
        label["text"] = "with"
        await sleep(500)
        label["text"] = "asynctkinter2."
        await sleep(2000)


if __name__ == "__main__":
    asyncio.run(main())
