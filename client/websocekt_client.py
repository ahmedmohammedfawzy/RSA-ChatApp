import asyncio
import json
import os
import threading
import websockets
from shared import encryption
from PyQt5.QtCore import QObject, pyqtSignal
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# --- Step 1: Padding function ---
def pad(data):
    padder = padding.PKCS7(128).padder()
    return padder.update(data) + padder.finalize()

def unpad(padded_data):
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded_data) + unpadder.finalize()

# --- Step 2: AES-CBC Encryption ---
def aes_cbc_encrypt(plaintext: bytes, key: bytes, iv: bytes):
    plaintext_padded = pad(plaintext)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(plaintext_padded) + encryptor.finalize()
    return ciphertext

# --- Step 3: AES-CBC Decryption ---
def aes_cbc_decrypt(ciphertext: bytes, key: bytes, iv: bytes):
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
    return unpad(padded_plaintext)

class WebSocketClient(QObject):
    message_received = pyqtSignal(str)
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, uri, rsaKeySize):
        super().__init__()
        self.uri = uri
        self.keep_running = True
        self.websocket = None
        self.loop = None
        self.worker_thread = None
        self.public_key, self.private_key = encryption.generate_keys(rsaKeySize)
        self.aes_key = bytes(16)

    async def listen(self):
        try:
            async with websockets.connect(self.uri) as websocket:
                self.websocket = websocket
                self.connected.emit()

                await websocket.send(json.dumps({"type": "ISC", "key": self.public_key}))

                while self.keep_running:
                    try:
                        msg = await websocket.recv()
                        if isinstance(msg, str):
                            data = json.loads(msg)
                            enc_key: int = data["key"]
                            key = encryption.decrypt_oaep(enc_key, self.private_key)
                            self.aes_key = key
                        else:
                            dec_msg = aes_cbc_decrypt(msg[16:],self.aes_key, msg[:16])
                            self.message_received.emit(dec_msg.decode())
                    except websockets.ConnectionClosed:
                        break

        except Exception:
            if self.keep_running:
                raise
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

            iv = os.urandom(16)
            enc_msg = iv + aes_cbc_encrypt(msg.encode(),self.aes_key, iv)
            print(enc_msg)
            asyncio.run_coroutine_threadsafe(self.websocket.send(enc_msg), self.loop)
        else:
            print("⚠️ WebSocket is not connected.")


