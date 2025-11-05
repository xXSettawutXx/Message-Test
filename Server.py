import asyncio, websockets, os, json

PORT = int(os.getenv("PORT", 5000))  # Render จะ override ให้เอง

board = [["", "", ""], ["", "", ""], ["", "", ""]]
current_player = "X"
clients = set()

async def broadcast(data):
    msg = json.dumps(data)
    for client in clients:
        await client.send(msg)

async def handler(ws):
    global current_player, board
    clients.add(ws)

    await ws.send(json.dumps({"type":"state", "board":board, "turn":current_player}))

    try:
        async for message in ws:
            data = json.loads(message)

            if data["type"] == "move":
                x, y = data["x"], data["y"]
                player = data["player"]

                if board[x][y] == "" and player == current_player:
                    board[x][y] = player
                    current_player = "O" if current_player == "X" else "X"

                    await broadcast({"type":"state", "board":board, "turn":current_player})

    except:
        pass
    finally:
        clients.remove(ws)

async def main():
    print(f"Server running on port {PORT}")
    async with websockets.serve(handler, "0.0.0.0", PORT):
        await asyncio.Future()

asyncio.run(main())
