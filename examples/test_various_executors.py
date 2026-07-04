from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import tkinter as tk
import asynctkinter2 as atk


available_executors = [ThreadPoolExecutor, ProcessPoolExecutor]
try:
    from concurrent.futures import InterpreterPoolExecutor
except ImportError:
    pass
else:
    available_executors.append(InterpreterPoolExecutor)


def main():
    root = tk.Tk()
    root_task = atk.start(async_main(root))
    root.protocol("WM_DELETE_WINDOW", lambda: (root_task.cancel(), root.destroy()))
    root.mainloop()


def sleep_2_seconds_then_return_ROTK9():
    import time
    time.sleep(2)
    return "ROTK9"


def sleep_2_seconds_then_raise_exception():
    import time
    time.sleep(2)
    return 1 / 0


async def async_main(root: tk.Tk):
    root.title("HTTP Request")
    root.geometry("1000x400")
    label = tk.Label(root, font=(None, 40))
    label.pack(expand=True)

    for exe_cls in available_executors:
        with exe_cls() as executor:
            label["text"] = f"Testing {exe_cls.__name__}..."
            result = await atk.run_in_executor(
                executor,
                root.after,
                sleep_2_seconds_then_return_ROTK9,
                polling_interval_ms=200,
            )
            assert result == "ROTK9"

            label["text"] = f"Testing {exe_cls.__name__}...\n(exception)"
            try:
                await atk.run_in_executor(
                    executor,
                    root.after,
                    sleep_2_seconds_then_raise_exception,
                    polling_interval_ms=200,
                )
            except ZeroDivisionError:
                pass
            else:
                assert False, "Failed to catch exception"

    label["text"] = "done!"


if __name__ == "__main__":
    main()
