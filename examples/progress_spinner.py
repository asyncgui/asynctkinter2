from itertools import accumulate, cycle
from functools import partial
import tkinter as tk
import asynctkinter2 as atk


def main():
    root = tk.Tk()
    root_task = atk.start(async_main(root))
    root.protocol("WM_DELETE_WINDOW", lambda: (root_task.cancel(), root.destroy()))
    root.mainloop()


async def async_main(root: tk.Tk):
    root.title("Progress Spinner")
    root.geometry("600x600")
    canvas = tk.Canvas(root, bg="white")
    canvas.pack(expand=True, fill="both")

    await run_progress_spinner(
        draw_target=canvas,
        line_width=(lw := 30),
        bbox=(lw, lw, 600 - lw, 600 - lw),
        fps=40,
    )


async def run_progress_spinner(
        draw_target: tk.Canvas, *, bbox=(0, 0, 100, 100), line_color="black", line_width=10,
        min_arc_angle=30, speed=1.0, fps=30):
    '''
    円周上を弧が伸び縮みしながら周るアニメーション。
    
    :param draw_target: 描画先
    :param bbox: 描画範囲 (left, top, right, bottom)
    :param min_arc_angle: 弧が縮み切った時の角度。度数法。伸び切った時の角度は ``360 - この値`` になる。
    :param speed: アニメーションの速度。大きいほど速くなる。
    '''
    # NOTE: 実装詳細
    #
    # アニメーションは以下の４つの段階に分かれ、それらを繰り返す。
    # 1. 弧が縮み切った状態で周る。
    # 2. 弧が伸びながら周る。
    # 3. 弧が伸び切った状態で周る。
    # 4. 弧が縮みながら周る。
    # cycle()に渡しているタプルの長さが４になっているのはこのため。

    MA = min_arc_angle
    BS = 60  # base speed
    get_next_start = accumulate(cycle((BS, BS, BS + 360 - MA - MA,  BS, )), initial=90).__next__
    get_next_extent = cycle((MA, 360 - MA, 360 - MA, MA, )).__next__
    del MA, BS
    start = get_next_start()
    extent = get_next_extent()

    arc = draw_target.create_arc(
        *bbox, outline=line_color, width=line_width, start=start, extent=extent, style="arc",
    )
    try:
        duration_per_phase = int(500. / speed)
        delta_time = int(1000 / fps)
        sleep = partial(atk.sleep, draw_target, delta_time)
        while True:
            next_start = get_next_start()
            next_extent = get_next_extent()
            slope_start = next_start - start
            slope_extent = next_extent - extent

            elapsed_time = 0
            while elapsed_time < duration_per_phase:
                t = elapsed_time / duration_per_phase
                draw_target.itemconfig(arc, start=slope_start * t + start, extent=slope_extent * t + extent)
                await sleep()
                elapsed_time += delta_time
            
            start = next_start
            extent = next_extent
    finally:
        draw_target.delete(arc)


if __name__ == "__main__":
    main()
