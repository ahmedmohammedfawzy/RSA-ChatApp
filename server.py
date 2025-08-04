import asyncio
import os
import websockets
import json
from shared import encryption

connected_clients = set()
aes_key_bytes = os.urandom(16)


async def handler(websocket):
    connected_clients.add(websocket)
    init_msg = await websocket.recv()
    data = json.loads(init_msg);

    pub_key = data.get("key")
    encrypted_aes = encryption.encrypt_oaep(aes_key_bytes, pub_key)
    await websocket.send(json.dumps({"type": "ISC", "key": encrypted_aes}))

    try:
        async for message in websocket:
            # Broadcast incoming message to all connected clients
            await asyncio.gather(*[
                client.send(message) for client in connected_clients
                if client != websocket
            ])
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        connected_clients.remove(websocket)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 6789):
        print("✅ WebSocket server running on ws://0.0.0.0:6789")
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
