import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QTreeView,
    QHeaderView,
    QStyledItemDelegate,
    QStyle,
    QListView,
    QSplitter,
    QAbstractItemView,
    QMenu,
)
from PySide6.QtGui import (
    QStandardItemModel,
    QStandardItem,
    QIcon,
    QDesktopServices,
    QAction,
    QColor,
    QBrush,
    QKeySequence,
    QShortcut,
    QPixmap,
)
from PySide6.QtCore import Qt, QDir, QUrl, QFileInfo, QSize

import os
import math
import shutil

from interface import file_actions
from interface.icon_mapper import IconMapper


class NoHighlightDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        if option.state & QStyle.State_MouseOver:
            option.state &= ~QStyle.State_MouseOver
        super().paint(painter, option, index)


class FileExplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python File Explorer")
        self.setGeometry(100, 100, 800, 600)

        # Get the directory of the current script
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Set application icon
        icon_path = os.path.join(self.base_dir, "icons", "icon.png")
        self.setWindowIcon(QIcon(icon_path))

        # Load icons

        # Initialize navigation history
        self.history_backward = []
        self.history_forward = []
        self.current_index = -1

        self.icon_mapper = IconMapper(self.base_dir)

        # Create main layout
        main_layout = QVBoxLayout()

        # Create toolbar
        toolbar = QHBoxLayout()
        self.back_btn = QPushButton()
        self.forward_btn = QPushButton()
        self.up_btn = QPushButton()
        self.refresh_btn = QPushButton()
        self.address_bar = QLineEdit()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search")

        # Set icons for buttons
        self.set_button_icon(self.back_btn, "back.png")
        self.set_button_icon(self.forward_btn, "forward.png")
        self.set_button_icon(self.up_btn, "up.png")
        self.set_button_icon(self.refresh_btn, "refresh.png")

        toolbar.addWidget(self.back_btn)
        toolbar.addWidget(self.forward_btn)
        toolbar.addWidget(self.up_btn)
        toolbar.addWidget(self.refresh_btn)
        toolbar.addWidget(self.address_bar)
        toolbar.addWidget(self.search_bar)

        main_layout.addLayout(toolbar)

        # Create splitter to hold the left and right views
        self.splitter = QSplitter(Qt.Horizontal)

        # Create left view for favorite folders
        self.favorites_view = QListView()
        self.favorites_model = QStandardItemModel()
        self.favorites_view.setModel(self.favorites_model)
        self.favorites_view.setEditTriggers(QTreeView.NoEditTriggers)
        self.favorites_view.setSelectionMode(QListView.NoSelection)
        self.populate_favorites()
        self.add_favorites_delimiter()

        self.splitter.addWidget(self.favorites_view)

        # Create tree view for file explorer
        self.tree_view = QTreeView()
        self.model = QStandardItemModel()
        self.tree_view.setModel(self.model)
        self.tree_view.setUniformRowHeights(True)
        self.tree_view.header().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.tree_view.setItemDelegate(NoHighlightDelegate(self.tree_view))
        self.tree_view.setSelectionMode(QTreeView.ExtendedSelection)
        self.tree_view.setEditTriggers(QTreeView.NoEditTriggers)
        self.tree_view.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)

        self.splitter.addWidget(self.tree_view)

        # Set the initial sizes of the splitter
        self.splitter.setSizes([150, 650])  # Adjust these values as needed

        # Set stretch factors: 0 for favorites_view (don't stretch) and 1 for tree_view (stretch)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        main_layout.addWidget(self.splitter)

        # Set up central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Initialize file system
        self.current_path = QDir.rootPath()
        self.update_view()

        # Connect signals
        self.refresh_btn.clicked.connect(self.update_view)
        self.address_bar.returnPressed.connect(self.change_directory)
        self.tree_view.doubleClicked.connect(self.on_double_click)
        self.favorites_view.clicked.connect(self.on_favorite_click)
        self.back_btn.clicked.connect(self.go_back)
        self.forward_btn.clicked.connect(self.go_forward)
        self.up_btn.clicked.connect(self.go_up)

        self.clipboard = []
        self.setup_shortcuts()

    def set_button_icon(self, button, icon_name):
        icon_path = os.path.join(self.base_dir, "icons", icon_name)
        icon = QIcon(QPixmap(icon_path))
        button.setIcon(icon)
        button.setIconSize(QSize(16, 16))  # Adjust size as needed
        button.setFixedSize(24, 24)  # Adjust size as needed

    def setup_shortcuts(self):
        QShortcut(QKeySequence.Copy, self.tree_view, self.copy_clipboard)
        QShortcut(QKeySequence.Paste, self.tree_view, self.paste_clipboard)
        # QShortcut(QKeySequence.Cut, self.tree_view, self.cut_selected)
        QShortcut(QKeySequence.Delete, self.tree_view, self.delete_selected)

    def copy_clipboard(self):
        self.clipboard = []
        for index in self.tree_view.selectedIndexes():
            if index.column() == 0:  # Only process the first column
                item = self.model.itemFromIndex(index)
                file_path = os.path.join(self.current_path, item.text())
                self.clipboard.append(file_path)

    def paste_clipboard(self):
        files_copied = file_actions.copy_files(self.clipboard, self.current_path)

        if files_copied:
            self.update_view()

    def delete_selected(self):
        selected_indexes = self.tree_view.selectedIndexes()
        if not selected_indexes:
            return

        # Get unique rows (files/folders) to delete
        rows_to_delete = set(index.row() for index in selected_indexes)
        items_to_delete = [self.model.item(row, 0).text() for row in rows_to_delete]

        files_deleted = file_actions.delete_files(
            self, items_to_delete, self.current_path
        )

        if files_deleted:
            self.update_view()

    def populate_favorites(self):
        favorites = [
            ("Home", QDir.homePath()),
            ("Desktop", QDir.homePath() + "/Desktop"),
            ("Documents", QDir.homePath() + "/Documents"),
            ("Downloads", QDir.homePath() + "/Downloads"),
            ("Pictures", QDir.homePath() + "/Pictures"),
            ("Music", QDir.homePath() + "/Music"),
            ("Videos", QDir.homePath() + "/Videos"),
            ("Dropbox", QDir.homePath() + "/Dropbox"),
        ]

        # Add available disk drives on Windows
        if sys.platform == "win32":
            import win32api

            drives = win32api.GetLogicalDriveStrings()
            drives = drives.split("\000")[:-1]
            for drive in drives:
                drive_name = drive.rstrip("\\")
                favorites.append((drive_name, drive_name))

        for name, path in favorites:
            if os.path.exists(path):
                item = QStandardItem(name)
                item.setData(path, Qt.UserRole)
                item.setData("default", Qt.UserRole + 1)  # Mark as default favorite
                icon_path = os.path.join(self.base_dir, "icons", "folder.png")
                item.setIcon(QIcon(icon_path))
                self.favorites_model.appendRow(item)

    def add_favorites_delimiter(self):
        delimiter_item = QStandardItem()
        delimiter_item.setEnabled(False)
        delimiter_item.setData("delimiter", Qt.UserRole + 1)

        # Set the background color to light gray
        light_gray_color = QColor(200, 200, 200)  # RGB values for light gray
        delimiter_item.setBackground(QBrush(light_gray_color))

        # Set a custom size hint to make the item thinner
        delimiter_item.setSizeHint(QSize(0, 4))  # Height of 1 pixel

        self.favorites_model.appendRow(delimiter_item)

    def update_view(self):
        # Save current column sizes
        column_sizes = [
            self.tree_view.columnWidth(i) for i in range(self.model.columnCount())
        ]

        self.model.clear()
        self.model.setHorizontalHeaderLabels(["Name", "Date Modified", "Type", "Size"])

        # Set a larger default width for the Name column
        self.tree_view.setColumnWidth(0, 300)  # Adjust this value as needed

        # Restore column sizes for other columns
        for i, size in enumerate(column_sizes[1:], start=1):
            self.tree_view.setColumnWidth(i, size)

        up_item = QStandardItem("..")
        icon_path = os.path.join(self.base_dir, "icons", "folder.png")
        up_item.setIcon(QIcon(icon_path))
        self.model.appendRow(
            [up_item, QStandardItem(), QStandardItem(), QStandardItem()]
        )

        self.address_bar.setText(self.current_path)

        self.load_directory_contents()

        self.update_navigation_buttons()

    def load_directory_contents(self):
        directory = QDir(self.current_path)
        folders = []
        files = []

        for file_info in directory.entryInfoList():
            if file_info.fileName() in [".", ".."]:
                continue

            size_kb = math.ceil(file_info.size() / 1024)
            size_str = f"{size_kb} KB" if file_info.isFile() else ""
            item_data = [
                file_info.fileName(),
                file_info.lastModified().toString("yyyy-MM-dd HH:mm:ss"),
                "File folder" if file_info.isDir() else file_info.suffix(),
                size_str,
                file_info.isDir(),
            ]

            if file_info.isDir():
                folders.append(item_data)
            else:
                files.append(item_data)

        # Process folders first
        for folder in folders:
            self.add_file_item(folder, True)

        # Then process files
        for file in files:
            self.add_file_item(file, False)

    def add_file_item(self, file_data, is_dir):
        name, date, file_type, size, _ = file_data
        name_item = QStandardItem(name)
        print(f"{name}")

        name_item.setIcon(
            self.icon_mapper.get_icon(os.path.join(self.current_path, name))
        )

        self.model.appendRow(
            [
                name_item,
                QStandardItem(date),
                QStandardItem(file_type),
                QStandardItem(size),
            ]
        )

    def on_double_click(self, index):
        if QApplication.mouseButtons() == Qt.LeftButton:
            item = self.model.itemFromIndex(index)
            if item:
                file_name = item.text()
                if file_name == "..":
                    self.go_up()
                else:
                    new_path = QDir(self.current_path).filePath(file_name)
                    file_info = QFileInfo(new_path)
                    if file_info.exists():
                        if file_info.isDir():
                            self.navigate_to(new_path)
                        else:
                            QDesktopServices.openUrl(QUrl.fromLocalFile(new_path))

    def on_favorite_click(self, index):
        item = self.favorites_model.itemFromIndex(index)
        if item and item.data(Qt.UserRole + 1) != "delimiter":
            path = item.data(Qt.UserRole)
            if QDir(path).exists():
                self.navigate_to(path)

    def navigate_to(self, path):
        if path != self.current_path:
            self.history_backward.append(self.current_path)
            self.history_forward.clear()
            self.current_path = path
            self.update_view()

    def go_back(self):
        if self.history_backward:
            self.history_forward.append(self.current_path)
            self.current_path = self.history_backward.pop()
            self.update_view()

    def go_forward(self):
        if self.history_forward:
            self.history_backward.append(self.current_path)
            self.current_path = self.history_forward.pop()
            self.update_view()

    def go_up(self):
        parent_path = QDir(self.current_path).filePath("..")
        self.navigate_to(QDir(parent_path).absolutePath())

    def update_navigation_buttons(self):
        self.back_btn.setEnabled(bool(self.history_backward))
        self.forward_btn.setEnabled(bool(self.history_forward))
        self.up_btn.setEnabled(self.current_path != QDir.rootPath())

    def change_directory(self):
        new_path = self.address_bar.text()
        if QDir(new_path).exists():
            self.navigate_to(new_path)

    def show_context_menu(self, position):
        index = self.tree_view.indexAt(position)
        if index.isValid():
            item = self.model.itemFromIndex(index)
            file_path = os.path.join(self.current_path, item.text())

            if os.path.isdir(file_path):
                context_menu = QMenu(self)
                star_action = QAction("Star folder", self)
                star_action.triggered.connect(lambda: self.star_folder(file_path))
                context_menu.addAction(star_action)

                # Disable the action if the folder is already in favorites
                star_action.setEnabled(not self.is_folder_in_favorites(file_path))

                context_menu.exec(self.tree_view.viewport().mapToGlobal(position))

    def star_folder(self, folder_path):
        folder_name = os.path.basename(folder_path)
        item = QStandardItem(folder_name)
        item.setData(folder_path, Qt.UserRole)
        item.setData("starred", Qt.UserRole + 1)  # Mark as starred favorite
        icon_path = os.path.join(self.base_dir, "icons", "folder.png")
        item.setIcon(QIcon(icon_path))

        # Find the position to insert the new item
        insert_position = self.favorites_model.rowCount()
        for row in range(self.favorites_model.rowCount()):
            current_item = self.favorites_model.item(row)
            if current_item.data(Qt.UserRole + 1) == "delimiter":
                insert_position = row + 1
                break

        # Find the correct position within the starred favorites
        while insert_position < self.favorites_model.rowCount():
            current_item = self.favorites_model.item(insert_position)
            if current_item.text().lower() > folder_name.lower():
                break
            insert_position += 1

        self.favorites_model.insertRow(insert_position, item)

    def is_folder_in_favorites(self, folder_path):
        for row in range(self.favorites_model.rowCount()):
            item = self.favorites_model.item(row)
            if (
                item.data(Qt.UserRole + 1) != "delimiter"
                and item.data(Qt.UserRole) == folder_path
            ):
                return True
        return False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    explorer = FileExplorer()
    explorer.show()
    sys.exit(app.exec())
