"""Abstract Port for Messaging and Notification providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass(frozen=True)
class MessageDispatchResult:
    is_delivered: bool
    channel: Literal["WHATSAPP", "SMS", "EMAIL"]
    message_id: Optional[str] = None
    error_message: Optional[str] = None


class MessagingPort(ABC):
    """
    Abstract Messaging Interface for customer notifications.
    """

    @abstractmethod
    async def send_message(
        self,
        recipient_contact: str,
        channel: Literal["WHATSAPP", "SMS", "EMAIL"],
        message_body: str,
    ) -> MessageDispatchResult:
        """Dispatches customer communication."""
        pass
