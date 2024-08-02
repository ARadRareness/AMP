from typing import List, Optional, Sequence, Union
from language_models.prompt_formatter import PromptFormatter
from language_models.model_message import ModelMessage


# This formatter seems to not be able to produce reliable results, probably due to <s> not expected to be an ordinary string token
class MistralFormatter(PromptFormatter):
    def __init__(self):
        super().__init__("MISTRAL")

        self.BOS = 1
        self.EOS = 2

    # returns a list containing ints and strings
    def generate_prompt(
        self, messages: Sequence[ModelMessage], use_metadata: bool = False
    ) -> List[Union[int, str]]:
        prompt: List[Union[int, str]] = [self.BOS]

        system_message = ""
        system_message_latest = ""
        print(messages)

        for i, message in enumerate(messages):
            if message.is_user_message():
                if i == len(messages) - 1:
                    prompt.append(self._user_message(message, system_message_latest))
                else:
                    prompt.append(self._user_message(message, system_message))
                system_message = ""

            elif message.is_assistant_message():
                prompt.append(f"{message.get_message()}")
                prompt.append(self.EOS)
            elif message.is_system_message():
                system_message = message.get_message()
                system_message_latest = system_message

        if system_message:
            prompt.append(self._user_message(None, system_message))

        print(prompt)
        return prompt

    def _user_message(
        self,
        message: Optional[ModelMessage],
        system_message: str,
    ) -> str:

        prompt_message = ""

        if system_message:
            # prompt_message += f"<SYSTEM_MESSAGE>{system_message}</SYSTEM_MESSAGE>"
            prompt_message += f"{system_message}\n\n"

        if message:
            # prompt_message += f"<USER_MESSAGE>{message.get_message()}</USER_MESSAGE>"
            prompt_message += f"{message.get_message()}"

        return f"[INST] {prompt_message} [/INST]"
