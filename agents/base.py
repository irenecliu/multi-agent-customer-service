from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AgentMessage:
    sender: str
    recipient: str
    content: str
    intent: Optional[str] = None
    payload: Optional[Dict[str, Any]] = field(default_factory=dict)


class AgentLogger:
    def __init__(self) -> None:
        self.messages: List[AgentMessage] = []

    def record(self, message: AgentMessage) -> None:
        self.messages.append(message)

    def dump(self) -> List[AgentMessage]:
        return self.messages

    def print_log(self) -> None:
        for msg in self.messages:
            payload = f" | payload={msg.payload}" if msg.payload else ""
            print(f"[{msg.sender} -> {msg.recipient}] {msg.intent or ''} {msg.content}{payload}")


class Agent:
    def __init__(self, name: str, logger: AgentLogger) -> None:
        self.name = name
        self.logger = logger

    def send(self, recipient: str, content: str, intent: Optional[str] = None, payload: Optional[Dict[str, Any]] = None) -> AgentMessage:
        message = AgentMessage(sender=self.name, recipient=recipient, content=content, intent=intent, payload=payload or {})
        self.logger.record(message)
        return message

    def handle(self, message: AgentMessage) -> AgentMessage:
        raise NotImplementedError("Agents must implement handle()")
