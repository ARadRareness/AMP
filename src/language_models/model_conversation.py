import datetime
from typing import List, Sequence
from language_models.api_model import ApiModel

from language_models.model_message import ModelMessage, Role


class ModelConversation:
    def __init__(
        self,
        model_path: str,
        single_message_mode: bool = False,
    ):
        self.messages: List[ModelMessage] = []
        self.single_message_mode: bool = single_message_mode
        # self.tool_manager: ToolManager = ToolManager()
        # self.memory_manager: MemoryManager = memory_manager
        self.model_path: str = model_path

    def get_model_path(self) -> str:
        return self.model_path

    def set_model_path(self, new_model_path: str):
        self.model_path = new_model_path

    def get_messages(self, single_message_mode: bool = False) -> List[ModelMessage]:
        if not self.messages:
            return []

        if single_message_mode:
            messages: List[ModelMessage] = []
            system_message = None
            for message in self.messages:
                if message.is_system_message():
                    system_message = message

            if system_message:
                messages.append(system_message)

            if len(self.messages) > 0 and not system_message == self.messages[-1]:
                messages.append(self.messages[-1])

            return messages

        return self.messages[::]

    def add_user_message(self, content: str) -> None:
        self.messages.append(ModelMessage(Role.USER, content, datetime.datetime.now()))

    def add_assistant_message(self, content: str) -> None:
        self.messages.append(
            ModelMessage(Role.ASSISTANT, content, datetime.datetime.now())
        )

    def add_system_message(self, content: str) -> None:
        self.messages.append(
            ModelMessage(Role.SYSTEM, content, datetime.datetime.now())
        )

    def generate_message(
        self,
        model: ApiModel,
        max_tokens: int,
        single_message_mode: bool,
        use_metadata: bool = False,
        use_tools: bool = False,
        use_reflections: bool = False,
        use_knowledge: bool = False,
        ask_permission_to_run_tools: bool = False,
        response_prefix: str = "",
    ) -> str:
        messages = self.get_messages(single_message_mode)

        response = model.generate_text(
            messages,
            max_tokens,
            use_metadata=use_metadata,
            response_prefix=response_prefix,
        )

        self.add_assistant_message(response.get_text())

        return response.get_text()
