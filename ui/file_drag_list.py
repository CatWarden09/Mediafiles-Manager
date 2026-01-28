from pathlib import Path

from PySide6 import QtWidgets
from PySide6.QtCore import Qt, QMimeData, QUrl
from PySide6.QtGui import QDrag

class FileDragList(QtWidgets.QListWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return

        file_path = self.db.get_filepath(item.text())
        if not file_path or not Path(file_path).exists():
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setUrls([QUrl.fromLocalFile(file_path)])
        drag.setMimeData(mime_data)

        drag.exec(Qt.CopyAction)