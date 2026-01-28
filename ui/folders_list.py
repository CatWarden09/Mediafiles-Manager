import os, config

from PySide6 import QtWidgets
from PySide6.QtWidgets import QTreeWidgetItem
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt


class FoldersListWindow(QtWidgets.QTreeWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.setHeaderHidden(True)
        self.setFixedWidth(200)
        self.itemClicked.connect(self.on_item_clicked)

    def display_folder_list(self, folder):
        self.clear()
        root_item = self.populate_tree(folder)
        self.addTopLevelItem(root_item)

    def populate_tree(self, folder):
        tree_item = QTreeWidgetItem()
        tree_item.setText(0, os.path.basename(folder))

        icon_path = os.path.join(config.assign_script_dir(), "icons", "folder_icon.png")
        tree_item.setIcon(0, QIcon(icon_path))

        tree_item.setData(0, Qt.UserRole, folder)

        for dir in os.listdir(folder):
            dir_path = os.path.join(folder, dir)
            if os.path.isdir(dir_path) and dir.lower() != "thumbnails":
                tree_item.addChild(self.populate_tree(dir_path))

        return tree_item

    def on_item_clicked(self, item):
        current_path = item.data(0, Qt.UserRole)
        self.main_window.display_files_list(current_path, "folder_tree")
