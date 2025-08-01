import asyncio
import websockets

connected_clients = set()

async def handler(websocket):
    connected_clients.add(websocket)
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
