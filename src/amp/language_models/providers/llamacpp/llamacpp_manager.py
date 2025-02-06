import atexit
import os
import subprocess
from typing import List
import logging

from amp.language_models.api_model import ApiModel
from amp.language_models.prompt_formatter import PromptFormatter
from amp.language_models.providers.llamacpp.formatters.aya import AyaFormatter
from amp.language_models.providers.llamacpp.formatters.deepseek_r1 import (
    DeepseekR1Formatter,
)
from amp.language_models.providers.llamacpp.formatters.gemma import GemmaFormatter
from amp.language_models.providers.llamacpp.formatters.llama3 import Llama3Formatter
from amp.language_models.providers.llamacpp.formatters.mistral import MistralFormatter
from amp.language_models.providers.llamacpp.formatters.phi import PhiFormatter
from amp.language_models.providers.llamacpp.formatters.glm import GLMFormatter
from amp.language_models.providers.llamacpp.formatters.phi4 import Phi4Formatter
from amp.language_models.providers.llamacpp.llamacpp_model import LlamaCppModel


logger = logging.getLogger(__name__)


class LlamaCppManager:
    def __init__(self, llama_cpp_path: str, start_port: int):
        self.llama_cpp_path = llama_cpp_path
        self.start_port = start_port
        self.popen = None
        self.active_models: List[ApiModel] = []
        atexit.register(self.cleanup)

    def model_is_loaded(self) -> bool:
        return self.popen != None

    def load_model(
        self, model_index: int = -1, gpu_layers: int = -1, context_window_size: int = -1
    ) -> None:
        try:
            logger.debug("Starting model load process")
            if model_index == -1:
                last_model_used = os.getenv("MODEL.LAST_USED", "")
                available_models = self.get_available_models()
                try:
                    model_index = available_models.index(last_model_used)
                except ValueError:
                    model_index = (
                        0  # Default to the first model if last_model_used is not found
                    )

            if self.popen:
                # Terminate the existing process
                self.popen.terminate()
                self.popen = None
                if self.active_models:
                    self.active_models.pop()

            available_models = self.get_available_models()

            model_identifier = available_models[model_index]

            print("STARTING MODEL LOAD")
            # Load a local model
            model_path = os.path.join("models", model_identifier)
            # print("PROMPT FORMAT:", self.read_prompt_format(model_path))

            print(self.llama_cpp_path)

            if gpu_layers == -1:
                gpu_layers = int(os.getenv("LLAMACPP.GPU_LAYERS", 9001))

            if context_window_size == -1:
                context_window_size = int(
                    os.getenv("LLAMACPP.CONTEXT_WINDOW_SIZE", 8192)
                )

            repeat_penalty = os.getenv("LLAMACPP.REPEAT_PENALTY", 1.1)

            # Start a new child process with the llama cpp path and the model path as arguments
            self.popen = subprocess.Popen(
                [
                    self.llama_cpp_path,
                    "--n-gpu-layers",
                    str(gpu_layers),
                    "--ctx-size",
                    str(context_window_size),
                    "--port",
                    str(self.start_port),
                    "-m",
                    model_path,
                    "--repeat-penalty",
                    str(repeat_penalty),
                    "--predict",
                    "-2",  # Only predict up to context window size
                    "-fa",  # FLASH ATTENTION
                    "--no-perf",  # No performance metrics
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            while True:
                if self.popen and self.popen.stdout:
                    try:
                        line = self.popen.stdout.buffer.readline().decode(
                            "utf-8", errors="ignore"
                        )
                        print(line, end="")

                        if "all slots are idle" in line:
                            break

                    except Exception as e:
                        print("EXCEPTION:", e)
                        break

                else:
                    return

            # Close the stdout pipe after the while loop to allow normal process output
            if self.popen and self.popen.stdout:
                self.popen.stdout.close()

            prompt_formatter = self.get_prompt_formatter(model_identifier)
            self.active_models.append(
                LlamaCppModel(
                    "127.0.0.1",
                    str(self.start_port),
                    prompt_formatter,
                    model_identifier,
                    context_window_size,
                )
            )
            logger.debug("Model loaded successfully")
        except Exception as e:
            logger.exception("Exception during load_model")
            raise

    def unload_model(self) -> None:
        if self.popen:
            logger.debug("Terminating llama.cpp subprocess")
            self.popen.terminate()
            self.popen = None
        if self.active_models:
            logger.debug("Clearing active models")
            self.active_models.clear()

    def read_prompt_format(self, model_path: str) -> str:
        from gguf import GGUFReader

        reader = GGUFReader(model_path, "r+")

        if "tokenizer.chat_template" in reader.fields:
            jinja_template = "".join(
                [chr(c) for c in reader.fields["tokenizer.chat_template"].parts[4]]
            )
            return jinja_template
        else:
            print("No chat template found.")
            return ""

    def get_prompt_formatter(self, model_path: str) -> PromptFormatter:
        # Create an environment variable name based on the model_path
        env_var_name = f"MODEL_FILE_{model_path.replace(' ', '_').replace('-', '_').replace('.', '_')}"
        print("ENV VAR NAME:", env_var_name)

        # Check if the environment variable exists
        custom_formatter = os.getenv(env_var_name)
        print("CUSTOM FORMATTER:", custom_formatter)

        # If no custom formatter is found, use the existing logic
        if custom_formatter == "LLAMA" or "llama-3" in model_path.lower():
            return Llama3Formatter()
        elif (
            custom_formatter == "MISTRAL"
            or "mistral" in model_path.lower()
            or "magnum" in model_path.lower()
            or "ministral" in model_path.lower()
        ):
            return MistralFormatter()
        elif custom_formatter == "GEMMA" or "gemma" in model_path.lower():
            return GemmaFormatter()
        elif custom_formatter == "PHI" or "phi-3" in model_path.lower():
            return PhiFormatter()
        elif custom_formatter == "PHI-4" or "phi_4" in model_path.lower():
            return Phi4Formatter()
        elif custom_formatter == "GLM" or "glm" in model_path.lower():
            return GLMFormatter()
        elif custom_formatter == "AYA" or "aya" in model_path.lower():
            return AyaFormatter()
        elif custom_formatter == "DEEPSEEK-R1" or "deepseekr1" in model_path.lower():
            return DeepseekR1Formatter()
        else:
            return PromptFormatter()

    def change_model(
        self, model_path: str, gpu_layers: int = -1, context_window_size: int = -1
    ) -> None:
        for model in self.active_models:
            if model.get_model_path() == model_path:
                if model.context_window_size > context_window_size:
                    return
                else:
                    print("RIGHT MODEL BUT TOO SMALL CONTEXT WINDOW")

        model_index = self.get_available_models().index(model_path)

        if model_index == -1:
            print(f"Error: Model {model_path} not found.")
            return

        self.load_model(model_index, gpu_layers, context_window_size)

    def get_available_models(self) -> List[str]:
        models = list(filter(lambda f: f.endswith(".gguf"), os.listdir("models")))
        return models

    def __del__(self) -> None:
        # Terminate the process if it is still running
        if self.popen:
            self.popen.kill()
            self.popen = None

    def cleanup(self):
        logger.info("Cleaning up LlamaCppManager")
        self.unload_model()
