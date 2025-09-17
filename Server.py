import asyncio
import websockets
import json
import os  # ใช้ดึง PORT จาก environment

clients = set()

async def handler(websocket):
    clients.add(websocket)
    print(f"✅ Client เชื่อมต่อ: {websocket.remote_address}")
    try:
        async for message in websocket:
            # พยายาม parse ข้อความเป็น JSON
            try:
                data = json.loads(message)
                sender = data.get("from", "unknown")
                msg_text = data.get("msg", "")
            except json.JSONDecodeError:
                sender = "unknown"
                msg_text = str(message)

            print(f"📨 {sender}: {msg_text}")

            # Broadcast ข้อความไปทุก client
            broadcast = json.dumps({"from": sender, "msg": msg_text})
            for client in clients.copy():
                try:
                    await client.send(broadcast)
                except Exception as e:
                    print(f"❌ Client {client.remote_address} ขาดการเชื่อมต่อ: {e}")
                    clients.remove(client)

    except websockets.exceptions.ConnectionClosed:
        print(f"❌ Client {websocket.remote_address} ปิด connection")
    finally:
        clients.discard(websocket)

async def main():
    # ดึง PORT จาก environment variable (Render จะส่งมาให้)
    port = int(os.environ.get("PORT", 9999))
    print(f"🟢 Server รันที่ ws://0.0.0.0:{port}")
    async with websockets.serve(handler, "0.0.0.0", port):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
