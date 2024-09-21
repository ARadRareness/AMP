import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import subprocess
import re
from amp_lib.amp_lib import AmpClient
import uuid
import threading
from dotenv import load_dotenv


class BookExplorer:
    def __init__(self, root):
        self.root = root
        self.root.title("Book Explorer")
        self.root.geometry("800x600")

        load_dotenv()

        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(current_dir, "books.db")

        # Create menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Create Options menu
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)

        # Add Analyze books toggle
        self.analyze_var = tk.BooleanVar()
        self.options_menu.add_checkbutton(
            label="Analyze books",
            variable=self.analyze_var,
            command=self.toggle_analyze,
        )

        # Set up drag and drop
        self.root.bind("<ButtonRelease-1>", self.on_drop)
        self.root.bind("<Enter>", self.on_enter)

        # Create main frame
        main_frame = ttk.Frame(root)
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Create search frame
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(pady=6, padx=10, fill=tk.X)

        # Name search
        ttk.Label(search_frame, text="Name:").grid(row=0, column=0, padx=5)
        self.name_search_var = tk.StringVar()
        self.name_search_entry = ttk.Entry(
            search_frame, textvariable=self.name_search_var
        )
        self.name_search_entry.grid(row=0, column=1, padx=5)

        # Author search
        ttk.Label(search_frame, text="Author:").grid(row=0, column=2, padx=5)
        self.author_search_var = tk.StringVar()
        self.author_search_entry = ttk.Entry(
            search_frame, textvariable=self.author_search_var
        )
        self.author_search_entry.grid(row=0, column=3, padx=5)

        # Genre search
        ttk.Label(search_frame, text="Genre:").grid(row=0, column=4, padx=5)
        self.genre_search_var = tk.StringVar()
        self.genre_search_entry = ttk.Entry(
            search_frame, textvariable=self.genre_search_var
        )
        self.genre_search_entry.grid(row=0, column=5, padx=5)

        # Content search
        ttk.Label(search_frame, text="Content:").grid(row=1, column=0, padx=5)
        self.content_search_var = tk.StringVar()
        self.content_search_entry = ttk.Entry(
            search_frame, textvariable=self.content_search_var
        )
        self.content_search_entry.grid(
            row=1, column=1, columnspan=3, padx=5, sticky="ew"
        )

        # Add reload button
        reload_button = ttk.Button(
            search_frame, text="Reload", command=self.reload_database
        )
        reload_button.grid(row=1, column=5, padx=5, sticky="E")

        # Bind search function to all entry fields
        for entry in (
            self.name_search_entry,
            self.author_search_entry,
            self.genre_search_entry,
            self.content_search_entry,
        ):
            entry.bind("<KeyRelease>", self.search_books)

        columns = ("Name", "Author", "Year", "Path", "Genre")

        # Create a frame to hold the Treeview and scrollbar
        self.tree_frame = ttk.Frame(main_frame)
        self.tree_frame.pack(pady=6, padx=10, expand=True, fill=tk.BOTH)

        # Create the Treeview widget
        self.tree = ttk.Treeview(self.tree_frame, columns=columns, show="headings")

        # Create the scrollbar
        self.scrollbar = ttk.Scrollbar(
            self.tree_frame, orient="vertical", command=self.tree.yview
        )
        self.scrollbar.pack(side="right", fill="y")

        # Configure the Treeview to use the scrollbar
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.tree.pack(side="left", expand=True, fill=tk.BOTH)

        for col in columns:
            self.tree.heading(
                col, text=col, command=lambda _col=col: self.sort_column(_col, False)
            )
            self.tree.column(col, width=100, minwidth=50)

        self.tree.bind("<Double-1>", self.open_book)
        self.tree.bind("<Button-3>", self.show_context_menu)

        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(
            label="Show content matches", command=self.show_content_matches
        )
        self.context_menu.add_command(label="Show summary", command=self.show_summary)
        self.context_menu.add_command(
            label="Show questions & answers", command=self.show_qa
        )
        self.context_menu.add_command(
            label="Show takeaways", command=self.show_takeaways
        )
        self.context_menu.add_command(label="Delete", command=self.delete_book)
        self.context_menu.add_command(
            label="Add like", command=lambda: self.update_like_status(1)
        )
        self.context_menu.add_command(
            label="Add dislike", command=lambda: self.update_like_status(-1)
        )

        self.amp_client = AmpClient()

        self.load_books()
        self.reload_files()

        self.current_sort_column = None
        self.current_sort_reverse = False

        self.analyzer_process = None
        self.toggle_analyze()

    def toggle_analyze(self):
        is_on = self.analyze_var.get()
        if is_on:
            print("Analyze books turned ON")
            self.start_analyzer()
        else:
            print("Analyze books turned OFF")
            self.stop_analyzer()

    def start_analyzer(self):
        # Implement book analysis process
        pass

    def stop_analyzer(self):
        # Implement stopping book analysis process
        pass

    def load_books(self):
        # Load books from the SQLite database
        pass

    def reload_files(self, sort_column=None, reverse=False):
        # Reload and display books in the treeview
        pass

    def sort_column(self, col, reverse):
        # Implement column sorting
        pass

    def search_books(self, event):
        # Implement book search functionality
        pass

    def open_book(self, event):
        # Implement book opening functionality
        pass

    def show_context_menu(self, event):
        # Show context menu on right-click
        pass

    def show_content_matches(self):
        # Implement content matches display
        pass

    def show_summary(self):
        # Implement summary display
        pass

    def show_qa(self):
        # Implement questions & answers display
        pass

    def show_takeaways(self):
        # Implement takeaways display
        pass

    def delete_book(self):
        # Implement book deletion
        pass

    def update_like_status(self, status):
        # Implement like/dislike functionality
        pass

    def reload_database(self):
        # Reload the database and update the display
        pass

    def on_enter(self, event):
        self.root.focus_force()
        return event.widget

    def on_drop(self, event):
        try:
            file_path = self.root.selection_get(selection="DND_Files")
        except tk.TclError:
            return  # Not a file drop event

        if file_path.lower().endswith(".epub"):
            self.add_book_to_database(file_path)
            self.reload_files()
        else:
            messagebox.showwarning("Invalid File", "Please drop only EPUB files.")

    def add_book_to_database(self, file_path):
        # Extract book information from the epub file
        book_info = self.extract_epub_info(file_path)

        # Insert the book into the database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO books (name, author, year, path, genre)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                book_info["title"],
                book_info["author"],
                book_info["year"],
                file_path,
                book_info["genre"],
            ),
        )
        conn.commit()
        conn.close()

    def extract_epub_info(self, file_path):
        # This is a placeholder. You'll need to implement actual epub metadata extraction.
        return {
            "title": os.path.basename(file_path),
            "author": "Unknown",
            "year": "Unknown",
            "genre": "Unknown",
        }


if __name__ == "__main__":
    root = tk.Tk()
    app = BookExplorer(root)
    root.mainloop()
