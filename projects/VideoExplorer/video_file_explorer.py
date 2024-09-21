import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import subprocess
import re
from amp_lib.amp_lib import AmpClient
import uuid
import threading
import os
import subprocess
from dotenv import load_dotenv


class VideoFileExplorer:
    def __init__(self, root):
        self.root = root
        self.root.title("Video File Explorer")
        self.root.geometry("800x600")

        # Load environment variables
        load_dotenv()

        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(current_dir, "video_transcriptions.db")

        # Create menu bar
        self.menu_bar = tk.Menu(self.root)
        self.menu_bar.configure(bg="lightblue", fg="black")
        self.root.config(menu=self.menu_bar)

        # Create Options menu
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)

        # Add Download videos option
        self.options_menu.add_command(
            label="Download videos", command=self.start_video_downloader
        )

        # Add Transcribe videos toggle
        self.transcribe_var = tk.BooleanVar()
        self.options_menu.add_checkbutton(
            label="Transcribe videos",
            variable=self.transcribe_var,
            command=self.toggle_transcribe,
        )

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

        # Path search
        ttk.Label(search_frame, text="Path:").grid(row=0, column=2, padx=5)
        self.path_search_var = tk.StringVar()
        self.path_search_entry = ttk.Entry(
            search_frame, textvariable=self.path_search_var
        )
        self.path_search_entry.grid(row=0, column=3, padx=5)

        # Content search
        ttk.Label(search_frame, text="Content:").grid(row=0, column=4, padx=5)
        self.content_search_var = tk.StringVar()
        self.content_search_entry = ttk.Entry(
            search_frame, textvariable=self.content_search_var
        )
        self.content_search_entry.grid(row=0, column=5, padx=5)

        # Add reload button
        reload_button = ttk.Button(
            search_frame, text="Reload", command=self.reload_database
        )
        reload_button.grid(row=0, column=6, padx=5, sticky="E")

        # Configure the grid to push the reload button to the right
        search_frame.grid_columnconfigure(6, weight=1)

        # Bind search function to all entry fields
        for entry in (
            self.name_search_entry,
            self.path_search_entry,
            self.content_search_entry,
        ):
            entry.bind("<KeyRelease>", self.search_videos)

        columns = ("Name", "Path", "Length", "Date modified")

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
                col,
                text=col.capitalize(),
                command=lambda _col=col: self.sort_column(_col, False),
            )
            if col == "Name":
                self.tree.column(col, width=520, minwidth=150)
            elif col == "Path":
                self.tree.column(col, width=70, minwidth=10)
            elif col == "Length":
                self.tree.column(col, width=50, minwidth=50)
            elif col == "Date modified":
                self.tree.column(col, width=115, minwidth=115)
            else:
                self.tree.column(col, width=70, minwidth=70)

        self.tree.bind("<Double-1>", self.play_video)
        self.tree.bind("<Button-3>", self.show_context_menu)  # Add right-click binding

        self.context_menu = tk.Menu(self.root, tearoff=0)
        # Add a new command for showing the transcript
        self.context_menu.add_command(
            label="Show content matches", command=self.show_content_matches
        )
        self.context_menu.add_command(
            label="Show transcript", command=self.show_transcript
        )
        self.context_menu.add_command(
            label="Show summary", command=self.summarize_video
        )

        self.amp_client = AmpClient()

        self.load_videos()
        self.reload_files()

        self.current_sort_column = None
        self.current_sort_reverse = False

        self.transcriber_process = None
        self.toggle_transcribe()  # Initialize the transcriber based on the initial state

    def start_video_downloader(self):
        # Get the start folder and script path from environment variables
        start_folder = os.getenv("VIDEO_DOWNLOADER_START_FOLDER")
        script_path = os.getenv("VIDEO_DOWNLOADER_SCRIPT_PATH")

        if not start_folder or not script_path:
            messagebox.showerror(
                "Error", "Video downloader configuration is missing in the .env file."
            )
            return

        try:
            if os.name == "nt":  # Windows
                subprocess.Popen(
                    [
                        "start",
                        "cmd",
                        "/c",
                        "python",
                        script_path,
                        start_folder,
                        # "& exit",
                    ],
                    shell=True,
                    cwd=os.path.dirname(script_path),
                )
            else:  # macOS and Linux
                subprocess.Popen(
                    ["gnome-terminal", "--", "python", script_path, start_folder],
                    cwd=os.path.dirname(script_path),
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start video downloader: {str(e)}")

    def toggle_transcribe(self):
        is_on = self.transcribe_var.get()
        if is_on:
            print("Transcribe videos turned ON")
            self.start_transcriber()
            print("Transcriber started")
        else:
            print("Transcribe videos turned OFF")
            self.stop_transcriber()

    def start_transcriber(self):
        print("YA?")
        if (
            self.transcriber_process is None
            or self.transcriber_process.poll() is not None
        ):
            print("Starting transcriber")
            # Get the directory of the current file
            current_dir = os.path.dirname(os.path.abspath(__file__))

            # Construct the path to video_transcriber_db.py
            transcriber_path = os.path.join(current_dir, "video_transcriber_db.py")

            # Get the start folder (assuming it's the same as the current directory)
            start_folder = current_dir

            print(start_folder)
            print(transcriber_path)

            # Start the transcriber process
            self.transcriber_process = subprocess.Popen(
                ["python", transcriber_path, start_folder],
                cwd=current_dir,  # Set the working directory
            )

    def stop_transcriber(self):
        if self.transcriber_process and self.transcriber_process.poll() is None:
            self.transcriber_process.terminate()
            self.transcriber_process.wait()
        self.transcriber_process = None

    def __del__(self):
        self.stop_transcriber()  # Ensure the transcriber is stopped when the app is closed

    def reload_database(self):
        self.load_videos()
        # Apply current search filters and sort
        self.search_videos(None)

    def load_videos(self):
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))

        db_path = os.path.join(current_dir, "video_transcriptions.db")

        if not os.path.exists(db_path):
            print(f"Database file not found: {db_path}")
            self.all_videos = []
            return

        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute(
                "SELECT name, path, length, last_changed, transcription, summary, liked FROM transcriptions WHERE removed = 0"
            )
            all_videos = c.fetchall()
            conn.close()

            # Filter videos to only include those that exist
            self.all_videos = [
                video for video in all_videos if os.path.exists(video[1])
            ]
        except sqlite3.Error as e:
            print(f"An error occurred while accessing the database: {e}")
            self.all_videos = []

    def reload_files(self, sort_column=None, reverse=False):
        self.tree.delete(*self.tree.get_children())  # Clear any existing items
        videos_to_display = self.all_videos

        if sort_column:
            column_index = ["Name", "Path", "Length", "Date modified"].index(
                sort_column
            )
            videos_to_display = sorted(
                videos_to_display, key=lambda x: x[column_index], reverse=reverse
            )

        for video in videos_to_display:
            name, path, length, last_changed, transcription, summary, liked = (
                video  # Unpack 5 values
            )
            formatted_length = self.format_length(length)
            directory_path = os.path.dirname(path)
            self.tree.insert(
                "",
                tk.END,
                values=(name, directory_path, formatted_length, last_changed),
            )

    def format_length(self, length):
        hours, remainder = divmod(int(length), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def sort_column(self, col, reverse):
        self.current_sort_column = col
        self.current_sort_reverse = reverse
        if col == "Date modified":
            # For last_changed, start with descending order
            reverse = not reverse

        # Apply current search filters
        self.search_videos(None)

        self.tree.heading(
            col,
            command=lambda: self.sort_column(
                col, not reverse if col != "Date modified" else reverse
            ),
        )

    def search_videos(self, event):
        name_query = self.name_search_var.get().lower()
        path_query = self.path_search_var.get().lower()
        content_query = self.content_search_var.get().lower()

        filtered_videos = [
            video
            for video in self.all_videos
            if (
                name_query in video[0].lower()
                and path_query in os.path.dirname(video[1]).lower()
                and (
                    content_query in (video[4].lower() if video[4] else "")
                    or content_query in (video[5].lower() if video[5] else "")
                )
            )
        ]

        if self.current_sort_column:
            column_index = ["Name", "Path", "Length", "Date modified"].index(
                self.current_sort_column
            )
            filtered_videos.sort(
                key=lambda x: x[column_index], reverse=self.current_sort_reverse
            )

        self.tree.delete(*self.tree.get_children())  # Clear the current tree view

        for video in filtered_videos:
            name, path, length, last_changed, transcription, summary, liked = video
            formatted_length = self.format_length(length)
            directory_path = os.path.dirname(path)
            self.tree.insert(
                "",
                tk.END,
                values=(name, directory_path, formatted_length, last_changed),
            )

    def play_video(self, event):
        if not self.tree.selection():
            return
        item = self.tree.selection()[0]
        directory_path = self.tree.item(item, "values")[1]
        video_name = self.tree.item(item, "values")[0]
        video_path = os.path.join(directory_path, video_name)
        if os.path.exists(video_path):
            subprocess.Popen(["start", "", video_path], shell=True)

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)

            # Recreate the context menu each time
            self.context_menu.delete(0, tk.END)

            # Add "Show content matches" only if there's a content search query
            if self.content_search_var.get():
                self.context_menu.add_command(
                    label="Show content matches", command=self.show_content_matches
                )

            # Always add "Show transcript" option
            self.context_menu.add_command(
                label="Show transcript", command=self.show_transcript
            )

            # Add "Summarize Video" option
            self.context_menu.add_command(
                label="Show summary", command=self.summarize_video
            )

            # Add "Delete" option
            self.context_menu.add_command(label="Delete", command=self.delete_video)

            # Add like/dislike options
            video_name = self.tree.item(item, "values")[0]
            liked_status = self.get_liked_status(video_name)

            if liked_status == 0:
                self.context_menu.add_command(
                    label="Add like",
                    command=lambda: self.update_like_status(video_name, 1),
                )
                self.context_menu.add_command(
                    label="Add dislike",
                    command=lambda: self.update_like_status(video_name, -1),
                )
            elif liked_status == 1:
                self.context_menu.add_command(
                    label="Undo like",
                    command=lambda: self.update_like_status(video_name, 0),
                )
                self.context_menu.add_command(
                    label="Add dislike",
                    command=lambda: self.update_like_status(video_name, -1),
                )
            else:  # liked_status == -1
                self.context_menu.add_command(
                    label="Add like",
                    command=lambda: self.update_like_status(video_name, 1),
                )
                self.context_menu.add_command(
                    label="Undo dislike",
                    command=lambda: self.update_like_status(video_name, 0),
                )

            self.context_menu.post(event.x_root, event.y_root)

    def get_liked_status(self, video_name):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT liked FROM transcriptions WHERE name = ?", (video_name,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else 0

    def update_like_status(self, video_name, new_status):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "UPDATE transcriptions SET liked = ? WHERE name = ?",
            (new_status, video_name),
        )
        conn.commit()
        conn.close()

    def show_content_matches(self):
        item = self.tree.selection()[0]
        video_name = self.tree.item(item, "values")[0]
        content_query = self.content_search_var.get().lower()

        if not content_query:
            messagebox.showinfo(
                "No Content Search", "Please enter a content search query first."
            )
            return

        for video in self.all_videos:
            name, path, length, last_changed, transcription, summary, liked = video
            if name == video_name:
                matches = self.find_content_matches(transcription, content_query)
                summary_matches = (
                    self.find_content_matches(summary, content_query) if summary else []
                )

                all_matches = matches + summary_matches
                if all_matches:
                    self.show_matches_popup(video_name, all_matches)
                else:
                    messagebox.showinfo(
                        "No Matches",
                        f"No matches found for '{content_query}' in {video_name}",
                    )
                break

    def find_content_matches(self, transcription, query):
        matches = []
        shown_ranges = []
        for match in re.finditer(re.escape(query), transcription, re.IGNORECASE):
            start = max(0, match.start() - 300)
            end = min(len(transcription), match.end() + 300)

            # Check if this match overlaps with any previously shown range
            if any(
                s <= match.start() <= e or s <= match.end() <= e
                for s, e in shown_ranges
            ):
                continue

            # Adjust start to beginning of a word
            while start > 0 and not transcription[start - 1].isspace():
                start -= 1

            # Adjust end to end of a word
            while end < len(transcription) and not transcription[end].isspace():
                end += 1

            context = transcription[start:end].strip()
            matches.append(context)
            shown_ranges.append((start, end))
        return matches

    def show_matches_popup(self, video_name, matches):
        popup = tk.Toplevel(self.root)
        popup.title(f"Content Matches - {video_name}")
        popup.geometry("700x400")  # Increased size

        # Create a frame to hold the Text widget and scrollbar
        frame = ttk.Frame(popup)
        frame.pack(expand=True, fill=tk.BOTH)

        # Create the Text widget
        text_widget = tk.Text(frame, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        # Create the scrollbar
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure the Text widget to use the scrollbar
        text_widget.configure(yscrollcommand=scrollbar.set)

        # Create a tag for highlighting
        text_widget.tag_configure("highlight", background="yellow")

        query = self.content_search_var.get().lower()
        for i, match in enumerate(matches, 1):
            text_widget.insert(tk.END, f"Match {i}:\n")

            # Split the match text by the query
            parts = re.split(f"({re.escape(query)})", match, flags=re.IGNORECASE)

            for part in parts:
                if part.lower() == query.lower():
                    text_widget.insert(tk.END, part, "highlight")
                else:
                    text_widget.insert(tk.END, part)

            text_widget.insert(tk.END, "\n\n")

        # Make the Text widget read-only
        text_widget.configure(state="disabled")

        # Ensure the scrollbar is visible even if there's not enough content
        text_widget.update_idletasks()
        if text_widget.yview()[1] == 1.0:
            # Add some empty space to force the scrollbar to appear
            text_widget.configure(state="normal")
            text_widget.insert(tk.END, "\n" * 20)
            text_widget.configure(state="disabled")

        # Set minimum size for the popup
        popup.update_idletasks()
        popup.minsize(popup.winfo_width(), popup.winfo_height())

    def show_transcript(self):
        item = self.tree.selection()[0]
        video_name = self.tree.item(item, "values")[0]

        for video in self.all_videos:
            name, path, length, last_changed, transcription, summary, liked = video
            if name == video_name:
                self.show_transcript_popup(video_name, transcription)
                break

    def show_transcript_popup(self, video_name, transcription):
        popup = tk.Toplevel(self.root)
        popup.title(f"Transcript - {video_name}")
        popup.geometry("700x400")

        frame = ttk.Frame(popup)
        frame.pack(expand=True, fill=tk.BOTH)

        text_widget = tk.Text(frame, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.insert(tk.END, transcription)
        text_widget.configure(state="disabled")

        popup.update_idletasks()
        popup.minsize(popup.winfo_width(), popup.winfo_height())

    def summarize_video(self):
        item = self.tree.selection()[0]
        video_name = self.tree.item(item, "values")[0]

        for video in self.all_videos:
            name, path, length, last_changed, transcription, summary, liked = video
            if name == video_name:
                if summary:
                    # If summary exists, show it immediately
                    self.show_summary_popup(video_name, summary)
                else:
                    # If no summary, create loading popup and generate in thread
                    loading_popup = self.create_loading_popup(video_name)
                    thread = threading.Thread(
                        target=self.generate_summary_thread,
                        args=(video_name, transcription, loading_popup),
                    )
                    thread.start()
                break

    def create_loading_popup(self, video_name):
        popup = tk.Toplevel(self.root)
        popup.title(f"Generating Summary - {video_name}")
        popup.geometry("300x100")

        label = ttk.Label(popup, text="Generating summary, please wait...")
        label.pack(pady=20)

        return popup

    def generate_summary_thread(self, video_name, transcription, loading_popup):
        summary = self.get_video_summary(video_name, transcription)

        # Update the all_videos list with the new summary
        for i, video in enumerate(self.all_videos):
            if video[0] == video_name:
                self.all_videos[i] = video[:5] + (summary,)
                break

        # Use after() to schedule the UI update on the main thread
        self.root.after(0, self.show_summary_popup, video_name, summary, loading_popup)

    def get_video_summary(self, video_name, transcription):
        conversation_id = str(uuid.uuid4())
        prompt = f"""Please provide a concise summary of the following video transcription. The summary should:
1. Be around 3-5 sentences long
2. Capture the main topics or themes discussed
3. Highlight any key points or conclusions
4. Avoid unnecessary details or tangents
5. There might be some named entity mistakes in the transcription, such as pi game instead of pygame, or chad gpt instead of chatgpt, feel free to correct them without mentioning it in the summary
6. Just present the summary, no need for any intro text such as "Here is the summary:" or "Here is a concise summary:"

Video: {video_name}
Transcription:
{transcription}

Summary:"""

        summary = self.amp_client.generate_response(conversation_id, prompt)
        return summary

    def show_summary_popup(self, video_name, summary, loading_popup=None):
        if loading_popup:
            loading_popup.destroy()

        popup = tk.Toplevel(self.root)
        popup.title(f"Video Summary - {video_name}")
        popup.geometry("700x300")

        frame = ttk.Frame(popup)
        frame.pack(expand=True, fill=tk.BOTH)

        text_widget = tk.Text(frame, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.insert(tk.END, summary)
        text_widget.configure(state="disabled")

        popup.update_idletasks()
        popup.minsize(popup.winfo_width(), popup.winfo_height())

    def delete_video(self):
        item = self.tree.selection()[0]
        video_name = self.tree.item(item, "values")[0]
        video_path = os.path.join(self.tree.item(item, "values")[1], video_name)

        # Show confirmation popup
        confirm = messagebox.askyesno(
            "Confirm Deletion", f"Are you sure you want to delete '{video_name}'?"
        )

        if confirm:
            try:
                # Remove the file from the filesystem
                os.remove(video_path)

                # Remove the video from the all_videos list
                self.all_videos = [
                    video for video in self.all_videos if video[0] != video_name
                ]

                # Remove the video from the treeview
                self.tree.delete(item)

            except OSError as e:
                messagebox.showerror(
                    "Error", f"Failed to delete '{video_name}': {str(e)}"
                )


if __name__ == "__main__":
    root = tk.Tk()
    app = VideoFileExplorer(root)
    root.mainloop()
