import asyncio
import json
import signal
import websockets
import aioconsole


async def receive_messages(websocket, stop):
    """サーバーからのメッセージを受信して表示"""
    try:
        while not stop.done():
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(message)
                if data["type"] == "message":
                    print(
                        f"\n[{data['timestamp']}] {data['sender']}: {data['content']}"
                    )
                elif data["type"] == "error":
                    print(f"\n[{data['timestamp']}] エラー: {data['content']}")
                    if not stop.done():
                        stop.set_result(None)
            except asyncio.TimeoutError:
                continue
    except websockets.exceptions.ConnectionClosed:
        print("\nサーバーとの接続が切断されました")
        if not stop.done():
            stop.set_result(None)


async def send_messages(websocket, stop):
    """ユーザー入力を受け付けてサーバーに送信"""
    try:
        while not stop.done():
            try:
                message = await aioconsole.ainput(
                    "メッセージを入力 (終了するには 'quit' と入力): "
                )
                if message.lower() == "quit":
                    stop.set_result(None)
                    break
                if not stop.done():
                    await websocket.send(message)
            except asyncio.CancelledError:
                break
    except websockets.exceptions.ConnectionClosed:
        if not stop.done():
            stop.set_result(None)


async def main():
    """WebSocketクライアントを起動"""
    try:
        # 終了制御用のFuture
        stop = asyncio.Future()

        # シグナルハンドラを設定
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig, lambda: stop.set_result(None) if not stop.done() else None
            )

        async with websockets.connect("ws://localhost:8765") as websocket:
            print("チャットに接続しました")

            # メッセージの送受信タスクを作成
            tasks = asyncio.gather(
                receive_messages(websocket, stop), send_messages(websocket, stop)
            )

            # いずれかのタスクが終了するまで待機
            try:
                await stop
                print("\nシャットダウンを開始します...")
                tasks.cancel()
                try:
                    await tasks
                except asyncio.CancelledError:
                    pass
            finally:
                print("チャットを終了します")

    except ConnectionRefusedError:
        print("サーバーに接続できません。サーバーが起動しているか確認してください。")


if __name__ == "__main__":
    asyncio.run(main())
