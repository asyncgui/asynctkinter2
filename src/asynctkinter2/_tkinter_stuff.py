__all__ = (
    'event', 'event_freq', 'sleep', 'run_in_thread', 'run_in_executor',
)
from functools import partial
from typing import Protocol
from collections.abc import Awaitable, Iterator, Callable
from contextlib import contextmanager

from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import tkinter

from asyncgui import ExclusiveEvent, Cancelled


# ----------------------------------------------------------------------------
# Tk Event 
# ----------------------------------------------------------------------------

def _event_callback(ee: ExclusiveEvent, filter, e: tkinter.Event):
    if filter is None or filter(e):
        ee.fire(e)


async def event(widget, event_name, *, filter=None) -> Awaitable[tkinter.Event]:
    '''
    .. code-block::

        e = await event(widget, '<ButtonPress>')
        print(f"{e.x = }, {e.y = }")
    '''
    ee = ExclusiveEvent()
    bind_id = widget.bind(event_name, partial(_event_callback, ee, filter), "+")
    try:
        return await ee.wait_args_0()
    finally:
        widget.unbind(event_name, bind_id)


@contextmanager
def event_freq(widget, event_name, *, filter=None) -> Iterator[Callable[[], Awaitable[tkinter.Event]]]:
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
    '''
    ee = ExclusiveEvent()
    bind_id = widget.bind(event_name, partial(_event_callback, ee, filter), "+")
    try:
        yield ee.wait_args_0
    finally:
        widget.unbind(event_name, bind_id)


# ----------------------------------------------------------------------------
# Tk Timer
# ----------------------------------------------------------------------------

class AfterScheduler(Protocol):
    def after(self, delay_ms: int, func: Callable, *args): ...


def sleep(scheduler: AfterScheduler, duration_ms) -> Awaitable:
    '''
    .. code-block::

        await sleep(widget, 1000)  # Sleeps for 1000 milliseconds
    '''
    ee = ExclusiveEvent()
    scheduler.after(duration_ms, ee.fire)
    return ee.wait()


# ----------------------------------------------------------------------------
# Thread
# ----------------------------------------------------------------------------


async def run_in_thread(scheduler: AfterScheduler, func, *, daemon=None, polling_interval_ms=1000):
    '''
    Creates a new thread, runs the given function within it, then waits for the completion of the function.

    .. code-block::

        return_value = await run_in_thread(widget, func)

    .. warning::
        When the caller Task is cancelled, the ``func`` will be left running, which violates "structured concurrency".
    '''
    return_value = None
    exc = None
    done = False

    def wrapper():
        nonlocal return_value, done, exc
        try:
            return_value = func()
        except Exception as e:
            exc = e
        finally:
            done = True

    Thread(target=wrapper, daemon=daemon, name="asynctkinter2.run_in_thread").start()
    _sleep = sleep
    while not done:
        await _sleep(scheduler, polling_interval_ms)
    if exc is not None:
        raise exc
    return return_value


async def run_in_executor(executer: ThreadPoolExecutor, scheduler: AfterScheduler, func, *, polling_interval_ms=1000):
    '''
    Runs the given function within the given :class:`concurrent.futures.ThreadPoolExecutor`,
    then waits for the completion of the function.

    .. code-block::

        executor = ThreadPoolExecutor()
        ...
        return_value = await run_in_executor(executor, widget, func)

    .. warning::
        When the caller Task is cancelled, the ``func`` will be left running if it has already started,
        which violates "structured concurrency".
    '''
    return_value = None
    exc = None
    done = False

    def wrapper():
        nonlocal return_value, done, exc
        try:
            return_value = func()
        except Exception as e:
            exc = e
        finally:
            done = True

    future = executer.submit(wrapper)
    try:
        _sleep = sleep
        while not done:
            await _sleep(scheduler, polling_interval_ms)
    except Cancelled:
        future.cancel()
        raise
    if exc is not None:
        raise exc
    return return_value


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
