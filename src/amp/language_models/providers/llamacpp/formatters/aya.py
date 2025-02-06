from typing import Sequence
from amp.language_models.prompt_formatter import PromptFormatter
from amp.language_models.model_message import ModelMessage


class AyaFormatter(PromptFormatter):
    def __init__(self):
        super().__init__("Aya")

    def generate_prompt(self, messages: Sequence[ModelMessage]) -> str:
        prompt = ""
        system_message = ""

        for message in messages:
            if message.is_system_message():
                system_message = message.get_message()

        if system_message:
            prompt += (
                "<|START_OF_TURN_TOKEN|><|SYSTEM_TOKEN|>"
                + system_message
                + "<|END_OF_TURN_TOKEN|>"
            )

        for message in messages:
            if message.is_user_message():
                prompt += (
                    "<|START_OF_TURN_TOKEN|><|USER_TOKEN|>"
                    + message.get_message()
                    + "<|END_OF_TURN_TOKEN|>"
                )
            elif message.is_assistant_message():
                prompt += (
                    "<|START_OF_TURN_TOKEN|><|CHATBOT_TOKEN|>"
                    + message.get_message()
                    + "<|END_OF_TURN_TOKEN|>"
                )

        prompt += "<|START_OF_TURN_TOKEN|><|CHATBOT_TOKEN|>"
        return prompt
