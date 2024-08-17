# First, in your terminal.
#
# $ python3 -m virtualenv env
# $ source env/bin/activate
# $ pip install torch torchvision transformers sentencepiece protobuf accelerate
# $ pip install git+https://github.com/huggingface/diffusers.git
# $ pip install optimum-quanto

import torch
import os


# Check if CUDA (GPU support) is available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# Optionally, you can print more details about the GPU if available
if torch.cuda.is_available():
    print(f"GPU Name: {torch.cuda.get_device_name(0)}")
    print(f"Number of GPUs available: {torch.cuda.device_count()}")


from optimum.quanto import freeze, qfloat8, quantize

from diffusers import FlowMatchEulerDiscreteScheduler, AutoencoderKL
from diffusers.models.transformers.transformer_flux import FluxTransformer2DModel
from diffusers.pipelines.flux.pipeline_flux import FluxPipeline
from transformers import CLIPTextModel, CLIPTokenizer, T5EncoderModel, T5TokenizerFast

dtype = torch.bfloat16

# schnell is the distilled turbo model. For the CFG distilled model, use:
# bfl_repo = "black-forest-labs/FLUX.1-dev"
# revision = "refs/pr/3"
#
# The undistilled model that uses CFG ("pro") which can use negative prompts
# was not released.
bfl_repo = "black-forest-labs/FLUX.1-schnell"
revision = "refs/pr/1"

quantize_int4 = True


def quantize_freeze_and_save_models(bfl_repo, revision, dtype):
    transformer = FluxTransformer2DModel.from_pretrained(
        bfl_repo, subfolder="transformer", torch_dtype=dtype, revision=revision
    ).to(device)
    text_encoder_2 = T5EncoderModel.from_pretrained(
        bfl_repo, subfolder="text_encoder_2", torch_dtype=dtype, revision=revision
    ).to(device)

    from optimum.quanto import qint4

    if quantize_int4:
        quantize(
            transformer,
            weights=qint4,
            exclude=["proj_out", "x_embedder", "norm_out", "context_embedder"],
        )
    else:
        quantize(transformer, weights=qfloat8)

    freeze(transformer)
    if quantize_int4:
        quantize(text_encoder_2, weights=qint4)
    else:
        quantize(text_encoder_2, weights=qfloat8)
    freeze(text_encoder_2)

    # Create the "models" folder if it doesn't exist
    script_dir = os.path.dirname(os.path.abspath(__file__))
    models_dir = os.path.join(os.path.dirname(script_dir), "models")
    os.makedirs(models_dir, exist_ok=True)
    print(f"Models will be saved in: {models_dir}")

    # Save the models in the "models" folder
    torch.save(transformer, os.path.join(models_dir, "FLUX.1-schnell.pth"))
    torch.save(
        text_encoder_2, os.path.join(models_dir, "FLUX.1-schnell_text_encoder.pth")
    )


if __name__ == "__main__":
    quantize_freeze_and_save_models(bfl_repo, revision, dtype)
