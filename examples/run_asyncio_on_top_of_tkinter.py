'''
tkinterのメインループ上でasyncioを動かす例。
'''

from contextlib import ExitStack
from functools import partial
import asyncio
import tkinter as tk
import asynctkinter2 as atk


def main():
    root = tk.Tk()
    root.title("Run asyncio on top of tkinter")
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
        # NOTE: I'm not familiar with asyncio, this part might be incorrect.
        loop = asyncio.new_event_loop()
        loop.set_debug(True)
        asyncio.set_event_loop(loop)  # Not sure if this is necessary.
        defer(loop.close)
        defer(loop.stop)
        def process_asyncio(stop=loop.stop, run_forever=loop.run_forever, after=root.after, interval_ms=100):
            # https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_forever
            stop()
            run_forever()
            after(interval_ms, process_asyncio)
        root.after(100, process_asyncio)
        task = loop.create_task(asyncio_anim(root))
        defer(task.cancel)

        root.protocol("WM_DELETE_WINDOW", stack.close)
        root.mainloop()


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
    main()
