from datetime import datetime
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt

class MessageBubble(QWidget):
    def __init__(self, message, username, is_user):
        super().__init__()
        self.message = message
        self.is_user = is_user
        self.timestamp = datetime.now()
        self.username = username
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
