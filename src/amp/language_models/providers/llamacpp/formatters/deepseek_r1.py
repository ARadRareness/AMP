from typing import Sequence
from amp.language_models.model_message import ModelMessage
from amp.language_models.prompt_formatter import PromptFormatter


class DeepseekR1Formatter(PromptFormatter):
    def __init__(self):
        super().__init__("DeepSeek-R1")

    def generate_prompt(self, messages: Sequence[ModelMessage]) -> str:
        system_prompt = ""
        formatted_messages = []

        # Collect system message
        for message in messages:
            if message.is_system_message():
                system_prompt = message.get_message()

        # Filter out system messages for length check
        non_system_messages = [m for m in messages if not m.is_system_message()]

        # If we only have one user message, return just the message
        if len(non_system_messages) == 1 and non_system_messages[0].is_user_message():
            return f"<｜begin▁of▁sentence｜>{system_prompt}<｜User｜>{non_system_messages[0].get_message()}<｜Assistant｜><｜end▁of▁sentence｜><｜Assistant｜>"

        # Format conversation with User: and Assistant: prefixes
        for message in messages:
            if message.is_user_message():
                formatted_messages.append(f"User: {message.get_message()}")
            elif message.is_assistant_message():
                formatted_messages.append(f"Assistant: {message.get_message()}")

        conversation = "\n".join(formatted_messages)

        return f"<｜begin▁of▁sentence｜>{system_prompt}<｜User｜>{conversation}<｜Assistant｜><｜end▁of▁sentence｜><｜Assistant｜>"
