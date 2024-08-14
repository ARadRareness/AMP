from typing import List, Optional
import torch
import hashlib
import os
from TTS.api import TTS  # type: ignore
import spacy


class XttsManager:
    def __init__(self) -> None:
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print("TTS IS USING", self.device)
        self.tts = None

    def text_to_speech(
        self, text: str, clone_audio_data: Optional[bytes] = None
    ) -> str:
        output_folder = "output"
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)

        md5sum = hashlib.md5(text.encode()).hexdigest()
        output_path = os.path.join(output_folder, f"{md5sum}.wav")

        if not os.path.exists(output_path):
            if self.tts is None:
                self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(
                    self.device
                )

            if clone_audio_data:
                # Create a temporary file for the clone audio data
                temp_audio_path = os.path.join(output_folder, "temp_clone_audio.wav")
                with open(temp_audio_path, "wb") as temp_file:
                    temp_file.write(clone_audio_data)
                speaker_wav = temp_audio_path
            else:
                speaker_wav = os.getenv("AUDIO.VOICE_TO_CLONE", "example_audio.wav")

            if os.path.exists(speaker_wav):
                self.tts.tts_to_file(  # type: ignore
                    text,
                    speaker_wav=speaker_wav,
                    file_path=output_path,
                    language="en",
                )
            else:
                print(f"Error: Add a voice file to {speaker_wav} to clone that voice")

            # Remove the temporary file if it was created
            if clone_audio_data and os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)

        return output_path

    def text_to_speech_with_split(
        self, text: str, clone_audio_data: Optional[bytes] = None
    ):
        try:
            nlp = spacy.load("en_core_web_sm")
        except:
            from spacy.cli import download  # type: ignore

            download("en_core_web_sm")
            nlp = spacy.load("en_core_web_sm")

        text = self.filter_text(text)

        doc = nlp(text)

        sentences: List[str] = []
        current_sentence: str = ""
        for sentence in doc.sents:
            current_sentence += sentence.text
            if len(current_sentence) > 20:
                sentences.append(current_sentence)
                current_sentence = ""
        if current_sentence:
            sentences.append(current_sentence)

        for sentence in sentences:
            yield self.text_to_speech(sentence, clone_audio_data)

    def filter_text(self, text: str) -> str:
        response = "".join(
            char if not (0x1F600 <= ord(char) <= 0x1F64F) else "," for char in text
        )

        response = response.replace("*", " ")

        return response

    def model_is_loaded(self):
        return self.tts is not None

    def unload_model(self):
        if self.tts is not None:
            del self.tts
            self.tts = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
