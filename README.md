# AsyncTkinter2

`asynctkinter2` は`tkinter`用のライブラリで、 よくあるasyncライブラリと同じでコールバック関数だらけの醜いコードを読みやすくしてくれます。 例えば

- Aを出力
- 一秒待機
- Bを出力
- labelが押されるまで待機
- Cを出力

といった事を普通にやろうとするとコードは

```python
def やりたき事(label):
    bind_id = None
    print('A')

    def 一秒後に(__):
        nonlocal bind_id
        print('B')
        bind_id = label.bind("<ButtonPress>", labelが押された時に, "+")
    label.after(1000, 一秒後に)

    def labelが押された時に(event):
        label.unbind("<ButtonPress>", bind_id)
        print('C')

やりたき事(...)
```

のように読みにくい物となりますが`asynctkinter2`を用いることで

```python
import asynctkinter2 as atk

async def やりたき事(label):
    print('A')
    await atk.sleep(label, 1000)
    print('B')
    await atk.event(label, "<ButtonPress>")
    print('C')

atk.start(やりたき事(...))
```

と分かりやすく書けます。

## Installation

Pin the minor version.

```text
pip install "asynctkinter2>=0.1,<0.2"
```

## 使用例

```python
import tkinter as tk
import asynctkinter2 as atk


def main():
    root = tk.Tk()
    root_task = atk.start(async_main(root))
    root.protocol("WM_DELETE_WINDOW", lambda: (root_task.cancel(), root.destroy()))
    root.mainloop()


async def async_main(root: tk.Tk):
    label = tk.Label(root, text='Hello', font=('', 80))
    label.pack()

    # 二秒待つ
    await atk.sleep(root, 2000)

    # labelが押されるのを待つ
    event = await atk.event(label, "<ButtonPress>")
    print(f"pos: {event.x}, {event.y}")

    # labelが押される か 5秒経つまで待つ。
    tasks = await atk.wait_any(
        atk.sleep(root, 5000),
        atk.event(label, "<ButtonPress>"),
    )
    if tasks[0].finished:
        print("5秒経った")
    else:
        event = tasks[1].result
        print(f"labelが押された (pos: {event.x}, {event.y})")

    # labelが押され なおかつ 5秒経つまで待つ
    tasks = await atk.wait_all(
        atk.sleep(root, 5000),
        atk.event(label, "<ButtonPress>"),
    )

    # GUIを固まらせずにHTTPリクエストを実行し、その完了を待つ
    import requests
    res: requests.Response = await atk.run_in_thread(root, lambda: requests.get("https://httpbin.org/delay/2"))
    label["text"] = f"{res.status_code = }"


if __name__ == "__main__":
    main()
```

## `asynctkinter` との違い

現在の[asynctkinter](https://github.com/asyncgui/asynctkinter)は

- メインループは `tkinter` が元々持っている `mainloop()` ではなく独自の物を用い
- タイマー機能に関しても `tkinter` が元々持っている `after()` ではなく独自の物を用いています。

対して `asynctkinter2` では独自の物を用いないようにしています。
そのおかげで `asyncio` や `trio` といった他のasyncライブラリと共存しやくなっています。
ただ代償としてフレームレート非依存のアニメーションを書く際の手間が増えます。
具体的には自身で `time.perf_counter()` 等を用いて経過時間を計測しないといけません。

## `asyncio` との共存

共存といっても何でもできるわけではなく、１つのasync関数内に `asyncio` に対するasync処理と`asynctkinter2` に対するasync処理を混在させることはできません。

```python
async def this_does_not_work():
    await asyncio.sleep(1)
    await asynctkinter2.sleep(widget, 1000)
``` 

ここで言う "async処理" というのは予約語の `async` や `await` を含む処理だけを指します。
なので以下のコードでは `asyncio` に対する処理と `asynctkinter2` に対する処理が混在しているものの、`asynctkinter2` 側は予約語 `async/await` を含んでいないため問題ありません。

```python
async def this_works():
    await asyncio.sleep(1)
    task = asynctkinter2.start(...)

asyncio.create_task(this_works())
```

以下の例も `asyncio` 側がasync処理ではないので問題ありません。

```python
async def this_also_works():
    task = asyncio.create_task(...)
    await asynctkinter2.sleep(widget, 1000)

asynctkinter2.start(this_also_works())
```
