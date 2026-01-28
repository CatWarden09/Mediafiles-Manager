import config
from PySide6 import QtCore, QtWidgets, QtGui

PROTECTED_TAGS = ["Audio", "Video", "Image"]

class TagsSettingsWindow(QtWidgets.QWidget):
    # TODO add confirm window when deleting a tag
    def __init__(self, tags_list, db, error_window):
        super().__init__()

        self.db = db
        self.error_window = error_window
        self.main_tags_list = tags_list

        self.setWindowIcon(QtGui.QIcon(str(config.get_app_icon_path())))
        self.setWindowTitle("Настройки тегов")
        self.resize(600, 400)

        # create the window layout
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.tags_list = QtWidgets.QListWidget()

        # create manage buttons
        self.add_button = QtWidgets.QPushButton("Добавить тег")
        self.delete_button = QtWidgets.QPushButton("Удалить тег")

        # add widgets to the layouts
        self.buttons_layout.addWidget(self.add_button)
        self.buttons_layout.addWidget(self.delete_button)
        self.main_layout.addLayout(self.buttons_layout)
        self.main_layout.addWidget(self.tags_list)

        # connect to buttons click
        self.add_button.clicked.connect(self.on_add_button_clicked)
        self.delete_button.clicked.connect(self.on_delete_button_clicked)

    def add_tags_to_list(self, tag):
        item = QtWidgets.QListWidgetItem(tag)

        self.tags_list.addItem(item)

    def update_tags_list(self):
        self.tags_list.clear()

        tags_list = self.db.get_all_tagnames()

        for tag in tags_list:
            item = QtWidgets.QListWidgetItem(tag)

            self.tags_list.addItem(item)

    # button click events
    @QtCore.Slot()
    def on_add_button_clicked(self):
        tag_name, ok = QtWidgets.QInputDialog.getText(
            self, "Новый тег", "Введите название тега"
        )

        if ok:
            if tag_name.strip():
                # TODO add protection from creating same tags but with different register (Audio - audio) etc.
                if not self.db.tag_exists(tag_name):
                    self.db.save_tag_to_database(tag_name)
                    self.add_tags_to_list(tag_name)
                    self.main_tags_list.update_tags_list()
                else:
                    self.error_window.show_error_message(
                        "Тег с таким названием уже добавлен!"
                    )
            else:
                self.error_window.show_error_message("Укажите название тега!")

    @QtCore.Slot()
    def on_delete_button_clicked(self):
        item = self.tags_list.currentItem()

        if item is None:
            self.error_window.show_error_message("Выберите тег для удаления!")
        elif item.text() in PROTECTED_TAGS:
            self.error_window.show_error_message("Невозможно удалить стандартные теги!")
        else:
            tag = item.text()
            self.db.delete_tag_from_database(tag)
            self.update_tags_list()
            self.main_tags_list.update_tags_list()


class ItemTagsSettingsWindow(TagsSettingsWindow):
    def __init__(self, main_window, preview_window, tags_list, db, error_window):
        super().__init__(tags_list, db, error_window)

        self.db = db
        self.error_window = error_window
        self.setWindowTitle("Изменить теги")
        self.main_window = main_window
        self.preview_window = preview_window

        self.common_tags_list_label = QtWidgets.QLabel("Доступные теги:")
        self.current_tags_list_label = QtWidgets.QLabel("Теги выбранного файла:")

        # hide the parent's tags list because here we need 2 separate tag lists
        self.tags_list.hide()

        # create a VBox to separate lists labels and the lists themselves
        self.main_vbox = QtWidgets.QVBoxLayout()

        # create an HBox for lists labels
        self.labels_hbox = QtWidgets.QHBoxLayout()

        # add the lists labels to their Hbox
        self.labels_hbox.addWidget(self.common_tags_list_label)
        self.labels_hbox.addWidget(self.current_tags_list_label)

        # create a Hbox for 2 tags lists
        self.list_hbox = QtWidgets.QHBoxLayout()
        self.common_tags_list = QtWidgets.QListWidget()
        self.current_tags_list = QtWidgets.QListWidget()
        self.common_tags_list.setSelectionMode(
            QtWidgets.QAbstractItemView.MultiSelection
        )
        self.current_tags_list.setSelectionMode(
            QtWidgets.QAbstractItemView.MultiSelection
        )

        # add common and current tags lists to the tags list layout
        self.list_hbox.addWidget(self.common_tags_list)
        self.list_hbox.addWidget(self.current_tags_list)

        # place the Hboxes inside the main Vbox
        self.main_vbox.addLayout(self.labels_hbox)
        self.main_vbox.addLayout(self.list_hbox)

        # add the tags list layout to the main layout
        self.main_layout.addLayout(self.main_vbox)

    def set_tags_list(self):
        # prepare both tags list for display
        # define current selected item, then get tags_list from the DB and make 2 tuples for current item tags and available tags accordinly
        # clear both lists to avoid tags duplication on next settings window openings
        # after lists are ready, call update_lists function to display both lists in the current item tags settings window
        current_item = self.main_window.get_current_item().text()

        self.common_tags_list.clear()
        self.current_tags_list.clear()

        self.current_tags_tuple = self.db.get_current_item_tags(current_item)
        self.common_tags_tuple = [
            tag
            for tag in self.db.get_all_tagnames()
            if tag not in self.current_tags_tuple
        ]

        self.update_lists(self.current_tags_list, self.current_tags_tuple)
        self.update_lists(self.common_tags_list, self.common_tags_tuple)

    # update both lists using the same method to avoid code duplication
    def update_lists(self, target_list, tags_list):
        for tag in tags_list:
            item = QtWidgets.QListWidgetItem(tag)

            target_list.addItem(item)

    @QtCore.Slot()
    def on_add_button_clicked(self):
        # get current selected item from the main window and current selected tags from available tags list
        # and save the selected tags for the selected file in the DB
        # also update tags list in the file preview window
        current_item = self.main_window.get_current_item().text()
        selected_tags_list = self.common_tags_list.selectedItems()

        # protection from adding more than 1 standard tag (Audio, Video, Image)
        assigned_tags = [
            self.current_tags_list.item(i).text()
            for i in range(self.current_tags_list.count())
        ]

        selected_tags = [tag.text() for tag in selected_tags_list]

        all_tags_after_add = assigned_tags + selected_tags

        standard_tags_count = sum(tag in PROTECTED_TAGS for tag in all_tags_after_add)

        if not selected_tags:
            self.error_window.show_error_message(
                "Не выбран ни один тег для добавления!"
            )
        elif standard_tags_count > 1:
            self.error_window.show_error_message(
                "Невозможно добавить более одного стандартного тега!"
            )
        else:
            self.db.save_current_item_tags(current_item, selected_tags)
            self.set_tags_list()
            self.preview_window.update_item_tags_list(current_item)

    @QtCore.Slot()
    def on_delete_button_clicked(self):
        current_item = self.main_window.get_current_item().text()
        selected_tags_list = self.current_tags_list.selectedItems()

        # protection from deleting a standard tag (Audio, Video, Image)
        selected_tags = [tag.text() for tag in selected_tags_list]
        protected_tag_found = any(tag in PROTECTED_TAGS for tag in selected_tags)

        if selected_tags and not protected_tag_found:
            self.db.delete_current_item_tags(current_item, selected_tags)
            self.set_tags_list()
            self.preview_window.update_item_tags_list(current_item)
        elif protected_tag_found:
            self.error_window.show_error_message("Невозможно удалить стандартные теги!")
        else:
            self.error_window.show_error_message("Не выбран ни один тег для удаления!")