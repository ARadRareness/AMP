from typing import List, Sequence, Union

from amp.language_models.model_message import ModelMessage


class PromptFormatter:
    def __init__(self, model_type: str = ""):
        self.model_type = model_type

    def generate_prompt(
        self, messages: Sequence[ModelMessage]
    ) -> str | List[Union[int, str]]:
        prompt = ""

        for message in messages:
            prompt += (
                f"<|im_start|>{message.get_role()}\n{message.get_message()}<|im_end|>\n"
            )

        return prompt.strip() + "<|im_start|>assistant"
