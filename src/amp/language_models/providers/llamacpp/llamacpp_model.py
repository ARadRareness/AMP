import logging
from typing import Sequence
import requests
import json
from amp.language_models.api_model import ApiModel
from amp.language_models.model_message import ModelMessage
from amp.language_models.model_response import ModelResponse
from amp.language_models.prompt_formatter import PromptFormatter

logger = logging.getLogger(__name__)


class LlamaCppModel(ApiModel):
    def __init__(
        self,
        host_url: str,
        host_port: str,
        prompt_formatter: PromptFormatter,
        model_path: str,
    ):
        super().__init__(model_path, prompt_formatter)

        self.host_url = host_url
        self.host_port = host_port

    def generate_text(
        self,
        messages: Sequence[ModelMessage],
        max_tokens: int = 200,
        temperature: float = 0.2,
        response_prefix: str = "",
    ) -> ModelResponse:
        prompt = self.prompt_formatter.generate_prompt(messages)

        if response_prefix:
            prompt += response_prefix

        request = {
            "prompt": prompt,
            "n_predict": max_tokens,
            "temperature": temperature,
            "top_p": 0.8,
            "min_p": 0.05,
            "typical_p": 1,
            "repeat_penalty": 1.18,
            "top_k": 40,
        }

        with open("_input.txt", "w", encoding="utf8") as file:
            file.write(str(prompt))

        url = f"http://{self.host_url}:{self.host_port}/completion"

        logger.info("LLAMA-CPP: GENERATING RESPONSE")
        response = requests.post(url, json=request)
        logger.info("LLAMA-CPP: RESPONSE GENERATED")

        with open("_output.json", "w") as file:
            json.dump(response.json(), file)

        if response.status_code == 200:
            json_data = response.json()
            content = json_data["content"].strip()
            if "<|eot_id|>" in content:  # Temporary fix for LLama-3
                content = content.split("<|eot_id|>")[0]
            return ModelResponse(content, json_data["model"])

        return ModelResponse("", "")
