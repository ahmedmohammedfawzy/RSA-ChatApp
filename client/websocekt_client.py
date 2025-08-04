import asyncio
import threading
import websockets
from PyQt5.QtCore import QObject, pyqtSignal

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
        self.worker_thread = None

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
        finally:
            self.websocket = None
            self.disconnected.emit()

    def _run_event_loop(self):
        """Run asyncio event loop in separate thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.listen())
        finally:
            self.loop.close()

    def start(self):
        """Start WebSocket connection"""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.keep_running = True
            self.worker_thread = threading.Thread(target=self._run_event_loop, daemon=True)
            self.worker_thread.start()

    def stop(self):
        """Stop WebSocket connection"""
        self.keep_running = False
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.loop.stop)

        # Wait for thread to finish
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=2.0)

    def send_message(self, msg: str):
        """Send message through WebSocket"""
        if (self.websocket and 
            self.loop and 
            not self.loop.is_closed() and
            self.websocket.state == websockets.protocol.State.OPEN):

            asyncio.run_coroutine_threadsafe(self.websocket.send(msg), self.loop)
        else:
            print("⚠️ WebSocket is not connected.")
