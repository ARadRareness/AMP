from typing import Sequence
from amp.language_models.model_message import ModelMessage
from amp.language_models.prompt_formatter import PromptFormatter


class Phi4Formatter(PromptFormatter):
    def __init__(self):
        super().__init__("PHI-4")

    def generate_prompt(self, messages: Sequence[ModelMessage]) -> str:
        prompt: str = ""

        system_message = ""

        for message in messages:
            if message.is_system_message():
                system_message = message.get_message()

        if system_message:
            prompt += self._add_message(system_message, "system")

        for message in messages:
            if message.is_user_message():
                prompt += self._add_message(message.get_message(), "user")
            elif message.is_assistant_message():
                prompt += self._add_message(message.get_message(), "assistant")

        prompt += "<|im_start|>assistant<|im_sep|>"
        return prompt

    def _add_message(self, message: str, role: str) -> str:
        return f"<|im_start|>{role}<|im_sep|>{message}<|im_end|>"
