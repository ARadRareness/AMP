import sys
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QMainWindow,
    QFormLayout,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QMenu,
    QMessageBox,
    QTextEdit,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QAction, QTextCursor, QTextCharFormat, QColor
import os
import re
from amp_lib.amp_lib import AmpClient
from dotenv import load_dotenv
from book_db import BookDatabase
from book_summarizer import (
    create_rag_qa_pairs,
    create_shortened_version,
    create_qa_pairs,
    create_best_takeaways,
    analyze_genre,
    analyze_metadata,
)
from epub_lib import load_epub

import tempfile


class AnalyzerThread(QThread):
    update_signal = Signal(str, str, str)

    def __init__(self, book_db, parent=None):
        super().__init__(parent)
        self.book_db = book_db
        self.running = True

    def run(self):
        books = self.book_db.load_books()

        # First pass: Metadata analysis
        for book in books:
            if not self.running:
                break
            self.analyze_metadata(book)

        # Second pass: Other analyses
        for book in books:
            if not self.running:
                break
            self.analyze_book_content(book)

    def analyze_metadata(self, book):
        book_name, author, year, path, genre = book
        if (
            not book_name
            or book_name == "Unknown"
            or book_name.lower().endswith(".epub")
            or not author
            or author == "Unknown"
            or not year
            or year == "Unknown"
        ):
            content = self.book_db.get_book_content(path)
            if content is None:
                print(f"Warning: No content found for book: {book_name}")
                return

            with tempfile.NamedTemporaryFile(
                mode="w", delete=False, suffix=".txt"
            ) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name

            try:
                metadata = analyze_metadata(temp_path)
                if len(metadata) == 3:
                    new_name, new_author, new_year = metadata
                    if new_name and new_name != book_name:
                        self.update_signal.emit(path, "name", new_name)
                        self.book_db.update_book_field(path, "name", new_name)
                    if new_author and new_author != author:
                        self.update_signal.emit(path, "author", new_author)
                        self.book_db.update_book_field(path, "author", new_author)
                    if new_year and new_year != year:
                        self.update_signal.emit(path, "year", str(new_year))
                        self.book_db.update_book_field(path, "year", str(new_year))

                if not genre or genre == "Unknown":
                    genre = analyze_genre(temp_path)
                    self.update_signal.emit(path, "genre", genre)
                    self.book_db.update_book_field(path, "genre", genre)
            finally:
                os.unlink(temp_path)

    def analyze_book_content(self, book):
        book_name, author, year, path, genre = book
        content = self.book_db.get_book_content(path)
        if content is None:
            print(f"Warning: No content found for book: {book_name}")
            return

        with tempfile.NamedTemporaryFile(
            mode="w", delete=False, suffix=".txt"
        ) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        try:

            if not self.book_db.get_summary(path):
                print(f"Generating summary for {path}")
                summary = create_shortened_version(temp_path)
                self.update_signal.emit(path, "summary", summary)
                self.book_db.update_book_field(path, "summary", summary)

            if not self.book_db.get_rag_qa(path):
                print(f"Generating rag_qa_pairs for {path}")
                qa_pairs = create_rag_qa_pairs(temp_path)
                self.update_signal.emit(path, "qa_pairs", qa_pairs)
                self.book_db.update_book_field(path, "qa", qa_pairs)

            if not self.book_db.get_takeaways(path):
                print(f"Generating takeaways for {path}")
                takeaways = create_best_takeaways(temp_path)
                self.update_signal.emit(path, "takeaways", takeaways)
                self.book_db.update_book_field(path, "takeaways", takeaways)
        finally:
            os.unlink(temp_path)
        print("Done analyzing book")

    def stop(self):
        self.running = False


class BookExplorer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Book Explorer")
        self.setGeometry(100, 100, 800, 600)

        load_dotenv()

        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, "books.db")
        self.book_db = BookDatabase(db_path)

        # Initialize sorting attributes
        self.current_sort_column = 0
        self.current_sort_order = Qt.AscendingOrder

        self.setup_ui()
        self.load_books()
        self.setup_menu()
        self.setup_sorting()

        self.amp_client = AmpClient()
        self.analyzer_thread = None

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Search frame
        search_frame = QWidget()
        search_layout = QHBoxLayout(search_frame)

        self.name_search = QLineEdit()
        self.author_search = QLineEdit()
        self.genre_search = QLineEdit()
        self.content_search = QLineEdit()

        search_layout.addWidget(QLabel("Name:"))
        search_layout.addWidget(self.name_search)
        search_layout.addWidget(QLabel("Author:"))
        search_layout.addWidget(self.author_search)
        search_layout.addWidget(QLabel("Genre:"))
        search_layout.addWidget(self.genre_search)

        main_layout.addWidget(search_frame)

        content_search_layout = QHBoxLayout()
        content_search_layout.addWidget(QLabel("Content:"))
        content_search_layout.addWidget(self.content_search)
        reload_button = QPushButton("Reload")
        reload_button.clicked.connect(self.load_books)
        content_search_layout.addWidget(reload_button)

        main_layout.addLayout(content_search_layout)

        # TreeWidget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Author", "Year", "Path", "Genre"])
        self.tree.itemDoubleClicked.connect(self.open_book)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.setSortingEnabled(True)  # Enable sorting
        main_layout.addWidget(self.tree)

        for entry in (
            self.name_search,
            self.author_search,
            self.genre_search,
            self.content_search,
        ):
            entry.textChanged.connect(self.search_books)

        self.setAcceptDrops(True)

    def setup_sorting(self):
        self.tree.header().setSectionsClickable(True)
        self.tree.header().sectionClicked.connect(self.handle_sort)

    def handle_sort(self, logical_index):
        if logical_index == self.current_sort_column:
            # If clicking the same column, toggle the sort order
            self.current_sort_order = (
                Qt.DescendingOrder
                if self.current_sort_order == Qt.AscendingOrder
                else Qt.AscendingOrder
            )
        else:
            # If clicking a different column, set it as the new sort column with ascending order
            self.current_sort_column = logical_index
            self.current_sort_order = Qt.AscendingOrder

        self.tree.sortItems(self.current_sort_column, self.current_sort_order)

    def load_books(self):
        self.tree.clear()
        books = self.book_db.load_books()

        for row in books:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, row[0])  # Name
            item.setText(1, row[1])  # Author
            item.setText(2, row[2])  # Year
            item.setText(3, row[3])  # Path
            item.setText(4, row[4])  # Genre

            # Set the 'Year' column to be treated as numbers for proper sorting
            item.setData(2, Qt.UserRole, int(row[2]) if row[2].isdigit() else 0)

        # Resize columns to content
        for i in range(self.tree.columnCount()):
            self.tree.resizeColumnToContents(i)

        # Sort the tree based on the current sort column and order
        self.tree.sortItems(self.current_sort_column, self.current_sort_order)

    def setup_menu(self):
        menu_bar = self.menuBar()
        options_menu = menu_bar.addMenu("Options")

        analyze_action = QAction("Analyze books", self, checkable=True)
        analyze_action.triggered.connect(self.toggle_analyze)
        options_menu.addAction(analyze_action)

    def toggle_analyze(self, state):
        if state:
            print("Analyze books turned ON")
            self.start_analyzer()
        else:
            print("Analyze books turned OFF")
            self.stop_analyzer()

    def start_analyzer(self):
        if self.analyzer_thread is None or not self.analyzer_thread.isRunning():
            self.analyzer_thread = AnalyzerThread(self.book_db)
            self.analyzer_thread.update_signal.connect(self.update_book_info)
            self.analyzer_thread.start()

    def stop_analyzer(self):
        if self.analyzer_thread and self.analyzer_thread.isRunning():
            self.analyzer_thread.stop()
            self.analyzer_thread.wait()  # Wait for the thread to finish

    def update_book_info(self, book_path, field, value):
        items = self.tree.findItems(
            book_path, Qt.MatchExactly, 3
        )  # Search in the Path column
        if items:
            item = items[0]
            if field == "name":
                item.setText(0, value)
            elif field == "author":
                item.setText(1, value)
            elif field == "year":
                item.setText(2, value)
            elif field == "genre":
                item.setText(4, value)
        self.tree.viewport().update()

    def search_books(self, event):
        search_name = self.name_search.text().lower()
        search_author = self.author_search.text().lower()
        search_genre = self.genre_search.text().lower()
        search_content = self.content_search.text().lower()

        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            name = item.text(0).lower()
            author = item.text(1).lower()
            genre = item.text(4).lower()
            book_path = item.text(3)

            name_match = search_name in name
            author_match = search_author in author
            genre_match = search_genre in genre

            # Content search
            content_match = True
            if search_content:
                content = self.book_db.get_book_content(book_path).lower()
                content_match = search_content in content

            # Show item if all search criteria are met
            item.setHidden(
                not (name_match and author_match and genre_match and content_match)
            )

        # Resize columns to content after filtering
        for i in range(self.tree.columnCount()):
            self.tree.resizeColumnToContents(i)

    def open_book(self, item, column):
        book_path = item.text(3)  # Path is in column 3
        if os.path.exists(book_path):
            if os.name == "nt":  # Windows
                os.startfile(book_path)
            elif os.name == "posix":  # macOS and Linux
                subprocess.call(("open", book_path))
            else:
                subprocess.call(("xdg-open", book_path))

    def show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if item is None:
            return

        context_menu = QMenu(self)

        # Initialize actions
        show_content_matches = None
        show_summary = None
        show_qa = None
        show_takeaways = None
        modify_action = None
        delete_action = None
        remove_metadata_action = None
        like_action = None
        dislike_action = None

        # Only add "Show content matches" if content_search is not empty
        if self.content_search.text().strip():
            show_content_matches = context_menu.addAction("Show content matches")

        show_summary = context_menu.addAction("Show summary")
        show_qa = context_menu.addAction("Show questions and answers")
        show_takeaways = context_menu.addAction("Show takeaways")
        modify_action = context_menu.addAction("Modify")
        delete_action = context_menu.addAction("Delete")
        remove_metadata_action = context_menu.addAction("Remove metadata")

        # Get the liked status for the book
        book_path = item.text(3)  # Path is now in column 3
        liked_status = self.get_liked_status(book_path)

        # Add like/dislike options based on the current status
        if liked_status == 0:
            like_action = context_menu.addAction("Add like")
            dislike_action = context_menu.addAction("Add dislike")
        elif liked_status == 1:
            like_action = context_menu.addAction("Undo like")
            dislike_action = context_menu.addAction("Add dislike")
        else:  # liked_status == -1
            like_action = context_menu.addAction("Add like")
            dislike_action = context_menu.addAction("Undo dislike")

        action = context_menu.exec(self.tree.viewport().mapToGlobal(position))

        if action == show_content_matches:
            self.show_content_matches(item)
        elif action == show_summary:
            self.show_summary(item)
        elif action == show_qa:
            self.show_qa(item)
        elif action == show_takeaways:
            self.show_takeaways(item)
        elif action == modify_action:
            self.modify_book(item)
        elif action == delete_action:
            self.delete_book(item)
        elif action == remove_metadata_action:
            self.remove_metadata(item)
        elif action == like_action:
            new_status = 0 if liked_status == 1 else 1
            self.update_like_status(book_path, new_status)
        elif action == dislike_action:
            new_status = 0 if liked_status == -1 else -1
            self.update_like_status(book_path, new_status)

    def modify_book(self, item):
        book_path = item.text(3)
        book_name = item.text(0)
        author = item.text(1)
        year = item.text(2)
        genre = item.text(4)

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Modify Book - {book_name}")
        layout = QFormLayout(dialog)

        name_edit = QLineEdit(book_name)
        author_edit = QLineEdit(author)
        year_edit = QLineEdit(year)
        genre_edit = QLineEdit(genre)

        layout.addRow("Name:", name_edit)
        layout.addRow("Author:", author_edit)
        layout.addRow("Year:", year_edit)
        layout.addRow("Genre:", genre_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)

        if dialog.exec() == QDialog.Accepted:
            changes = {}
            if name_edit.text() != book_name:
                changes["name"] = name_edit.text()
            if author_edit.text() != author:
                changes["author"] = author_edit.text()
            if year_edit.text() != year:
                changes["year"] = year_edit.text()
            if genre_edit.text() != genre:
                changes["genre"] = genre_edit.text()

            if changes:
                for field, value in changes.items():
                    self.book_db.update_book_field(book_path, field, value)
                self.load_books()  # Refresh the book list to reflect the changes
                QMessageBox.information(
                    self, "Book Updated", "Book information has been updated."
                )
            else:
                QMessageBox.information(
                    self, "No Changes", "No changes were made to the book information."
                )

    def get_liked_status(self, book_path):
        return self.book_db.get_liked_status(book_path)

    def update_like_status(self, book_path, new_status):
        self.book_db.update_like_status(book_path, new_status)
        self.load_books()  # Refresh the book list to reflect the changes

    def show_content_matches(self, item):
        book_path = item.text(3)
        book_name = item.text(0)
        content = self.book_db.get_book_content(book_path)
        search_term = self.content_search.text().strip().lower()

        if not search_term:
            return

        matches = self.find_content_matches(content, search_term)

        if matches:
            self.show_matches_popup(book_name, matches, search_term)
        else:
            QMessageBox.information(
                self,
                "No Matches",
                f"No matches found for '{search_term}' in {book_name}",
            )

    def find_content_matches(self, content, query):
        matches = []
        shown_ranges = []
        for match in re.finditer(re.escape(query), content, re.IGNORECASE):
            start = max(0, match.start() - 300)
            end = min(len(content), match.end() + 300)

            # Check if this match overlaps with any previously shown range
            if any(
                s <= match.start() <= e or s <= match.end() <= e
                for s, e in shown_ranges
            ):
                continue

            # Adjust start to beginning of a word
            while start > 0 and not content[start - 1].isspace():
                start -= 1

            # Adjust end to end of a word
            while end < len(content) and not content[end].isspace():
                end += 1

            context = content[start:end].strip()
            matches.append(context)
            shown_ranges.append((start, end))
        return matches

    def show_matches_popup(self, book_name, matches, search_term):
        popup = QDialog(self)
        popup.setWindowTitle(f"Content Matches - {book_name}")
        popup.setGeometry(100, 100, 700, 400)

        layout = QVBoxLayout(popup)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        normal_format = QTextCharFormat()
        normal_format.setBackground(QColor("white"))

        highlight_format = QTextCharFormat()
        highlight_format.setBackground(QColor("yellow"))

        # Limit the number of matches to 50
        max_matches = min(50, len(matches))
        for i, match in enumerate(matches[:max_matches], 1):
            text_edit.append(f"Match {i}:\n")

            cursor = text_edit.textCursor()
            cursor.movePosition(QTextCursor.End)

            parts = re.split(f"({re.escape(search_term)})", match, flags=re.IGNORECASE)
            for part in parts:
                if part.lower() == search_term.lower():
                    cursor.insertText(part, highlight_format)
                else:
                    cursor.insertText(part, normal_format)

            text_edit.append("")

        # Add a note if there are more matches than displayed
        if len(matches) > max_matches:
            text_edit.append(
                f"Showing {max_matches} out of {len(matches)} total matches."
            )

        popup.exec()

    def show_summary(self, item):
        book_path = item.text(3)
        book_name = item.text(0)
        summary = self.book_db.get_summary(book_path)

        if summary:
            self.show_summary_popup(book_name, summary)
        else:
            QMessageBox.warning(
                self, "No Summary", f"No summary available for {book_name}"
            )

    def show_summary_popup(self, book_name, summary):
        popup = QDialog(self)
        popup.setWindowTitle(f"Summary - {book_name}")
        popup.setGeometry(100, 100, 700, 400)

        layout = QVBoxLayout(popup)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        text_edit.setPlainText(summary)

        popup.exec()

    def show_qa(self, item):
        book_path = item.text(3)
        book_name = item.text(0)
        qa_pairs = self.book_db.get_qa_pairs(book_path)

        if qa_pairs:
            self.show_qa_popup(book_name, qa_pairs)
        else:
            QMessageBox.warning(
                self, "No Q&A", f"No questions and answers available for {book_name}"
            )

    def show_qa_popup(self, book_name, qa_pairs):
        popup = QDialog(self)
        popup.setWindowTitle(f"Q&A - {book_name}")
        popup.setGeometry(100, 100, 700, 400)

        layout = QVBoxLayout(popup)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        text_edit.setPlainText(qa_pairs)

        popup.exec()

    def show_takeaways(self, item):
        book_path = item.text(3)
        book_name = item.text(0)
        takeaways = self.book_db.get_takeaways(book_path)

        if takeaways:
            self.show_takeaways_popup(book_name, takeaways)
        else:
            QMessageBox.warning(
                self, "No Takeaways", f"No takeaways available for {book_name}"
            )

    def show_takeaways_popup(self, book_name, takeaways):
        popup = QDialog(self)
        popup.setWindowTitle(f"Takeaways - {book_name}")
        popup.setGeometry(100, 100, 700, 400)

        layout = QVBoxLayout(popup)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        layout.addWidget(text_edit)

        text_edit.setPlainText(takeaways)

        popup.exec()

    def delete_book(self, item):
        book_name = item.text(0)
        book_path = item.text(3)
        reply = QMessageBox.question(
            self,
            "Delete Book",
            f"Are you sure you want to delete {book_name} from the database?\n\n"
            "Note: This will only remove the book from the database. "
            "The actual file will not be deleted from your computer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.book_db.delete_book(book_path)
            QMessageBox.information(
                self,
                "Delete Book",
                f"{book_name} has been marked as deleted in the database",
            )
            self.tree.takeTopLevelItem(self.tree.indexOfTopLevelItem(item))
            self.load_books()  # Refresh the book list to reflect the changes

    def remove_metadata(self, item):
        book_name = item.text(0)
        book_path = item.text(3)
        reply = QMessageBox.question(
            self,
            "Remove Metadata",
            f"Are you sure you want to remove all metadata for {book_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            filename = os.path.basename(book_path)
            self.book_db.remove_metadata(book_path, filename)
            self.load_books()  # Refresh the book list to reflect the changes

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        added_books = False
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(".epub"):
                print("Adding book to database:", file_path)
                if self.add_book_to_database(file_path):
                    added_books = True
            else:
                QMessageBox.warning(
                    self, "Invalid File", "Please drop only EPUB files."
                )
        if added_books:
            self.load_books()  # Update the tree view

    def add_book_to_database(self, file_path):
        content = load_epub(file_path)
        book_name = os.path.basename(file_path)
        result = self.book_db.add_book(file_path, book_name, content)

        if result == "restored":
            QMessageBox.information(
                self,
                "Book Restored",
                "This book was previously removed and has been restored.",
            )
            return True
        elif result == "duplicate":
            QMessageBox.information(
                self, "Duplicate Book", "This book is already in the database."
            )
            return False
        else:  # "added"
            return True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    explorer = BookExplorer()
    explorer.show()
    sys.exit(app.exec())
