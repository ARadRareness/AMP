import os
import time
import sqlite3
from datetime import datetime
from amp_lib import AmpClient
from moviepy.editor import VideoFileClip
import uuid
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


def create_database():
    conn = sqlite3.connect("video_transcriptions.db")
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS transcriptions
                 (name TEXT, path TEXT PRIMARY KEY, last_changed TEXT, transcription TEXT, summary TEXT, removed BOOLEAN, length FLOAT, liked INTEGER DEFAULT 0)"""
    )
    conn.commit()
    conn.close()


def get_mp4_files(drive):
    for root, dirs, files in os.walk(drive):
        for file in files:
            if file.lower().endswith(".mp4"):
                yield os.path.join(root, file)


def get_video_length(file_path):
    try:
        clip = VideoFileClip(file_path)
        length = clip.duration
        clip.close()
        return length
    except Exception as e:
        print(f"Error getting video length for {file_path}: {e}")
        return None


def get_video_summary(amp_client, video_name, transcription):
    conversation_id = "VideoTranscriber_" + str(uuid.uuid4())
    prompt = f"""Please provide a concise summary of the following video transcription. The summary should:
1. Be around 3-5 sentences long
2. Capture the main topics or themes discussed
3. Highlight any key points or conclusions
4. Avoid unnecessary details or tangents
5. There might be some named entity mistakes in the transcription, such as pi game instead of pygame, or chad gpt instead of chatgpt, feel free to correct them without mentioning it in the summary
6. Just present the summary, no need for any other text such as "Here is the summary:"

Video: {video_name}
Transcription:
{transcription}

Summary:"""

    summary = amp_client.generate_response(conversation_id, prompt, max_tokens=5000)
    return summary


class VideoHandler(FileSystemEventHandler):
    def __init__(self):
        self.amp_client = AmpClient()

    def on_created(self, event):
        if event.src_path.lower().endswith(".mp4"):
            print(f"New video detected: {event.src_path}")
            self.process_video(event.src_path)

    def on_modified(self, event):
        if event.src_path.lower().endswith(".mp4"):
            print(f"Video modified: {event.src_path}")
            self.process_video(event.src_path)

    def process_video(self, file_path):
        conn = sqlite3.connect("video_transcriptions.db")
        c = conn.cursor()

        file_name = os.path.basename(file_path)
        last_changed = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
        video_length = get_video_length(file_path)

        print(f"Processing: {file_path}")
        transcription = self.amp_client.speech_to_text(file_path, srt_mode=False)
        summary = get_video_summary(self.amp_client, file_name, transcription)

        if transcription:
            c.execute(
                """INSERT OR REPLACE INTO transcriptions 
                     (name, path, last_changed, transcription, summary, removed, length, liked) 
                     VALUES (?, ?, ?, ?, ?, ?, ?, 0)""",
                (
                    file_name,
                    file_path,
                    last_changed,
                    transcription,
                    summary,
                    False,
                    video_length,
                ),
            )
            conn.commit()

        conn.close()


def update_missing_summaries():
    amp_client = AmpClient()
    conn = sqlite3.connect("video_transcriptions.db")
    c = conn.cursor()

    # Fetch all entries with missing summaries
    c.execute(
        "SELECT name, path, transcription FROM transcriptions WHERE summary IS NULL OR summary = ''"
    )
    entries = c.fetchall()

    for name, path, transcription in entries:
        print(f"Generating summary for: {name}")
        summary = get_video_summary(amp_client, name, transcription)

        # Update the database with the new summary
        c.execute(
            "UPDATE transcriptions SET summary = ? WHERE path = ?", (summary, path)
        )
        conn.commit()

    conn.close()
    print("Finished updating missing summaries.")


def remove_all_summaries(contains):
    conn = sqlite3.connect("video_transcriptions.db")
    c = conn.cursor()
    c.execute(f"UPDATE transcriptions SET summary = '' WHERE name LIKE '%{contains}%'")
    conn.commit()
    conn.close()


def process_videos():
    amp_client = AmpClient()
    conn = sqlite3.connect("video_transcriptions.db")
    c = conn.cursor()

    start_folder = os.getenv("START_FOLDER", "C:\\")

    for file_path in get_mp4_files(start_folder):
        file_name = os.path.basename(file_path)
        last_changed = datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
        video_length = get_video_length(file_path)

        c.execute(
            "SELECT last_changed FROM transcriptions WHERE path = ?", (file_path,)
        )
        result = c.fetchone()

        if result is None or result[0] != last_changed:
            print(f"Processing: {file_path}")
            transcription = amp_client.speech_to_text(file_path, srt_mode=False)
            summary = get_video_summary(amp_client, file_name, transcription)

            if transcription:
                c.execute(
                    """INSERT OR REPLACE INTO transcriptions 
                         (name, path, last_changed, transcription, summary, removed, length, liked) 
                         VALUES (?, ?, ?, ?, ?, ?, ?, 0)""",
                    (
                        file_name,
                        file_path,
                        last_changed,
                        transcription,
                        summary,
                        False,
                        video_length,
                    ),
                )
                conn.commit()

    # Check for removed files
    c.execute("SELECT path FROM transcriptions")
    all_paths = c.fetchall()

    for (path,) in all_paths:
        if not os.path.exists(path):
            c.execute(
                "UPDATE transcriptions SET removed = ? WHERE path = ?", (True, path)
            )
        else:
            c.execute(
                "UPDATE transcriptions SET removed = ? WHERE path = ?", (False, path)
            )

    conn.commit()
    conn.close()


def main():
    create_database()
    update_missing_summaries()

    # Load environment variables
    load_dotenv()
    start_folder = os.getenv("START_FOLDER", "C:\\")

    event_handler = VideoHandler()
    observer = Observer()
    observer.schedule(event_handler, start_folder, recursive=True)
    observer.start()

    try:
        print(f"Watching for video changes in {start_folder}")

        # Process existing videos before starting the watchdog
        print("Processing existing videos...")
        process_videos()
        print("Finished processing existing videos.")

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
