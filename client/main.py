from PyQt5.QtWidgets import QApplication
from ui.main_window import ChatWindow
import sys

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = ChatWindow()
    window.show()


    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
