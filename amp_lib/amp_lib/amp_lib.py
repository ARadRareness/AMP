import struct
import requests
import base64
from typing import Dict, Any, Tuple, List, Generator
from io import BytesIO
from PIL import Image


class AmpClient:
    def __init__(self, base_url: str = "http://localhost:17173"):
        self.base_url = base_url

    def _post(
        self,
        endpoint: str,
        json: Dict[str, Any] = None,
        files: Dict[str, Any] = None,
        json_mode: bool = False,
    ) -> Any:
        response = requests.post(f"{self.base_url}/{endpoint}", json=json, files=files)

        if response.status_code != 200:
            print(response.json())
            return None

        return response.json() if json_mode else response.text

    def _get(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        response = requests.get(f"{self.base_url}/{endpoint}", params=params)

        if response.status_code != 200:
            print(response.json())
            return None

        return response.text

    def add_system_message(self, conversation_id: str, message: str) -> str:
        return self._post(
            "add_system_message",
            {"conversation_id": conversation_id, "message": message},
        )

    def add_user_message(self, conversation_id: str, message: str) -> str:
        return self._post(
            "add_user_message", {"conversation_id": conversation_id, "message": message}
        )

    def add_assistant_message(self, conversation_id: str, message: str) -> str:
        return self._post(
            "add_assistant_message",
            {"conversation_id": conversation_id, "message": message},
        )

    def get_available_models(self) -> List[str]:
        return self._get("get_available_models")

    def get_model_info(self, conversation_id: str) -> Dict[str, Any]:
        return self._post(
            "get_model_info", {"conversation_id": conversation_id}, json_mode=True
        )

    def generate_response(
        self,
        conversation_id: str,
        message: str,
        max_tokens: int = None,
        single_message_mode: bool = False,
        response_prefix: str = "",
    ) -> str:
        data = {
            "conversation_id": conversation_id,
            "message": message,
            "max_tokens": max_tokens,
            "single_message_mode": single_message_mode,
            "response_prefix": response_prefix,
        }
        return self._post("generate_response", data)

    def speech_to_text(self, audio_file_path: str) -> Dict[str, str]:
        with open(audio_file_path, "rb") as file:
            files = {"file": file}
            return self._post("stt", files=files)

    def text_to_speech(
        self, text: str, clone_audio_file_path: str = None
    ) -> Generator[bytes, None, None]:
        data = {"text": text}
        files = {}
        if clone_audio_file_path:
            files["clone_audio"] = open(clone_audio_file_path, "rb")

        response = requests.post(
            f"{self.base_url}/tts", data=data, files=files, stream=True
        )

        if response.status_code != 200:
            print(f"Error generating TTS. status_code={response.status_code}")
            yield b""  # Yield an empty byte string to indicate an error condition gracefully

        while True:
            # Read the size of the next WAV file (4 bytes = 32 bits integer)
            size_data = response.raw.read(4)
            if not size_data:
                break  # No more data, exit the loop

            # Unpack the 4 bytes to an integer (assuming little-endian byte order)
            (size,) = struct.unpack("<I", size_data)

            # Now read the WAV file of the specified size
            wav_data = response.raw.read(size)
            if wav_data:
                yield wav_data
            else:
                break  # In case the data stream is shorter than expected

    def generate_image(
        self, prompt: str, width: int = 1024, height: int = 1024, seed: int = None
    ) -> Tuple[bool, Image.Image]:
        data = {"prompt": prompt, "width": width, "height": height, "seed": seed}
        response = requests.post(f"{self.base_url}/generate_image", json=data)

        if response.status_code != 200:
            print(response.json())
            return None

        # Decode the base64-encoded string
        image_data = base64.b64decode(response.text)

        # Create an image from the decoded data
        return Image.open(BytesIO(image_data))

    def send_telegram_message(self, message: str) -> str:
        return self._post("telegram_message", {"message": message})
