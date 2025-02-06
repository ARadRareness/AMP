from typing import List, Optional, Sequence, Union
from amp.language_models.prompt_formatter import PromptFormatter
from amp.language_models.model_message import ModelMessage


class GemmaFormatter(PromptFormatter):
    def __init__(self):
        super().__init__("GEMMA")

    def generate_prompt(self, messages: Sequence[ModelMessage]) -> str:
        prompt = ""
        system_message = ""

        for message in messages:
            if message.is_system_message():
                system_message += message.get_message() + "\n"
            elif message.is_user_message():
                content = (
                    f"SYSTEM MESSAGE: {system_message}\n\n{message.get_message()}"
                    if system_message
                    else message.get_message()
                )
                prompt += self._add_message(content, "user")
                system_message = (
                    ""  # Reset system message after adding it to a user message
                )
            elif message.is_assistant_message():
                prompt += self._add_message(message.get_message(), "model")

        # Always end the prompt with <start_of_turn>model
        prompt += "<start_of_turn>model"
        return prompt

    def _add_message(self, message: str, role: str) -> str:
        return f"<start_of_turn>{role}\n{message}<end_of_turn>\n"
