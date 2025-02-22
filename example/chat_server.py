import asyncio
import json
import signal
from datetime import datetime
import websockets

# 接続中のクライアントを保持するセット
CONNECTIONS = set()

async def broadcast(message: str, sender_id: str):
    """全クライアントにメッセージをブロードキャストする"""
    if CONNECTIONS:
        # メッセージの形式を整える
        message_data = {
            "type": "message",
            "sender": sender_id,
            "content": message,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        # 接続中の全クライアントにメッセージを送信
        websockets.broadcast(CONNECTIONS, json.dumps(message_data))

async def handle_connection(websocket):
    """クライアント接続を処理する"""
    # クライアントIDを生成（接続アドレスを使用）
    client_id = f"User-{hash(websocket)}"
    
    try:
        # 新しい接続を登録
        CONNECTIONS.add(websocket)
        
        # 接続通知をブロードキャスト
        await broadcast(f"{client_id} が入室しました", "System")
        
        # クライアントからのメッセージを処理
        async for message in websocket:
            await broadcast(message, client_id)
            
    except websockets.exceptions.ConnectionClosed:
        print(f"Client {client_id} disconnected")
    finally:
        # 接続が切れた場合、セットから削除
        CONNECTIONS.remove(websocket)
        await broadcast(f"{client_id} が退室しました", "System")

async def shutdown(server):
    """サーバーを安全にシャットダウンする"""
    print("\nシャットダウンを開始します...")
    
    # 新規接続を停止
    server.close()
    await server.wait_closed()
    
    # クライアントに通知
    if CONNECTIONS:
        await broadcast("サーバーをシャットダウンします", "System")
        
    # 既存の接続をクローズ
    for ws in CONNECTIONS.copy():
        await ws.close()
    
    print("サーバーを終了します")

async def main():
    """WebSocketサーバーを起動"""
    stop = asyncio.Future()
    
    # シグナルハンドラを設定
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: stop.set_result(None))
    
    async with websockets.serve(handle_connection, "localhost", 8765) as server:
        print("Chat server started on ws://localhost:8765")
        print("終了するには Ctrl+C を押してください")
        
        try:
            await stop
        finally:
            await shutdown(server)

if __name__ == "__main__":
    asyncio.run(main()) 