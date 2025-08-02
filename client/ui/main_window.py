import json
import sys
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QInputDialog
from PyQt5.QtCore import QThread
from websocekt_client import WebSocketClient
from ui.chat_scroll_area import ChatScrollArea

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.websocket_thread = None
        self.websocket_client = None
        self.setWindowTitle("Conversation")
        self.setGeometry(100, 100, 400, 600)
        self.setup_ui()
        self.start_websocket();

        pop = QWidget()
        pop.setWindowTitle("Username Request")

        username, ok = QInputDialog.getText(pop, "Login", "Enter your username:")

        if ok:
            self.username = username
        else:
            sys.exit() 


    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = self.create_header()
        layout.addWidget(header)

        # Chat area
        self.chat_area = ChatScrollArea()
        layout.addWidget(self.chat_area)

        # Input area
        input_area = self.create_input_area()
        layout.addWidget(input_area)

        # Main window style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F2F2F7;
            }
        """)

    def create_header(self):
        header = QWidget()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QWidget {
                background-color: #F8F8F8;
                border-bottom: 1px solid #C7C7CC;
            }
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(15, 10, 15, 10)

        name_label = QLabel("Chat Room")
        name_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #000;
                border: none;
            }
        """)

        layout.addWidget(name_label)
        layout.addStretch()

        return header

    def create_input_area(self):
        input_widget = QWidget()
        input_widget.setFixedHeight(60)
        input_widget.setStyleSheet("""
            QWidget {
                background-color: #F8F8F8;
                border-top: 1px solid #C7C7CC;
            }
        """)

        layout = QHBoxLayout(input_widget)
        layout.setContentsMargins(10, 10, 10, 10)

        # Message input
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type a message...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #C7C7CC;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid #007AFF;
            }
        """)
        self.message_input.returnPressed.connect(self.send_message)

        # Send button
        send_button = QPushButton("Send")
        send_button.setFixedSize(60, 40)
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056CC;
            }
            QPushButton:pressed {
                background-color: #004499;
            }
        """)
        send_button.clicked.connect(self.send_message)

        layout.addWidget(self.message_input)
        layout.addSpacing(5)
        layout.addWidget(send_button)

        return input_widget

    def send_message(self):
        message = self.message_input.text().strip()
        structured_msg = {"username": self.username, "msg": message}
        if message:
            self.chat_area.add_message(message, self.username, is_user=True)
            self.message_input.clear()

        # Send to WebSocket
        if self.websocket_client:
            self.websocket_client.send_message(json.dumps(structured_msg))

    def start_websocket(self):
        self.websocket_client = WebSocketClient("ws://4.234.163.3:6789")
        self.websocket_thread = QThread()
        self.websocket_client.moveToThread(self.websocket_thread)

        self.websocket_thread.started.connect(self.websocket_client.start)
        self.websocket_client.message_received.connect(self.handle_incoming_message)
        self.websocket_client.connected.connect(lambda: print("🟢 Connected to server"))
        self.websocket_client.disconnected.connect(lambda: print("🔴 Disconnected from server"))
        self.websocket_client.error.connect(lambda err: print(f"❌ WebSocket error: {err}"))

        self.websocket_thread.start()

    def handle_incoming_message(self, message):
        msg_obj = json.loads(message)
        print(msg_obj["msg"])
        self.chat_area.add_message(msg_obj["msg"], is_user=False, username=msg_obj["username"])

    def closeEvent(self, a0):
        if self.websocket_client:
            self.websocket_client.stop()
        if self.websocket_thread:
            self.websocket_thread.quit()
            self.websocket_thread.wait()
        a0.accept()
