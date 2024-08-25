from amp_lib import AmpClient


def main():
    client = AmpClient()

    conversation_id = "123"

    model_info = client.get_model_info(conversation_id)

    print("Current model:", model_info.get("path"))

    print("Available models:", client.get_available_models())

    client.add_system_message(
        conversation_id,
        "You are an AI that ends all your sentences with the word meep!",
    )

    client.add_user_message(conversation_id, "Hello, world!")
    client.add_assistant_message(conversation_id, "Hello, world back to you too meep!")

    response = client.generate_response(conversation_id, "How's it going?")
    print("Response from AI:", response)


if __name__ == "__main__":
    main()
