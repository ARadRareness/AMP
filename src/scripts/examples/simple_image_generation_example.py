import os
import sys

# Hack to add the 'src' directory to the Python path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from amp_lib.amp_lib import AmpClient


def save_generated_image(
    prompt, width=1024, height=1024, seed=None, save_path="generated_images"
):
    # Ensure the save directory exists
    os.makedirs(save_path, exist_ok=True)

    client = AmpClient()
    image = client.generate_image(prompt, width, height, seed)

    if image:
        # Generate a filename based on the prompt
        filename = f"{prompt[:30].replace(' ', '_')}.png"
        full_path = os.path.join(save_path, filename)

        # Save the image
        image.save(full_path)
        print(f"Image saved successfully: {full_path}")
        return full_path
    else:
        print("FAILED TO GENERATE IMAGE")
        return None


if __name__ == "__main__":
    save_generated_image(
        "A realistic image of a sleeping cat",
        width=1024,
        height=1024,
    )
