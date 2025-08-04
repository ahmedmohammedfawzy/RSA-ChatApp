import json
import sys
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QInputDialog, QMessageBox
from websocekt_client import WebSocketClient
from ui.chat_scroll_area import ChatScrollArea

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.websocket_client = None
        self.setWindowTitle("Conversation")
        self.setGeometry(100, 100, 400, 600)
        self.setup_ui()
        self.get_user_info()
        self.start_websocket()

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

    def get_user_info(self):
        pop = QWidget()
        pop.setWindowTitle("Username Request")

        # Get username
        username, ok = QInputDialog.getText(pop, "Login", "Enter your username:")
        if not ok or not username.strip():
            sys.exit()

        # Validate username
        username = username.strip()
        if len(username) < 3:
            QMessageBox.warning(pop, "Error", "Username must be at least 3 characters!")
            sys.exit()

        self.username = username

        # Get RSA key size
        key_sizes = ["1024", "2048", "3072", "4096"]
        key_size_str, ok = QInputDialog.getItem(pop, 
                                                "RSA Key Size", 
                                                "Select RSA key size (bits):", 
                                                key_sizes, 1, False)  # Default to 2048
        if not ok:
            sys.exit()

        key_bits = int(key_size_str)

        # Warning for weak keys
        if key_bits < 2048:
            reply = QMessageBox.question(pop, "Security Warning", 
                                   f"Key size {key_bits} bits is weak. Continue anyway?",
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
            if reply == QMessageBox.No:
                sys.exit()

        self.RSAKeySize = int(key_size_str)

    def start_websocket(self):
        # 4.234.163.3
        self.websocket_client = WebSocketClient("ws://4.234.163.3:6789", self.RSAKeySize)

        # Connect signals
        self.websocket_client.message_received.connect(self.handle_incoming_message)
        self.websocket_client.connected.connect(lambda: print("🟢 Connected to server"))
        self.websocket_client.disconnected.connect(lambda: print("🔴 Disconnected from server"))
        self.websocket_client.error.connect(lambda err: print(f"❌ WebSocket error: {err}"))

        self.websocket_client.start()

    def send_message(self):
        message = self.message_input.text().strip()
        structured_msg = {"username": self.username, "msg": message}
        if message:
            self.chat_area.add_message(message, self.username, is_user=True)
            self.message_input.clear()

        # Send to WebSocket
        if self.websocket_client:
            self.websocket_client.send_message(json.dumps(structured_msg))


    def handle_incoming_message(self, message):
        try:
            msg_obj = json.loads(message)
            self.chat_area.add_message(msg_obj["msg"], is_user=False, username=msg_obj["username"])
        except json.JSONDecodeError as e:
            print(f"Failed to parse message: {e}")

    def closeEvent(self, a0):
        if self.websocket_client:
            self.websocket_client.stop()
        a0.accept()
