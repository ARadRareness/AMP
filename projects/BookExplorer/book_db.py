import sqlite3


class BookDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.initialize_database()

    def initialize_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='books'"
        )
        table_exists = cursor.fetchone()

        if not table_exists:
            cursor.execute(
                """
                CREATE TABLE books (
                    path TEXT PRIMARY KEY,
                    name TEXT,
                    author TEXT,
                    year TEXT,
                    genre TEXT,
                    analyze_date TEXT,
                    summary TEXT,
                    qa TEXT,
                    rag_qa TEXT,
                    takeaways TEXT,
                    removed BOOLEAN,
                    length INTEGER,
                    liked INTEGER DEFAULT 0,
                    content TEXT
                )
            """
            )
            conn.commit()
            print("Database initialized with books table.")
        else:
            print("Books table already exists.")

        conn.close()

    def load_books(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT name, author, year, path, genre
            FROM books
            WHERE removed = 0
            ORDER BY name
        """
        )

        books = cursor.fetchall()
        conn.close()
        return books

    def get_liked_status(self, book_path):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT liked FROM books WHERE path = ?", (book_path,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

    def update_like_status(self, book_path, new_status):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE books SET liked = ? WHERE path = ?",
            (new_status, book_path),
        )
        conn.commit()
        conn.close()

    def delete_book(self, book_path):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE books SET removed = 1 WHERE path = ?", (book_path,))
        conn.commit()
        conn.close()

    def add_book(self, book_path, book_name, content):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT removed FROM books WHERE path = ?", (book_path,))
        existing_book = cursor.fetchone()

        if existing_book:
            removed = existing_book[0]
            if removed:
                cursor.execute(
                    "UPDATE books SET content = ?, name = ?, removed = 0 WHERE path = ?",
                    (content, book_name, book_path),
                )
                conn.commit()
                conn.close()
                return "restored"
            else:
                conn.close()
                return "duplicate"

        cursor.execute(
            """
            INSERT INTO books (path, name, author, year, genre, analyze_date, summary, qa, rag_qa, takeaways, removed, length, liked, content)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                book_path,
                book_name,
                "Unknown",
                "Unknown",
                "Unknown",
                None,  # analyze_date
                None,  # summary
                None,  # qa
                None,  # rag_qa
                None,  # takeaways
                0,  # removed (default to 0)
                None,  # length # TODO should be calculated from content, number of words
                0,  # liked (default to 0)
                content,  # content
            ),
        )
        conn.commit()
        conn.close()
        return "added"

    def update_book_field(self, book_path, field, value):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE books SET {field} = ? WHERE path = ?", (value, book_path)
            )

    def get_summary(self, book_path):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT summary FROM books WHERE path = ?", (book_path,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_qa_pairs(self, book_path):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT qa FROM books WHERE path = ?", (book_path,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_takeaways(self, book_path):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT takeaways FROM books WHERE path = ?", (book_path,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_rag_qa(self, book_path):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT rag_qa FROM books WHERE path = ?", (book_path,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def get_book_content(self, book_path):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM books WHERE path = ?", (book_path,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def remove_metadata(self, book_path, filename):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE books
            SET name = ?, author = 'Unknown', year = 'Unknown', genre = 'Unknown',
                analyze_date = NULL, summary = NULL, qa = NULL, rag_qa = NULL,
                takeaways = NULL, liked = 0, length = NULL
            WHERE path = ?
            """,
            (filename, book_path),
        )
        conn.commit()
        conn.close()
