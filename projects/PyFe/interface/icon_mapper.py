from PySide6.QtGui import QIcon
import os


class IconMapper:

    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.folder_icon = QIcon(os.path.join(self.base_dir, "icons", "folder.png"))

        self.text_file_icon = QIcon(
            os.path.join(self.base_dir, "icons", "text_file.png")
        )
        self.dll_file_icon = QIcon(os.path.join(self.base_dir, "icons", "dll_file.png"))
        self.image_file_icon = QIcon(
            os.path.join(self.base_dir, "icons", "image_file.png")
        )
        self.audio_file_icon = QIcon(
            os.path.join(self.base_dir, "icons", "audio_file.png")
        )
        self.video_file_icon = QIcon(
            os.path.join(self.base_dir, "icons", "video_file.png")
        )
        self.archive_file_icon = QIcon(
            os.path.join(self.base_dir, "icons", "archive_file.png")
        )
        self.json_file_icon = QIcon(
            os.path.join(self.base_dir, "icons", "json_file.png")
        )
        self.document_file_icon = QIcon(
            os.path.join(self.base_dir, "icons", "document_file.png")
        )
        self.spreadsheet_file_icon = QIcon(
            os.path.join(self.base_dir, "icons", "spreadsheet_file.png")
        )
        self.presentation_file_icon = QIcon(
            os.path.join(self.base_dir, "icons", "presentation_file.png")
        )
        self.database_file_icon = QIcon(
            os.path.join(self.base_dir, "icons", "database_file.png")
        )
        self.executable_file_icon = QIcon(
            os.path.join(self.base_dir, "icons", "executable_file.png")
        )
        self.python_file_icon = QIcon(
            os.path.join(self.base_dir, "icons", "python_file.png")
        )
        self.pdf_file_icon = QIcon(os.path.join(self.base_dir, "icons", "pdf_file.png"))
        self.default_icon = QIcon(
            os.path.join(self.base_dir, "icons", "unknown_file.png")
        )

    def get_icon(self, file_path: str):
        if os.path.isdir(file_path):
            print(f"{file_path} is a directory")
            return self.folder_icon

        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension in [".txt", ".log", ".md"]:
            return self.text_file_icon
        elif file_extension in [".json"]:
            return self.json_file_icon
        elif file_extension in [".zip", ".rar", ".7z"]:
            return self.archive_file_icon

        elif file_extension in [".exe", ".msi"]:
            return self.executable_file_icon
        elif file_extension in [".dll"]:

            return self.dll_file_icon
        elif file_extension in [
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".bmp",
            ".tiff",
            ".ico",
        ]:
            return self.image_file_icon
        elif file_extension in [
            ".mp3",
            ".wav",
            ".flac",
            ".aac",
            ".m4a",
            ".ogg",
        ]:
            return self.audio_file_icon
        elif file_extension in [
            ".mp4",
            ".mov",
            ".avi",
            ".mkv",
            ".wmv",
            ".flv",
        ]:
            return self.video_file_icon
        elif file_extension in [
            ".doc",
            ".docx",
            ".odt",
            ".xls",
            ".xlsx",
        ]:
            return self.document_file_icon
        elif file_extension in [".py", ".pyw"]:
            return self.python_file_icon
        elif file_extension in [".ods", ".xls", ".xlsx"]:

            return self.spreadsheet_file_icon
        elif file_extension in [".ppt", ".pptx"]:
            return self.presentation_file_icon
        elif file_extension in [
            ".mp3",
            ".wav",
            ".flac",
            ".aac",
            ".m4a",
            ".ogg",
        ]:
            return self.audio_file_icon
        elif file_extension in [".pdf"]:
            return self.pdf_file_icon
        else:
            return self.default_icon
