from typing import Sequence
from amp.language_models.prompt_formatter import PromptFormatter
from amp.language_models.model_message import ModelMessage


class GLMFormatter(PromptFormatter):
    def __init__(self):
        super().__init__("GLM")

    def generate_prompt(self, messages: Sequence[ModelMessage]) -> str:
        prompt = "[gMASK]<sop> "
        system_message = ""

        for message in messages:
            if message.is_system_message():
                system_message = message.get_message()

        if system_message:
            prompt += f"<|system|> {system_message} "

        for message in messages:
            if message.is_user_message():
                prompt += f"<|user|> {message.get_message()} "
            elif message.is_assistant_message():
                prompt += f"<|assistant|> {message.get_message()} "

        prompt += "<|assistant|>"
        return prompt
