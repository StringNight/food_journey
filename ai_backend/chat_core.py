from typing import Generator
from ollama import Client, Message


class ChatInput:
    messages: list
    max_tokens: int
    model: str

    def __init__(self, messages: list, max_tokens: int, model: str):
        self.messages = messages
        self.max_tokens = max_tokens
        self.model = model


class ChatOutput:
    success: bool
    response: Message

    def __init__(self, success: bool, response: Message):
        self.success = success
        self.response = response


def chat_llm(input: ChatInput) -> ChatOutput:
    if len(input.messages) == 0 or len(input.messages) > input.max_tokens:
        return ChatOutput(success=False, response=Message(role="assistant", content=""))

    client = Client(host="http://localhost:11434", headers={"Content-Type": "application/json"})

    response = client.chat(
        model=f"{input.model}",
        messages=input.messages,
        stream=False,
    )

    return ChatOutput(success=True, response=response["message"])


def chat_llm_stream(input: ChatInput) -> Generator:
    if len(input.messages) == 0 or len(input.messages) > input.max_tokens:
        return ChatOutput(success=False, response=Message(role="assistant", content=""))

    client = Client(host="http://localhost:11434", headers={"Content-Type": "application/json"})

    response = client.chat(
        model=f"{input.model}",
        messages=input.messages,
        stream=True,
    )

    return response
