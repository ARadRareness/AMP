 python setup.py sdist bdist_wheel

 pip install dist/amp_lib-0.1.0-py3-none-any.whl

    pip install twine
   twine upload dist/*

# AMP Library

AMP Library is a Python package that provides a client for interacting with the AMP Server. It offers various AI and media processing services through a unified interface.

## Installation

### From source

To build and install the package from source:

1. Clone the repository
2. Navigate to the project directory
3. Build the package:
   ```bash
   python setup.py sdist bdist_wheel
   ```
4. Install the package:
   ```bash
   pip install dist/amp_lib-0.1.0-py3-none-any.whl
   ```

## Purpose

The primary purpose of the AMP Library is to serve as a client for the AMP Server. It provides a convenient and unified way to access various AI and media processing services offered by the server, including conversation management, text generation, speech processing, and image generation.

## Usage

The main class in this library is `AmpClient`. Here's a quick overview of its capabilities:

### Initialize the client
client = AmpClient(base_url="http://localhost:17173")

### Conversation management
client.add_system_message(conversation_id, message)

client.add_user_message(conversation_id, message)

client.add_assistant_message(conversation_id, message)

### Model information
client.get_available_models()

client.get_model_info(conversation_id)

### Text generation
client.generate_response(conversation_id, message, max_tokens, single_message_mode, response_prefix)

### Speech processing
client.speech_to_text(audio_file_path)

client.text_to_speech(text, clone_audio_file_path)

### Image generation
client.generate_image(prompt, width, height, seed)

### Messaging
client.send_telegram_message(message)