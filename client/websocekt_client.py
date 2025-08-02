from PyQt5.QtCore import QObject, pyqtSignal
import websockets
import asyncio
import threading

class WebSocketClient(QObject):
    message_received = pyqtSignal(str)
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, uri):
        super().__init__()
        self.uri = uri
        self.keep_running = True
        self.websocket = None
        self.loop = None
        self.lock = threading.Lock()

    async def listen(self):
        try:
            async with websockets.connect(self.uri) as websocket:
                self.websocket = websocket
                self.connected.emit()
                while self.keep_running:
                    try:
                        msg = await websocket.recv()
                        self.message_received.emit(msg)
                    except websockets.ConnectionClosed:
                        break
        except Exception as e:
            if self.keep_running:
                self.error.emit(str(e))

        self.websocket = None
        self.disconnected.emit()

    def start(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.listen())

    def stop(self):
        self.keep_running = False
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)

    def send_message(self, msg: str):
        if self.websocket and self.loop and self.websocket.state == websockets.protocol.State.OPEN:
            asyncio.run_coroutine_threadsafe(self.websocket.send(msg), self.loop)
        else:
            print("⚠️ WebSocket is not connected.")
