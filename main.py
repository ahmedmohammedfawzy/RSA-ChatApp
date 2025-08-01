from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import websockets
import asyncio
import sys
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

class MessageBubble(QWidget):
    def __init__(self, message, is_user=True, timestamp=None, username=None):
        super().__init__()
        self.message = message
        self.is_user = is_user
        self.timestamp = timestamp or datetime.now()
        self.username = username or ("You" if is_user else "Other")
        self.setup_ui()
    
    def setup_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(10, 5, 10, 5)
        
        # Create container for message content
        message_container = QVBoxLayout()
        message_container.setSpacing(2)
        
        # Create username and timestamp header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        username_label = QLabel(self.username)
        username_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
                font-weight: bold;
                margin: 0px;
                padding: 0px;
            }
        """)
        
        timestamp_label = QLabel(self.timestamp.strftime("%H:%M"))
        timestamp_label.setStyleSheet("""
            QLabel {
                color: #999999;
                font-size: 11px;
                margin: 0px;
                padding: 0px;
            }
        """)
        
        separator_label = QLabel("•")
        separator_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 11px;
                margin: 0px 3px;
                padding: 0px;
            }
        """)
        
        # Create message bubble
        bubble = QLabel(self.message)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(int(self.width() * 0.8)) 
        print(self.message)
        
        # Style and arrange based on sender
        if self.is_user:
            # User messages - right aligned
            bubble.setStyleSheet("""
                QLabel {
                    background-color: #007AFF;
                    color: white;
                    border-radius: 18px;
                    padding: 10px 15px;
                    font-size: 14px;
                }
            """)
            
            # Right-align header
            header_layout.addStretch()
            header_layout.addWidget(username_label)
            header_layout.addWidget(separator_label)
            header_layout.addWidget(timestamp_label)
            
            # Add header and bubble to container
            message_container.addLayout(header_layout)
            message_container.addWidget(bubble, alignment=Qt.AlignRight)
            
            # Right-align the entire message
            main_layout.addStretch()
            main_layout.addLayout(message_container)
        else:
            # Assistant messages - left aligned
            bubble.setStyleSheet("""
                QLabel {
                    background-color: #E5E5EA;
                    color: black;
                    border-radius: 18px;
                    padding: 10px 15px;
                    font-size: 14px;
                }
            """)
            
            # Left-align header
            header_layout.addWidget(username_label)
            header_layout.addWidget(separator_label)
            header_layout.addWidget(timestamp_label)
            header_layout.addStretch()
            
            # Add header and bubble to container
            message_container.addLayout(header_layout)
            message_container.addWidget(bubble, alignment=Qt.AlignLeft)
            
            # Left-align the entire message
            main_layout.addLayout(message_container)
            main_layout.addStretch()
        
        self.setLayout(main_layout)

class ChatScrollArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Content widget
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(5)
        self.content_layout.setContentsMargins(0, 10, 0, 10)
        self.content_layout.addStretch()

        self.setWidget(self.content_widget)

        # Style
        self.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #F2F2F7;
            }
            QScrollBar:vertical {
                background-color: #F2F2F7;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #C7C7CC;
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #AEAEB2;
            }
        """)

    def add_message(self, message, is_user=True):
        bubble = MessageBubble(message, is_user)
        # Insert before the stretch
        self.content_layout.insertWidget(self.content_layout.count() - 1, bubble)

        # Scroll to bottom
        QTimer.singleShot(50, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.websocket_thread = None
        self.websocket_client = None
        self.setWindowTitle("Conversation")
        self.setGeometry(100, 100, 400, 600)
        self.setup_ui()
        self.start_websocket();


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
        if message:
            self.chat_area.add_message(message, is_user=True)
            self.message_input.clear()

        # Send to WebSocket
        if self.websocket_client:
            self.websocket_client.send_message(message)

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
        self.chat_area.add_message(message, is_user=False)

    def closeEvent(self, a0):
        if self.websocket_client:
            self.websocket_client.stop()
        if self.websocket_thread:
            self.websocket_thread.quit()
            self.websocket_thread.wait()
        a0.accept()



def main():
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    window = ChatWindow()
    window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
