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

    def transcribe(self, audio_content):
        md5_hash = hashlib.md5(audio_content).hexdigest()
        filename = f"{md5_hash}.wav"
        filepath = os.path.join("output", filename)

        os.makedirs("output", exist_ok=True)

        # Save the file temporarily
        with open(filepath, "wb") as audio_file:
            audio_file.write(audio_content)

        # Initialize Whisper model if it hasn't been already
        if self.whisper_model is None:
            self.whisper_model = WhisperModel(
                "large-v2", device="cuda", compute_type="float16"
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
            # word_timestamps=True,
        )
        transcript = " ".join([x.text for x in segments])

        # Clean up the saved file
        os.remove(filepath)

        return transcript.strip()
