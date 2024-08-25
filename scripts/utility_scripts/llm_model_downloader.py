import os
from huggingface_hub import hf_hub_download

repo_id = "bartowski/Meta-Llama-3.1-8B-Instruct-GGUF"
filename = "Meta-Llama-3.1-8B-Instruct-Q4_K_L.gguf"

print(f"Downloading model from {repo_id} with name {filename}")

# Allow the models directory to be a few levels up from the current directory
model_dir_paths = [
    "models",
    os.path.join("..", "models"),
    os.path.join("..", "..", "models"),
]

for model_dir_path in model_dir_paths:
    if os.path.exists(model_dir_path):
        model_path = os.path.join(model_dir_path, filename)
        if not os.path.exists(model_path):
            downloaded_model_path = hf_hub_download(  # type: ignore
                repo_id=repo_id,
                filename=filename,
            )

            # Move the downloaded model to the models folder
            os.rename(downloaded_model_path, model_path)
        break
