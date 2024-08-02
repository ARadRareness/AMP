import os
import sys
import traceback
from typing import Dict, Tuple
from language_models.model_conversation import ModelConversation
from language_models.providers.llamacpp.llamacpp_manager import LlamaCppManager


class AmpManager:
    def __init__(self):
        self.state = {}
        self.llamacpp_manager: LlamaCppManager = self.initialize_llamacpp()
        self.gradio_port = 8080
        self.gradio_html_iframe = self.initialize_gradio_html()
        self.conversations: Dict[str, ModelConversation] = {}

    def get_available_models(self):
        return True, self.llamacpp_manager.get_available_models()

    def get_default_model(self):
        if not self.llamacpp_manager.get_available_models():
            raise ValueError("No models available.")
        return self.llamacpp_manager.get_available_models()[0]

    def add_system_message(self, data):
        return self.add_message(data, "system")

    def add_user_message(self, data):
        return self.add_message(data, "user")

    def add_assistant_message(self, data):
        return self.add_message(data, "assistant")

    def add_message(self, data, role):
        try:
            conversation_id: str = data.get("conversation_id")
            message: str = data.get("message")

            conversation_id, message = self.validate_conversation_id_and_message(
                conversation_id, message
            )

            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = ModelConversation(
                    self.get_default_model()
                )

            if role == "user":
                self.conversations[conversation_id].add_user_message(message)
            elif role == "assistant":
                self.conversations[conversation_id].add_assistant_message(message)
            elif role == "system":
                self.conversations[conversation_id].add_system_message(message)

            return True, ""

        except Exception as e:
            traceback.print_exc()
            return False, str(e)

    def generate_response(self, data):
        try:
            conversation_id = data.get("conversation_id")
            user_message = data.get("message")
            max_tokens = data.get("max_tokens")
            single_message_mode = data.get("single_message_mode")
            response_prefix = data.get("response_prefix", "")

            conversation_id, user_message = self.validate_conversation_id_and_message(
                conversation_id, user_message
            )

            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = ModelConversation(
                    self.get_default_model()
                )

            self.conversations[conversation_id].add_user_message(user_message)

            model_path = self.conversations[conversation_id].get_model_path()

            self.llamacpp_manager.change_model(model_path)  # TODO: Improve this

            response = self.conversations[conversation_id].generate_message(
                self.llamacpp_manager.active_models[0],
                max_tokens,
                single_message_mode,
                use_metadata=True,
                use_tools=False,
                use_reflections=False,
                use_knowledge=False,
                ask_permission_to_run_tools=False,
                response_prefix=response_prefix,
            )
            return True, response

        except Exception as e:
            traceback.print_exc()
            return False, str(e)

    def get_model_info(self, conversation_id):
        try:

            conversation_id = self.validate_conversation_id(conversation_id)

            if conversation_id not in self.conversations:
                model_path = self.get_default_model()

                if not model_path:
                    raise ValueError("No model available.")
                self.conversations[conversation_id] = ModelConversation(model_path)

            model_path = self.conversations[conversation_id].get_model_path()

            return True, {"path": model_path}

        except Exception as e:
            traceback.print_exc()
            return False, str(e)

    def initialize_gradio_html(self):
        return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gradio Interface</title>
        <style>
            body, html { margin: 0; padding: 0; height: 100%; overflow: hidden; }
            iframe { width: 100%; height: 100%; border: none; }
        </style>
    </head>
    <body>
        <iframe src="http://localhost:{gradio_port}"></iframe>
    </body>
    </html>
    """.replace(
            "{gradio_port}", str(self.gradio_port)
        )

    def initialize_llamacpp(self):
        binary_path = ""
        llama_cpp_path = "bin"
        for variants in ["llama-server", "server"]:
            if os.name == "nt":
                binary_path = os.path.join(llama_cpp_path, variants + ".exe")
            else:
                binary_path = os.path.join(llama_cpp_path, variants)
            if os.path.exists(binary_path):
                break

        if not os.path.exists(binary_path):
            print(
                "Error:",
                f"Add the llama.cpp server binary and (for Windows) llama.dll into the {llama_cpp_path} folder. See https://github.com/ggerganov/llama.cpp.",
            )
            sys.exit(-1)

        start_port = 8000
        return LlamaCppManager(binary_path, start_port)

    def validate_conversation_id_and_message(
        self, conversation_id, message
    ) -> Tuple[str, str]:
        return self.validate_conversation_id(conversation_id), self.validate_message(
            message
        )

    def validate_conversation_id(self, conversation_id) -> str:
        if not conversation_id:
            raise ValueError("Missing conversation_id in the request.")

        if not isinstance(conversation_id, str):
            raise ValueError("conversation_id must be a string.")

        return conversation_id

    def validate_message(self, message) -> str:
        if not message:
            raise ValueError("Missing message in the request.")

        if not isinstance(message, str):
            raise ValueError("message must be a string.")

        return message
