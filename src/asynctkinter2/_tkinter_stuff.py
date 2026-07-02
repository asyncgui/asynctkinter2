__all__ = (
    'event', 'event_freq', 'sleep', 'run_in_thread', 'run_in_executor',
)
from functools import partial
from collections.abc import Awaitable, Callable

from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import tkinter

from asyncgui import ExclusiveEvent, StatefulEvent, Cancelled


# ----------------------------------------------------------------------------
# Tk Event 
# ----------------------------------------------------------------------------

def _event_callback(callback, filter, e: tkinter.Event):
    if filter is None or filter(e):
        callback(e)


async def event(widget, event_name, *, filter=None) -> Awaitable[tkinter.Event]:
    '''
    .. code-block::

        e = await event(widget, '<ButtonPress>')
        print(f"{e.x = }, {e.y = }")
    '''
    ee = ExclusiveEvent()
    bind_id = widget.bind(event_name, partial(_event_callback, ee.fire, filter), "+")
    try:
        return await ee.wait_args_0()
    finally:
        widget.unbind(event_name, bind_id)


class event_freq:
    '''
    When handling a frequently occurring event, such as ``<Motion>``, the following kind of code
    may cause performance issues:

    .. code-block::

        while True:
            e = await event(widget, '<Motion>')
            ...

    If that happens, try the following code instead. It may resolve the issue:

    .. code-block::

        with event_freq(widget, '<Motion>') as mouse_motion:
            while True:
                e = await mouse_motion()
                ...

    When listening for a ``<Motion>`` event, you will often also want to listen for a ``<ButtonRelease>`` event,
    which leads to deeply nested code:

    .. code-block::

        async with move_on_when(event(widget, "<ButtonRelease>", filter=...)):
            with event_freq(widget, "<Motion>") as mouse_motion:
                while True:
                    e = await mouse_motion()
                    ...

    To mitigate this, ``event_freq`` can also be used as an async context manager, making the above code less nested:

    .. code-block::

        async with (
            move_on_when(event(widget, "<ButtonRelease>", filter=...)),
            event_freq(widget, "<Motion>") as mouse_motion,
        ):
            while True:
                e = await mouse_motion()
                ...
    '''
    def __init__(self, widget, event_name, *, filter=None):
        self.widget = widget
        self.event_name = event_name
        self.filter = filter

    def __enter__(self):
        ee = ExclusiveEvent()
        self.bind_id = self.widget.bind(self.event_name, partial(_event_callback, ee.fire, self.filter), "+")
        return ee.wait_args_0

    def __exit__(self, *args):
        self.widget.unbind(self.event_name, self.bind_id)

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, *args):
        return self.__exit__(*args)


# ----------------------------------------------------------------------------
# Tk Timer
# ----------------------------------------------------------------------------

def sleep(after: Callable, duration_ms) -> Awaitable:
    '''
    .. code-block::

        await sleep(widget.after, 1000)  # Sleeps for 1000 milliseconds

    .. versionchanged:: 0.2.0
        The API now requires an ``after`` method instead of a widget.
    '''
    ee = ExclusiveEvent()
    after(duration_ms, ee.fire)
    return ee.wait()


# ----------------------------------------------------------------------------
# Thread
# ----------------------------------------------------------------------------


async def run_in_thread(after: Callable, func, *, daemon=None):
    '''
    Creates a new thread, runs the given function within it, then waits for the completion of the function.

    .. code-block::

        return_value = await run_in_thread(widget.after, func)

    .. warning::
        When the caller Task is cancelled, the ``func`` will be left running, which violates "structured concurrency".

    .. versionchanged:: 0.2.0
        The API now requires an ``after`` method instead of a widget.
    '''

    result_event = StatefulEvent()

    def wrapper():
        return_value = None
        exc = None
        try:
            return_value = func()
        except Exception as e:
            exc = e
        finally:
            after(0, result_event.fire, return_value, exc)

    Thread(target=wrapper, daemon=daemon, name="asynctkinter2.run_in_thread").start()
    return_value, exc = await result_event.wait()
    if exc is not None:
        raise exc
    return return_value


async def run_in_executor(executor: ThreadPoolExecutor, after: Callable, func):
    '''
    Runs the given function within the given :class:`concurrent.futures.ThreadPoolExecutor`,
    then waits for the completion of the function.

    .. code-block::

        executor = ThreadPoolExecutor()
        ...
        return_value = await run_in_executor(executor, widget.after, func)

    .. warning::
        When the caller Task is cancelled, the ``func`` will be left running if it has already started,
        which violates "structured concurrency".

    .. versionchanged:: 0.2.0
        The API now requires an ``after`` method instead of a widget.
    '''
    result_event = StatefulEvent()

    def wrapper():
        return_value = None
        exc = None
        try:
            return_value = func()
        except Exception as e:
            exc = e
        finally:
            after(0, result_event.fire, return_value, exc)

    future = executor.submit(wrapper)
    try:
        return_value, exc = await result_event.wait()
    except Cancelled:
        future.cancel()
        raise
    if exc is not None:
        raise exc
    return return_value
    # This code is in line with the thread code above.
    # An alternative would be to use future.add_done_callback():
    #
    # future = executor.submit(func) # deals with both cases return value and exception
    # future.add_done_callback(partial(after, 0, event.fire))
    # fut = await event.wait_args_0()  # parameter of event.fire above
    # assert fut is future
    # return fut.result()
    # In this case, the wrapper can be omitted.


# ----------------------------------------------------------------------------
# Misc
# ----------------------------------------------------------------------------

def _patch_unbind():
    '''
    The reason we need to patch 'Misc.unbind()'.
    https://stackoverflow.com/questions/6433369/deleting-and-changing-a-tkinter-event-binding
    '''
    def _new_unbind(self, sequence, funcid=None):
        if not funcid:
            self.tk.call("bind", self._w, sequence, "")
            return
        func_callbacks = self.tk.call("bind", self._w, sequence, None).split("\n")
        new_callbacks = [l for l in func_callbacks if l[6:6 + len(funcid)] != funcid]
        self.tk.call("bind", self._w, sequence, "\n".join(new_callbacks))
        self.deletecommand(funcid)

    tkinter.Misc.unbind = _new_unbind
_patch_unbind()
