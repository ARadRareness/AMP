from datetime import datetime
from enum import Enum
from typing import List, Optional, Sequence


class Role(Enum):
    SYSTEM = 1
    USER = 2
    ASSISTANT = 3


class ModelMessage:
    def __init__(
        self,
        role: Role,
        content: str,
        timestamp: datetime,
        actor_name: str = "default",
    ):
        self.role = role
        self.content = content
        self.timestamp = timestamp
        self.actor_name = actor_name

    def get_content(self) -> str:
        return self.content

    def get_message(self) -> str:
        return self.get_content()

    def get_role(self) -> str:
        return self.role.name.lower()

    def get_actor_name(self) -> str:
        return self.actor_name

    def is_system_message(self) -> bool:
        return self.role == Role.SYSTEM

    def is_user_message(self) -> bool:
        return self.role == Role.USER

    def is_assistant_message(self) -> bool:
        return self.role == Role.ASSISTANT

    def __str__(self) -> str:
        return f"{self.role.name.lower()}: {self.content}"

    def __repr__(self) -> str:
        return f"{self.role.name.lower()}: {self.content}"
