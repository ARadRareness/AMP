import openai

# Set the API base to your server's address

import os
from openai import OpenAI

client = OpenAI(
    # This is the default and can be omitted
    api_key="test",
    base_url="http://localhost:17173",
)


def simple_chat(client):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are an assistant that always lies.",
            },
            {
                "role": "user",
                "content": "What's the capital of Sweden?",
            },
            {
                "role": "assistant",
                "content": "Is it norway?",
            },
            {
                "role": "user",
                "content": "That must be right!",
            },
            {
                "role": "assistant",
                "content": "I'm happy to help!",
            },
            {
                "role": "user",
                "content": "Yes, thank you!",
            },
        ],
        model="random_model",
    )

    print(chat_completion.choices[0].message.content)


def stream_chat(client):
    stream = client.chat.completions.create(
        model="mock-gpt-model",
        messages=[{"role": "user", "content": "What's the capital of Sweden?"}],
        stream=True,
    )

    for chunk in stream:
        print(chunk.choices[0].delta.content or "")


if __name__ == "__main__":
    simple_chat(client)
    # stream_chat(client)
