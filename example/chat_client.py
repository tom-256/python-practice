import asyncio
import json
import sys
import websockets
import aioconsole

async def receive_messages(websocket, running):
    """サーバーからのメッセージを受信して表示"""
    try:
        while running.is_set():
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                data = json.loads(message)
                if data["type"] == "message":
                    print(f"\n[{data['timestamp']}] {data['sender']}: {data['content']}")
                    print("メッセージを入力 (終了するには 'quit' と入力): ", end="", flush=True)
            except asyncio.TimeoutError:
                continue
    except websockets.exceptions.ConnectionClosed:
        print("\nサーバーとの接続が切断されました")
        running.clear()

async def send_messages(websocket, running):
    """ユーザー入力を受け付けてサーバーに送信"""
    try:
        while running.is_set():
            message = await aioconsole.ainput("メッセージを入力 (終了するには 'quit' と入力): ")
            if message.lower() == "quit":
                running.clear()
                break
            if running.is_set():
                await websocket.send(message)
    except websockets.exceptions.ConnectionClosed:
        running.clear()

async def main():
    """WebSocketクライアントを起動"""
    try:
        async with websockets.connect("ws://localhost:8765") as websocket:
            print("チャットに接続しました")
            
            # 実行状態を管理するフラグ
            running = asyncio.Event()
            running.set()
            
            # メッセージの送受信を並行して実行
            await asyncio.gather(
                receive_messages(websocket, running),
                send_messages(websocket, running)
            )
            
            print("チャットを終了します")
            sys.exit(0)
            
    except ConnectionRefusedError:
        print("サーバーに接続できません。サーバーが起動しているか確認してください。")
    except KeyboardInterrupt:
        print("\nクライアントを終了します")

if __name__ == "__main__":
    asyncio.run(main()) 