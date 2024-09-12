import hashlib
import os

from faster_whisper import WhisperModel


class WhisperManager:
    def __init__(self):
        self.whisper_model = None

    def unload_model(self):
        if self.whisper_model is not None:
            del self.whisper_model
            self.whisper_model = None

    def model_is_loaded(self) -> bool:
        return self.whisper_model is not None

    def transcribe(self, audio_content, srt_mode: bool = False):
        md5_hash = hashlib.md5(audio_content).hexdigest()
        filename = f"{md5_hash}.wav"
        filepath = os.path.join("output", filename)

        os.makedirs("output", exist_ok=True)

        # Save the file temporarily
        with open(filepath, "wb") as audio_file:
            audio_file.write(audio_content)

        # Initialize Whisper model if it hasn't been already
        if self.whisper_model is None:
            model_name = os.getenv("AUDIO.WHISPER_MODEL", "base.en")
            print(f"Loading whisper model {model_name}")
            self.whisper_model = WhisperModel(
                model_name, device="cuda", compute_type="int8_float16"  # "float16"
            )

        initial_whisper_prompt = "DEFAULT"
        language = "en"

        # Transcribe audio
        segments, _info = self.whisper_model.transcribe(  # type: ignore
            filepath,
            beam_size=5,
            initial_prompt=initial_whisper_prompt,
            language=language,
            vad_filter=True,
            word_timestamps=True,  # Enable word timestamps for SRT
        )

        if srt_mode:
            transcript = self.generate_srt(segments)
        else:
            transcript = " ".join([x.text for x in segments])

        # Clean up the saved file
        os.remove(filepath)

        return transcript.strip()

    def generate_srt(self, segments):
        srt_output = ""
        for i, segment in enumerate(segments, start=1):
            start = self.format_timestamp(segment.start)
            end = self.format_timestamp(segment.end)
            srt_output += f"{i}\n{start} --> {end}\n{segment.text}\n\n"
        return srt_output.strip()

    def format_timestamp(self, seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"
