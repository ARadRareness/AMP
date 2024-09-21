import os
import random
import torch

from diffusers import FlowMatchEulerDiscreteScheduler, AutoencoderKL
from diffusers.pipelines.flux.pipeline_flux import FluxPipeline
from transformers import CLIPTextModel, CLIPTokenizer, T5TokenizerFast

# Check if CUDA (GPU support) is available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

dtype = torch.bfloat16
bfl_repo = "black-forest-labs/FLUX.1-schnell"
revision = "refs/pr/1"

model_path = os.path.join("models", "FLUX.1-schnell.pth")
text_encoder_path = os.path.join("models", "FLUX.1-schnell_text_encoder.pth")


class FluxManager:
    def __init__(self):
        self.model_pipe = None

    def load_model(self):
        if self.model_pipe is not None:
            return self.model_pipe

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found at {model_path}. Download file separately or run flux_model_downloader.py."
            )

        if not os.path.exists(text_encoder_path):
            raise FileNotFoundError(
                f"Text encoder file not found at {text_encoder_path}. Download file separately or run flux_model_downloader.py."
            )

        # Load models and create pipeline
        scheduler = FlowMatchEulerDiscreteScheduler.from_pretrained(
            bfl_repo, subfolder="scheduler", revision=revision
        )
        text_encoder = CLIPTextModel.from_pretrained(
            "openai/clip-vit-large-patch14", torch_dtype=dtype
        ).to(device)
        tokenizer = CLIPTokenizer.from_pretrained(
            "openai/clip-vit-large-patch14", torch_dtype=dtype
        )
        tokenizer_2 = T5TokenizerFast.from_pretrained(
            bfl_repo, subfolder="tokenizer_2", torch_dtype=dtype, revision=revision
        )
        vae = AutoencoderKL.from_pretrained(
            bfl_repo, subfolder="vae", torch_dtype=dtype, revision=revision
        ).to(device)

        transformer = torch.load(model_path).to(device)
        transformer.eval()

        text_encoder_2 = torch.load(text_encoder_path).to(device)
        text_encoder_2.eval()

        # Create pipeline
        self.model_pipe = FluxPipeline(
            scheduler=scheduler,
            text_encoder=text_encoder,
            tokenizer=tokenizer,
            text_encoder_2=None,
            tokenizer_2=tokenizer_2,
            vae=vae,
            transformer=None,
        ).to(device)

        self.model_pipe.text_encoder_2 = text_encoder_2
        self.model_pipe.transformer = transformer

    def generate_image(self, prompt, width, height, guidance_scale=None, seed=None):
        self.load_model()

        if self.model_pipe is None:
            raise RuntimeError("Image generation model not loaded.")

        # Generate image
        generator = torch.Generator(device=device)  # .manual_seed(123456)
        if seed is not None:
            generator.manual_seed(seed)
        else:
            generator.manual_seed(random.randint(0, 2**32 - 1))

        if guidance_scale is None:
            guidance_scale = 3.5

        image = self.model_pipe(
            prompt=prompt,
            width=width,
            height=height,
            num_inference_steps=4,
            generator=generator,
            guidance_scale=guidance_scale,
        ).images[0]

        return image

    def model_is_loaded(self):
        return self.model_pipe is not None

    def unload_model(self):
        if self.model_pipe is not None:
            del self.model_pipe
            self.model_pipe = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
