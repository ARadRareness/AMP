from typing import Sequence
from amp.language_models.model_message import ModelMessage
from amp.language_models.model_response import ModelResponse
from amp.language_models.prompt_formatter import PromptFormatter


class ApiModel:
    def __init__(self, model_path: str, prompt_formatter: PromptFormatter):
        self.model_path = model_path
        self.prompt_formatter = prompt_formatter

    def get_model_path(self) -> str:
        return self.model_path

    def generate_text(
        self,
        messages: Sequence[ModelMessage],
        max_tokens: int = 200,
        temperature: float = 0.2,
        response_prefix: str = "",
    ) -> ModelResponse:
        return ModelResponse("TEXT", "MODEL_NAME")
