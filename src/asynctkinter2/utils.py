from abc import ABC, abstractmethod
from concurrent.futures import Future
from functools import partial

from asyncgui import ExclusiveEvent


class _AwaitMixin(ABC):
    """This mixin makes providing an __await__() function easier.

    __await__() is not a coroutine, but just a generator.

    This way, it is easier to implement __await__() by just implementing a
    coroutine _await() and take its __await__() to get the result from."""

    def __await__(self):
        return (yield from self._await().__await__())

    @abstractmethod
    async def _await(self):
        pass


class _TkSchedule:
    """This mixin makes providing the scheduling to a widget's after() mechanism easier.
    With the parameters ms and idle, you control whether the given callback is given to the widget
    via after_idle() or after() and in the latter case which how much of a delay, measured in ms."""

    def __init__(self, widget, *, ms=0, idle=False):
        self.widget = widget
        self.ms = ms
        self.idle = idle

    def __call__(self, callback, *args, **kw):
        # Never call the callback directly, even not after a test for the right thread!
        # The callback might fire an ExclusiveEvent, which will be waited for after we return.
        # If it is fired before waited on, the fire will be lost as the event is not stateful.
        if self.idle or self.ms is None:
            self.widget.after_idle(callback, *args, **kw)
        else:
            self.widget.after(self.ms, callback, *args, **kw)


class AwaitConcurrentFuture(_AwaitMixin):
    """Provide an elegant way to await on a concurrent.futures.Future which are the lowest common denominator
    concerning communication between incompatible universes.

    For example, when running asyncgui/asynctkinter2 in the main loop for GUI purposes and a asyncio event loop in a
    separate thread for IO purposes, one might want to do asyncio calls like loop.run_coroutine_threadsafe() and
    await in the asyncgui world for its result.

    Instead of polling, it is more elegant to rely on the capability of concurrent.futures.Future to call a callback
    on completion.

    This callback happens in the origin thread and must be transferred over the thread boundary. In this case, this is
    done with the _TkSchedule object which arranges for routing this callback to an ExclusiveEvent which is triggered by
    the done callback. We await for this and return the future's result (which might as well consist of an Exception or
    a Cancellation).
    """

    def __init__(self, widget, future: Future, *, ms=0, idle=False):
        self.schedule = _TkSchedule(widget, ms=ms, idle=idle)
        self.future = future

    async def _await(self):
        event = ExclusiveEvent()
        # future will be passed to the partial callable, eventually ending as parameter to event.fire:
        self.future.add_done_callback(partial(self.schedule, event.fire))
        fut = await event.wait_args_0()  # parameter of event.fire above
        assert fut is self.future
        return fut.result()


class TkYield(_AwaitMixin):
    """This class makes it possible to "take a breath", to "make a gasp".

    From time to time, it might be favourable to give the GUI event loop give the opportunity to run other jobs.

    This works with any of

    await TkYield(ms=0) or just await TkYield() # return as soon as possible
    await TkYield(idle=True) # return as soon as the GUI loop hasn't anything urgent to do
    await TkYield(ms=200) # return in a certain time, effectively forming some kind of sleep() function.
    """

    def __init__(self, widget, *, ms=0, idle=False):
        self.schedule = _TkSchedule(widget, ms=ms, idle=idle)

    async def _await(self):
        event = ExclusiveEvent()  # safe enough if the _TkSchedule never calls the callback directly
        self.schedule(event.fire)
        return await event.wait()
