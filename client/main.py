import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt5.QtWidgets import QApplication
from ui.main_window import ChatWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = ChatWindow()
    window.show()


    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
