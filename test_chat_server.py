import pytest
import pytest_asyncio
import asyncio
import websockets
import json
from chat_server import broadcast, CONNECTIONS, handle_connection


@pytest_asyncio.fixture(scope="function")
async def websocket_server():
    """WebSocketサーバーのフィクスチャ"""
    CONNECTIONS.clear()  # テスト前にコネクションをクリア
    server = await websockets.serve(handle_connection, "localhost", 8765)
    await asyncio.sleep(0.1)  # サーバーの起動を待つ
    yield server
    server.close()
    await server.wait_closed()


@pytest.mark.asyncio(loop_scope="function")
async def test_broadcast(websocket_server):
    """ブロードキャスト機能のテスト"""
    # テスト用のWebSocket接続を作成
    ws = await websockets.connect("ws://localhost:8765")

    # 入室メッセージをスキップ
    await ws.recv()

    # テストメッセージを送信
    test_message = "Hello, World!"
    test_sender = "TestUser"
    await broadcast(test_message, test_sender)

    # ブロードキャストされたメッセージを受信
    received = await ws.recv()
    message_data = json.loads(received)

    # メッセージの内容を検証
    assert message_data["type"] == "message"
    assert message_data["sender"] == test_sender
    assert message_data["content"] == test_message

    # クリーンアップ
    await ws.close()


@pytest.mark.asyncio(loop_scope="function")
async def test_client_connection(websocket_server):
    """クライアント接続のテスト"""
    # クライアント接続を確立
    ws = await websockets.connect("ws://localhost:8765")

    # 入室メッセージを受信して接続が確立されていることを確認
    received = await ws.recv()
    message_data = json.loads(received)
    assert message_data["type"] == "message"
    assert "入室しました" in message_data["content"]

    # クリーンアップ
    await ws.close()


@pytest.mark.asyncio(loop_scope="function")
async def test_multiple_clients(websocket_server):
    """複数クライアントの同時接続テスト"""
    # 複数のクライアントを接続
    clients = []
    for _ in range(3):
        client = await websockets.connect("ws://localhost:8765")
        # 入室メッセージを受信
        received = await client.recv()
        message_data = json.loads(received)
        assert message_data["type"] == "message"
        assert "入室しました" in message_data["content"]
        clients.append(client)

    # クリーンアップ
    for client in clients:
        await client.close()
