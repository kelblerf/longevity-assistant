from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models import ChatMessage, Conversation
from app.services.storage_service import read_json, write_json

_conversations: dict[str, Conversation] = {}
_messages: dict[str, list[ChatMessage]] = {}
_loaded = False


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _save_state() -> None:
    write_json(
        "conversations.json",
        {
            "conversations": [item.model_dump(by_alias=True) for item in _conversations.values()],
            "messages": {
                conversation_id: [message.model_dump(by_alias=True) for message in messages]
                for conversation_id, messages in _messages.items()
            },
        },
    )


def _load_state() -> None:
    global _loaded
    if _loaded:
        return

    payload = read_json("conversations.json", default={"conversations": [], "messages": {}})
    for conversation_payload in payload.get("conversations", []):
        conversation = Conversation.model_validate(conversation_payload)
        _conversations[conversation.id] = conversation
    for conversation_id, messages_payload in payload.get("messages", {}).items():
        _messages[conversation_id] = [
            ChatMessage.model_validate(message_payload) for message_payload in messages_payload
        ]
    _loaded = True


def list_conversations() -> list[Conversation]:
    _load_state()
    return sorted(_conversations.values(), key=lambda item: item.updated_at, reverse=True)


def create_conversation(title: str | None = None) -> Conversation:
    _load_state()
    conversation = Conversation(
        id=f"conv-{uuid4().hex[:12]}",
        title=title or "Nova konverzace",
        createdAt=_now_iso(),
        updatedAt=_now_iso(),
    )
    _conversations[conversation.id] = conversation
    _messages[conversation.id] = []
    _save_state()
    return conversation


def get_conversation(conversation_id: str) -> Conversation:
    _load_state()
    if conversation_id not in _conversations:
        return create_conversation("Rychla konverzace")
    return _conversations[conversation_id]


def list_messages(conversation_id: str) -> list[ChatMessage]:
    _load_state()
    conversation = get_conversation(conversation_id)
    return list(_messages.get(conversation.id, []))


def add_message(conversation_id: str, role: str, content: str) -> ChatMessage:
    _load_state()
    conversation = get_conversation(conversation_id)
    message = ChatMessage(
        id=f"msg-{uuid4().hex[:12]}",
        conversationId=conversation.id,
        role=role,
        content=content,
        createdAt=_now_iso(),
    )
    _messages.setdefault(conversation.id, []).append(message)
    refreshed = conversation.model_copy(update={"updated_at": _now_iso()})
    _conversations[conversation.id] = refreshed
    _save_state()
    return message
