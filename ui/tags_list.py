from PySide6 import QtCore, QtWidgets, QtGui


# TODO add "select all" and "deselect all" buttons
class TagsList(QtWidgets.QWidget):
    def __init__(self, main_window, db):
        super().__init__()

        self.main_window = main_window
        self.db = db

        # create the main tags layout
        self.tags_layout = QtWidgets.QVBoxLayout(self)

        self.tags_widget = QtWidgets.QListWidget()

        self.tags_layout.addWidget(self.tags_widget)

        self.changed_items = []

        # self.tags_widget.itemChanged.connect(self.on_item_changed)

    def update_tags_list(self):
        self.tags_widget.clear()

        tags_list = self.db.get_all_tagnames()

        for tag in tags_list:

            checkbox = QtWidgets.QListWidgetItem(tag)

            # | is a bitwise OR to add the item flag without changing all the existing flags
            # it compares every bit in flags() and assigns 1 to the byte at ItemIsUserCheckable position
            # flags() returns a combination of all the item flags enum constants as an int (bit mask)
            checkbox.setFlags(checkbox.flags() | QtCore.Qt.ItemIsUserCheckable)

            checkbox.setCheckState(QtCore.Qt.Unchecked)
            self.tags_widget.addItem(checkbox)

    def get_selected_tags(self):
        selected_tags = []

        for i in range(self.tags_widget.count()):
            item = self.tags_widget.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                selected_tags.append(item.text())

        return selected_tags

    def deselect_all_tags(self):
        for i in range(self.tags_widget.count()):
            item = self.tags_widget.item(i)
            if item.checkState() == QtCore.Qt.Checked:
                item.setCheckState(QtCore.Qt.Unchecked)