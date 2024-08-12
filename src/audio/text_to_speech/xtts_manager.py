from typing import List
import torch
import hashlib
import os
import subprocess
from TTS.api import TTS  # type: ignore
import spacy


class XttsManager:
    def __init__(self) -> None:
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print("TTS IS USING", self.device)
        self.tts = None

    def text_to_speech(self, text: str) -> str:
        output_folder = "output"
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)

        md5sum = hashlib.md5(text.encode()).hexdigest()
        output_path = os.path.join(output_folder, f"{md5sum}.wav")

        if not os.path.exists(output_path):
            speaker_wav = os.getenv("AUDIO.VOICE_TO_CLONE", "example_audio.wav")

            if self.tts is None:
                self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(
                    self.device
                )

            if os.path.exists(speaker_wav):
                self.tts.tts_to_file(  # type: ignore
                    text,
                    speaker_wav=speaker_wav,
                    file_path=output_path,
                    language="en",
                )
            else:
                print(f"Error: Add a voice file to {speaker_wav} to clone that voice")
        return output_path

    def text_to_speech_with_split(self, text: str):
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
            yield self.text_to_speech(sentence)

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
