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


@pytest.mark.asyncio(loop_scope="function")
async def test_max_connections(websocket_server):
    """最大接続数のテスト"""
    # 最大接続数まで接続を作成
    clients = []
    for _ in range(10):
        client = await websockets.connect("ws://localhost:8765")
        # 入室メッセージを受信
        received = await client.recv()
        message_data = json.loads(received)
        assert message_data["type"] == "message"
        assert "入室しました" in message_data["content"]
        clients.append(client)

    # 11人目の接続を試みる
    excess_client = await websockets.connect("ws://localhost:8765")
    # エラーメッセージを受信
    received = await excess_client.recv()
    message_data = json.loads(received)
    assert message_data["type"] == "error"
    assert "満室です" in message_data["content"]

    # 接続が自動的に閉じられることを確認
    try:
        await excess_client.recv()
        assert False, "Connection should be closed"
    except websockets.exceptions.ConnectionClosed:
        pass

    # クリーンアップ
    await excess_client.close()
    for client in clients:
        await client.close()
