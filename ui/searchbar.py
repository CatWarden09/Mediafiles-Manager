import os, config

from PySide6 import QtCore, QtWidgets, QtGui


class SearchBar(QtWidgets.QWidget):
    # signal for folder tree selection clearing when whether the search or cancel icons are clicked
    clicked = QtCore.Signal()

    def __init__(self, main_window, tags_list_ui, db):
        super().__init__()

        self.db = db
        self.tags_list_ui = tags_list_ui
        self.main_window = main_window

        # create the search bar
        self.searchbar = QtWidgets.QLineEdit(self)
        self.searchbar.setPlaceholderText("Поиск по названию или описанию файла...")

        self.searchbar.returnPressed.connect(self.on_search_query_input)

        # create a layout to show the search bar in the main window correctly
        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.searchbar)

        # create the actions for the searchbar - search and cancel icons clicked
        cancel_icon_path = os.path.join(
            config.assign_script_dir(), "icons", "close.png"
        )
        cancel_icon = QtGui.QIcon(str(cancel_icon_path))
        cancel_action = self.searchbar.addAction(
            cancel_icon, QtWidgets.QLineEdit.TrailingPosition
        )

        search_icon_path = os.path.join(
            config.assign_script_dir(), "icons", "search_icon.png"
        )
        search_icon = QtGui.QIcon(str(search_icon_path))
        search_action = self.searchbar.addAction(search_icon, QtWidgets.QLineEdit.LeadingPosition)

        cancel_action.triggered.connect(self.on_cancel_button_clicked)
        search_action.triggered.connect(self.on_search_query_input)

    @QtCore.Slot()
    def on_search_query_input(self):
        query = self.searchbar.text()
        tags = self.tags_list_ui.get_selected_tags()

        if tags and query.strip():

            files_by_tags = self.db.get_files_by_tags(tags)
            files_by_description = self.db.get_files_by_text(query)
            all_files = [file for file in files_by_tags if file in files_by_description]
        elif tags:
            all_files = self.db.get_files_by_tags(tags)
        elif query.strip():
            all_files = self.db.get_files_by_text(query)
        else:
            all_files = self.db.get_all_filenames()

        self.main_window.display_files_list(all_files, "searchbar_clicked")

        self.clicked.emit()

    @QtCore.Slot()
    def on_cancel_button_clicked(self):
        self.searchbar.clear()
        self.tags_list_ui.deselect_all_tags()
        all_files = self.db.get_all_filenames()
        self.main_window.display_files_list(all_files, "searchbar_canceled")

        self.clicked.emit()
