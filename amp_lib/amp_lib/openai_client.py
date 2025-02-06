import requests
from PySide6.QtWidgets import QMessageBox


class OpenAIClient:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.audio = Audio(self)
        self.images = Images(self)
        self.models = Models(self)

    def check_api_access(self, parent):
        print(self.base_url, self.api_key)
        if self.base_url == "https://api.openai.com/v1" and not self.api_key:
            QMessageBox.warning(
                parent,
                "API Key Required",
                "You need to create an API key to use OpenAI services.",
            )
            return False
        return True

    def chat_completion(self, messages, model="gpt-3.5-turbo", max_tokens=8192):

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        response = requests.post(
            f"{self.base_url}/chat/completions", headers=headers, json=data
        )
        return response.json()


class Audio:
    def __init__(self, client):
        self.client = client
        self.speech = Speech(client)
        self.transcriptions = Transcriptions(client)


class Models:
    def __init__(self, client):
        self.client = client

    def list(self):
        response = requests.get(f"{self.client.base_url}/models")
        json_response = response.json()

        # Convert the response to match OpenAI's structure
        models = []
        for item in json_response.get("data", []):
            model = Model(
                id=item["id"],
                created=item["created"],
                object="model",
                owned_by="system",
            )
            models.append(model)

        return SyncPage(data=models, object="list")


class Model:
    def __init__(self, id, created, object, owned_by):
        self.id = id
        self.created = created
        self.object = object
        self.owned_by = owned_by

    def __str__(self):
        return f"Model(id='{self.id}', created={self.created}, object='{self.object}', owned_by='{self.owned_by}')"

    def __repr__(self):
        return self.__str__()


class SyncPage:
    def __init__(self, data, object):
        self.data = data
        self.object = object

    def __str__(self):
        return f"SyncPage[Model](data={self.data}, object='{self.object}')"

    def __repr__(self):
        return self.__str__()

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, index):
        return self.data[index]


class Transcriptions:
    def __init__(self, client):
        self.client = client

    def create(self, model, file):
        headers = {
            "Authorization": f"Bearer {self.client.api_key}",
        }
        files = {
            "file": file,
        }
        data = {
            "model": model,
        }
        response = requests.post(
            f"{self.client.base_url}/audio/transcriptions",
            headers=headers,
            files=files,
            data=data,
        )
        return TranscriptionResponse(response.json())


class TranscriptionResponse:
    def __init__(self, response_data):
        self.text = response_data.get("text", "")


class AudioResponse:
    def __init__(self, response):
        self.response = response

    def stream_to_file(self, output_path):
        with open(output_path, "wb") as f:
            for chunk in self.response.iter_content(chunk_size=8192):
                f.write(chunk)


class Speech:
    def __init__(self, client):
        self.client = client

    def create(self, model, voice, input):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.client.api_key}",
        }
        data = {
            "model": model,
            "voice": voice,
            "input": input,
        }
        response = requests.post(
            f"{self.client.base_url}/audio/speech",
            headers=headers,
            json=data,
            stream=True,
        )
        return AudioResponse(response)


class Images:
    def __init__(self, client):
        self.client = client

    def generate(self, model, prompt, size, quality, n):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.client.api_key}",
        }
        data = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "n": n,
        }
        response = requests.post(
            f"{self.client.base_url}/images/generations",
            headers=headers,
            json=data,
        )
        return ImageResponse(response.json())


class ImageResponse:
    def __init__(self, response_data):
        self.data = [ImageData(item) for item in response_data.get("data", [])]


class ImageData:
    def __init__(self, data):
        self.b64_json = data.get("b64_json")
