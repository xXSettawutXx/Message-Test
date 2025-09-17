import asyncio
import websockets
import json

clients = set()

async def handler(websocket, path):
    clients.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            print(f"[{data['name']}] {data['msg']}")

            # ส่งข้อความให้ทุก client
            for client in clients:
                if client != websocket:  # ไม่ส่งกลับตัวเอง
                    await client.send(json.dumps(data))
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        clients.remove(websocket)

async def main():
    # Railway จะกำหนด PORT ให้เอง
    import os
    port = int(os.environ.get("PORT", 8765))
    async with websockets.serve(handler, "0.0.0.0", port):
        print(f"Server started on port {port}")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
