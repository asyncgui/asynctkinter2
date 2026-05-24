# AsyncTkinter2

[日本語版](https://github.com/asyncgui/asynctkinter2/blob/main/README_ja.md)

`asynctkinter2` is an async library that saves you from ugly callback-style code,
like most of async libraries do.
Let's say you want to do:

1. `print("A")`
1. wait for 1sec
1. `print("B")`
1. wait for a label to be pressed
1. `print("C")`

in that order.
Your code would look like this:

```python
def what_you_want_to_do(label):
    bind_id = None
    print("A")

    def one_sec_lator(__):
        nonlocal bind_id
        print("B")
        bind_id = label.bind("<ButtonPress>", on_press, "+")
    label.after(1000, one_sec_lator)

    def on_press(event):
        label.unbind("<ButtonPress>", bind_id)
        print("C")

what_you_want_to_do(...)
```

This is hard to follow. With `asynctkinter2`, the same logic becomes:

```python
import asynctkinter2 as atk

async def what_you_want_to_do(label):
    print("A")
    await atk.sleep(label.after, 1000)
    print("B")
    await atk.event(label, "<ButtonPress>")
    print("C")

atk.start(what_you_want_to_do(...))
```

## Installation

Pin the minor version.

```text
pip install "asynctkinter2>=0.1,<0.2"
```

## Example

```python
from functools import partial
import tkinter as tk
import asynctkinter2 as atk


def main():
    root = tk.Tk()
    root_task = atk.start(async_main(root))
    root.protocol("WM_DELETE_WINDOW", lambda: (root_task.cancel(), root.destroy()))
    root.mainloop()


async def async_main(root: tk.Tk):
    sleep = partial(atk.sleep, root.after)
    label = tk.Label(root, text='Hello', font=('', 80))
    label.pack()

    # Waits for 2 seconds to elapse.
    await sleep(2000)

    # Waits for a label to be pressed.
    event = await atk.event(label, "<ButtonPress>")
    print(f"pos: {event.x}, {event.y}")

    # Waits for either 5 seconds to elapse or a label to be pressed.
    # i.e. Waits at most 5 seconds for a label to be pressed.
    tasks = await atk.wait_any(
        sleep(5000),
        atk.event(label, "<ButtonPress>"),
    )
    if tasks[0].finished:
        print("Timeout")
    else:
        event = tasks[1].result
        print(f"Label pressed (pos: {event.x}, {event.y})")

    # Waits for both 5 seconds to elapse and a label to be pressed.
    tasks = await atk.wait_all(
        sleep(5000),
        atk.event(label, "<ButtonPress>"),
    )

    # Performs an HTTP request without freezing the UI, then waits for completion.
    import requests
    res: requests.Response = await atk.run_in_thread(
        root.after, lambda: requests.get("https://httpbin.org/delay/2"))


if __name__ == "__main__":
    main()
```

## Differences from `asynctkinter`

[asynctkinter](https://github.com/asyncgui/asynctkinter):

- Uses its own main loop instead of `tkinter`'s built-in `mainloop()`
- Uses its own timer mechanism instead of `tkinter`'s built-in `after()`

`asynctkinter2`, on the other hand, relies entirely on `tkinter`'s built-in components.
This makes it much easier to coexist with other async libraries such as `asyncio` or `trio`.

## Coexisting with `asyncio`

Coexistence does come with one important limitation: you cannot mix `asyncio` async operations and `asynctkinter2` async operations inside the same async function:

```python
async def this_does_not_work():
    await asyncio.sleep(1)
    await asynctkinter2.sleep(widget.after, 1000)
```

"Async operation" here means only code that uses the Python keywords `async` or `await`.
The following is fine because, although it uses both `asyncio` and `asynctkinter2`,
the `asynctkinter2` side does not involve `async`/`await`:

```python
async def this_works():
    await asyncio.sleep(1)
    task = asynctkinter2.start(...)

asyncio.create_task(this_works())
```

The next example is also fine because the `asyncio` side does not involve `async`/`await`:

```python
async def this_also_works():
    task = asyncio.create_task(...)
    await asynctkinter2.sleep(widget.after, 1000)

asynctkinter2.start(this_also_works())
```
