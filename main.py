import sys
import config

from PySide6 import QtWidgets, QtGui

from ui import MainWindow

debug = False

if __name__ == "__main__":

    app = QtWidgets.QApplication([])

    # create the main program window
    main_window = MainWindow()
    main_window.setWindowTitle(str("Media Manager v." + config.VERSION))
    main_window.setWindowIcon(QtGui.QIcon(str(config.get_app_icon_path())))
    main_window.resize(1280, 720)

    main_window.show()

    sys.exit(app.exec())
