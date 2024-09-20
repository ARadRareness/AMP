import os
import cairosvg


def convert_svg_to_png(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.endswith(".svg"):
            svg_path = os.path.join(input_folder, filename)
            png_path = os.path.join(output_folder, filename[:-4] + ".png")
            cairosvg.svg2png(url=svg_path, write_to=png_path)
            print(f"Converted {filename} to PNG")


# Usage
input_folder = "C:\\Users\\gaste\\Downloads\\icons\\Clarity-master\\src\\mimetypes"
output_folder = "C:\\Users\\gaste\\Downloads\\icons\\Clarity-master\\src\\mimetypes"
convert_svg_to_png(input_folder, output_folder)
