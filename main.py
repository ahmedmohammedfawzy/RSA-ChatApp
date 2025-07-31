import sys
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class MessageBubble(QWidget):
    def __init__(self, message, is_user=True, timestamp=None):
        super().__init__()
        self.message = message
        self.is_user = is_user
        self.timestamp = timestamp or datetime.now()
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)

        # Create message bubble
        bubble = QLabel(self.message)
        bubble.setWordWrap(True)
        bubble.setMaximumWidth(400)
        bubble.setMinimumHeight(40)

        # Style the bubble based on sender
        if self.is_user:
            bubble.setStyleSheet("""
                QLabel {
                    background-color: #007AFF;
                    color: white;
                    border-radius: 18px;
                    padding: 10px 15px;
                    font-size: 14px;
                }
            """)
            layout.addStretch()
            layout.addWidget(bubble)
        else:
            bubble.setStyleSheet("""
                QLabel {
                    background-color: #E5E5EA;
                    color: black;
                    border-radius: 18px;
                    padding: 10px 15px;
                    font-size: 14px;
                }
            """)
            layout.addWidget(bubble)
            layout.addStretch()

        self.setLayout(layout)

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
        self.setWindowTitle("Conversation")
        self.setGeometry(100, 100, 400, 600)
        self.setup_ui()
        self.load_sample_messages()

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

        # Profile picture placeholder
        profile_pic = QLabel()
        profile_pic.setFixedSize(40, 40)
        profile_pic.setStyleSheet("""
            QLabel {
                background-color: #666;
                border-radius: 20px;
                border: none;
            }
        """)
        profile_pic.setText("B")
        profile_pic.setAlignment(Qt.AlignCenter)
        profile_pic.setStyleSheet("""
            QLabel {
                background-color: #666;
                border-radius: 20px;
                color: white;
                font-weight: bold;
                font-size: 16px;
            }
        """)

        # Name
        name_label = QLabel("Bolbol")
        name_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #000;
                border: none;
            }
        """)

        layout.addWidget(profile_pic)
        layout.addSpacing(10)
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

            # Simulate response after a short delay
            QTimer.singleShot(1000, lambda: self.simulate_response(message))

    def simulate_response(self, user_message):
        # Simple response simulation
        responses = [
            "I understand what you mean.",
            "I see your point.",
            "That makes sense to me."
        ]

        import random
        response = random.choice(responses)
        self.chat_area.add_message(response, is_user=False)

    def load_sample_messages(self):
        # Add some sample messages to match the screenshot
        sample_messages = [
        ]

        for message, is_user in sample_messages:
            self.chat_area.add_message(message, is_user)

def main():
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    window = ChatWindow()
    window.show()

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
