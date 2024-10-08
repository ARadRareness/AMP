from typing import Sequence
from amp.language_models.model_message import ModelMessage
from amp.language_models.prompt_formatter import PromptFormatter


# This formatter seems to not be able to produce reliable results, probably due to <s> not expected to be an ordinary string token
class Llama3Formatter(PromptFormatter):
    def __init__(self):
        super().__init__("LLAMA3")

    # returns a list containing ints and strings
    def generate_prompt(self, messages: Sequence[ModelMessage]) -> str:
        prompt: str = ""  # Llama.cpp will inject the token below automatically
        # prompt = "<|begin_of_text|>"

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

        prompt += "<|start_header_id|>assistant<|end_header_id|>\n\n"
        return prompt

    def _add_message(self, message: str, role: str) -> str:
        return f"<|start_header_id|>{role}<|end_header_id|>\n\n{message}<|eot_id|>"
