import hashlib
import os
import subprocess
import json
from threading import Lock


class WhisperManager:
    def __init__(self):
        self.model_lock = Lock()

    def model_is_loaded(self) -> bool:
        return True

    def transcribe_helper(self, audio_content, srt_mode: bool = False):
        md5_hash = hashlib.md5(audio_content).hexdigest()
        filename = f"{md5_hash}.wav"
        filepath = os.path.join("output", filename)

        os.makedirs("output", exist_ok=True)

        # Save the file temporarily
        with open(filepath, "wb") as audio_file:
            audio_file.write(audio_content)

        segments, _info = self.run_whisper_worker(
            filepath,
        )

        if srt_mode:
            transcript = self.generate_srt(segments)
        else:
            transcript = " ".join([x["text"] for x in segments]).replace("  ", " ")

        # Clean up the saved file
        os.remove(filepath)

        return transcript.strip()

    def run_whisper_worker(self, filepath):
        output_file = f"{filepath}.json"
        worker_script = os.path.join(os.path.dirname(__file__), "whisper_worker.py")
        cmd = ["python", worker_script, filepath, output_file]

        exception = None
        for _ in range(3):
            try:
                result = subprocess.run(
                    cmd, check=False, capture_output=True, text=True
                )

                with open(output_file, "r") as f:
                    result_data = json.load(f)

                os.remove(output_file)
                return result_data["segments"], result_data["info"]

            except subprocess.CalledProcessError as e:
                print(e)
                exception = e
            except Exception as e:
                print(e)
                exception = e

        raise exception

    def transcribe(self, audio_content, srt_mode: bool = False):
        with self.model_lock:
            transcript = self.transcribe_helper(audio_content, srt_mode)
            return transcript

    def generate_srt(self, segments):
        srt_output = ""
        for i, segment in enumerate(segments, start=1):
            # print(segment)
            start = self.format_timestamp(segment["start"])
            end = self.format_timestamp(segment["end"])
            srt_output += f"{i}\n{start} --> {end}\n{segment['text']}\n\n"
        return srt_output.strip()

    def format_timestamp(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"


if __name__ == "__main__":
    whisper_manager = WhisperManager()
    with open("bla.mp4", "rb") as f:
        audio_content = f.read()
    transcript = whisper_manager.transcribe(audio_content, srt_mode=False)
    print(transcript)
