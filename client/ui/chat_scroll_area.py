from PyQt5.QtWidgets import QWidget, QScrollArea, QVBoxLayout
from PyQt5.QtCore import QTimer
from .message_bubble import MessageBubble
from PyQt5.QtCore import Qt

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

    def add_message(self, message, username, is_user):
        bubble = MessageBubble(message, username, is_user)
        # Insert before the stretch
        self.content_layout.insertWidget(self.content_layout.count() - 1, bubble)

        # Scroll to bottom
        QTimer.singleShot(50, self.scroll_to_bottom)

    def scroll_to_bottom(self):
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
