import shutil
from PySide6.QtWidgets import (
    QMessageBox,
)
from PySide6.QtCore import Qt
import os
from send2trash import send2trash


def delete_files(app, items_to_delete, current_path):
    files_deleted = []

    # Normalize the current_path
    current_path = os.path.normpath(current_path)

    # Confirm deletion
    msg_box = QMessageBox(parent=app)
    # msg_box.setIcon(QMessageBox.Warning)
    msg_box.setText(
        f"Are you sure you want to move {len(items_to_delete)} item(s) to the trash?"
    )
    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    msg_box.setDefaultButton(QMessageBox.No)

    if msg_box.exec() == QMessageBox.Yes:
        for item_name in items_to_delete:
            item_path = os.path.join(current_path, item_name)
            print((item_name, item_path))
            try:
                send2trash(item_path)
                files_deleted.append(item_path)
            except Exception as e:
                QMessageBox.critical(
                    app, "Error", f"Failed to move {item_name} to trash: {str(e)}"
                )

    return files_deleted


def copy_files(items_to_copy, current_path):
    copied_files = []
    for source_path in items_to_copy:
        if not os.path.exists(source_path):
            continue

        copied_files.append(source_path)
        file_name = os.path.basename(source_path)

        destination_path = os.path.join(current_path, file_name)

        if os.path.exists(destination_path):
            # Handle name conflicts
            base, ext = os.path.splitext(file_name)
            counter = 1
            while os.path.exists(destination_path):
                new_name = f"{base} ({counter}){ext}"
                destination_path = os.path.join(current_path, new_name)
                counter += 1

        try:
            if os.path.isdir(source_path):
                shutil.copytree(source_path, destination_path)
            else:
                shutil.copy2(source_path, destination_path)
        except Exception as e:
            print(f"Error copying {source_path}: {str(e)}")

    return copied_files
