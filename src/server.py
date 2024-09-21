import struct
import traceback
import types
from flask import (
    Flask,
    Response,
    jsonify,
    render_template_string,
    request,
    stream_with_context,
)
import threading
import signal
import shutil
from dotenv import load_dotenv
from amp.amp_manager.amp_manager import AmpManager
from messaging.telegram_manager import TelegramManager
from web_management.gradio_interface_greeting import (
    get_current_name,
)

from web_management.gradio_interface import (
    run_gradio,
    shutdown_gradio,
)

import struct

import os
import base64
from io import BytesIO
import logging
from waitress import serve
import uuid  # Add this import at the top with other imports
import time
import json  # Add this import for JSON serialization

os.environ["KMP_DUPLICATE_LIB_OK"] = (
    "TRUE"  # Fix for OMP: Error #15: Initializing libiomp5md.dll, but found libomp140.x86_64.dll already initialized.
)

# Configure logging at the very beginning
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
    handlers=[logging.FileHandler("server.log")],  # , logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# Add test log
logger.info("Debug message")

if not os.path.exists(".env"):
    shutil.copy(".env_defaults", ".env")

load_dotenv()

ampManager = AmpManager()
telegramManager = TelegramManager()

app = Flask(__name__)


@app.route("/greet")
def greet():
    return f"Hello, {get_current_name()}!"


@app.route("/manage")
def manage():
    return render_template_string(ampManager.gradio_html_iframe)


@app.route("/icon.svg")
def serve_icon():
    return Response(ampManager.get_icon(), mimetype="image/svg+xml")


@app.route("/add_system_message", methods=["POST"])
def add_system_message() -> Response:
    result, response = ampManager.add_system_message(request.get_json())
    if not result:
        return jsonify({"error": response}), 400
    return Response(response, mimetype="text/plain")


@app.route("/add_user_message", methods=["POST"])
def add_user_message() -> Response:
    result, response = ampManager.add_user_message(request.get_json())
    if not result:
        return jsonify({"error": response}), 400
    return Response(response, mimetype="text/plain")


@app.route("/add_assistant_message", methods=["POST"])
def add_assistant_message() -> Response:
    result, response = ampManager.add_assistant_message(request.get_json())
    if not result:
        return jsonify({"error": response}), 400
    return Response(response, mimetype="text/plain")


@app.route("/get_available_models", methods=["GET"])
def get_available_models():
    result, response = ampManager.get_available_models()
    if not result:
        return jsonify({"error": response}), 400
    return jsonify(response)


@app.route("/get_model_info", methods=["POST"])
def get_model_info():
    data = request.get_json()
    conversation_id = data.get("conversation_id")
    result, response = ampManager.get_model_info(conversation_id)
    if not result:
        return jsonify({"error": response}), 400
    return jsonify(response)


MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10 MB


@app.route("/generate_response", methods=["POST"])
def generate_response() -> Response:
    logger.debug("Received /generate_response request")
    try:
        if request.content_length and request.content_length > MAX_REQUEST_SIZE:
            logger.warning("Request size exceeds maximum limit")
            return (
                jsonify({"error": "Request size too large"}),
                413,
            )  # Payload Too Large

        result, response = ampManager.generate_response(request.get_json())
        if not result:
            logger.error(f"Error in generate_response: {response}")
            return jsonify({"error": response}), 400
        logger.debug("generate_response successful")
        return Response(response, mimetype="text/plain")
    except Exception as e:
        logger.exception("Unhandled exception in /generate_response")
        return jsonify({"error": str(e)}), 500


@app.route("/stt", methods=["POST"])
def speech_to_text():
    try:
        logger.info("WHISPER: GENERATING SPEECH TO TEXT")
        result, response = ampManager.speech_to_text(request)
        logger.info("WHISPER: SPEECH TO TEXT GENERATED")

        if not result:
            logger.error(f"Speech to text error: {response}")
            return jsonify({"error": response}), 400
        return Response(response, mimetype="text/plain")
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/tts", methods=["POST"])
def tts() -> Response:
    try:
        data = request.form
        text = data.get("text")
        clone_audio = request.files.get("clone_audio")

        if not text:
            raise ValueError("Missing 'text' in the request.")

        clone_audio_data = clone_audio.read() if clone_audio else None

        wav_file_paths = ampManager.text_to_speech_with_split(text, clone_audio_data)

        def generate():
            for wav_file_path in wav_file_paths:
                with open(wav_file_path, "rb") as wav_file:
                    wav_data = wav_file.read()
                    # Prefix each WAV file with its size using a 4-byte integer
                    yield struct.pack("<I", len(wav_data))
                    yield wav_data

        return Response(generate(), mimetype="audio/wav")
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/generate_image", methods=["POST"])
def generate_image() -> Response:
    try:
        prompt = request.get_json().get("prompt")
        width = request.get_json().get("width", 1024)
        height = request.get_json().get("height", 1024)
        seed = request.get_json().get("seed", None)
        result_code, result = ampManager.generate_image(
            prompt, width, height, seed=seed
        )

        if not result_code:
            return jsonify({"error": result}), 400

        buffered = BytesIO()
        result.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return Response(img_str, mimetype="text/plain")
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/telegram_message", methods=["POST"])
def send_telegram_message():
    try:
        data = request.get_json()
        message = data.get("message")

        if not message:
            return jsonify({"error": "Missing 'message' in the request."}), 400

        success = telegramManager.send_message(message)

        if success:
            return Response("Message sent successfully", mimetype="text/plain")
        else:
            return jsonify({"error": "Failed to send message"}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/chat/completions", methods=["POST"])
def chat_completions():
    """
    OpenAI-compatible chat completions endpoint with streaming support.
    """
    try:
        data = request.get_json()
        success, response = ampManager.chat_completions(data)

        if not success:
            return jsonify({"error": response}), (
                400 if isinstance(response, str) else 500
            )

        if isinstance(
            response, types.GeneratorType
        ):  # Check if response is a generator
            return Response(response, mimetype="text/event-stream")

        return jsonify(response), 200

    except Exception as e:
        logger.exception("Error in /chat/completions endpoint")
        return jsonify({"error": str(e)}), 500


@app.route("/images/generations", methods=["POST"])
def images_generations():
    try:
        data = request.get_json()
        model = data.get("model", "dall-e-3")  # Default to DALL-E 3
        prompt = data.get("prompt")
        size = data.get("size", "1024x1024")  # Default size
        quality = data.get("quality", "standard")  # Default quality
        n = data.get("n", 1)  # Default to 1 image

        if not prompt:
            return jsonify({"error": "Missing 'prompt' in the request."}), 400

        width, height = map(int, size.split("x"))

        images = []
        for _ in range(n):
            result_code, result = ampManager.generate_image(prompt, width, height)

            if not result_code:
                return jsonify({"error": result}), 400

            buffered = BytesIO()
            result.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            images.append({"b64_json": img_str})

        response = {"created": int(time.time()), "data": images}

        return jsonify(response), 200
    except Exception as e:
        logger.exception("Error in /images/generations endpoint")
        return jsonify({"error": str(e)}), 500


@app.route("/audio/transcriptions", methods=["POST"])
def transcribe_audio():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        if file:
            result, response = ampManager.speech_to_text(request)

            if not result:
                return jsonify({"error": response}), 400

            return jsonify({"text": response})

        return jsonify({"error": "File processing failed"}), 500
    except Exception as e:
        logger.exception("Error in /audio/transcriptions endpoint")
        return jsonify({"error": str(e)}), 500


import struct


@app.route("/audio/speech", methods=["POST"])
def text_to_speech():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        model = data.get("model", "tts-1")
        voice = data.get("voice", "alloy")
        input_text = data.get("input")

        if not input_text:
            return jsonify({"error": "No input text provided"}), 400

        clone_audio_data = None

        print("The voice is:", voice)

        if len(voice) > 20:
            import base64

            clone_audio_data = base64.b64decode(voice)
            voice = None

        print("The input text is:", input_text)

        wav_file_paths = ampManager.text_to_speech_with_split(
            input_text, clone_audio_data
        )

        def generate():
            # TODO: Might be able to use proper streaming with
            # https://github.com/matatonic/openedai-speech/blob/main/speech.py
            # or similar solution
            total_audio_size = 0
            audio_data = []

            # First pass: collect all audio data and calculate total size
            for wav_file_path in wav_file_paths:
                with open(wav_file_path, "rb") as wav_file:
                    wav_file.seek(0, 2)  # Seek to end
                    file_size = wav_file.tell()
                    wav_file.seek(0)  # Reset to beginning
                    if total_audio_size == 0:
                        # For first file, keep header
                        audio_data.append(wav_file.read())
                        total_audio_size = file_size - 44  # Subtract header size
                    else:
                        # For subsequent files, skip header
                        wav_file.seek(44)
                        audio_data.append(wav_file.read())
                        total_audio_size += file_size - 44

            # Update header with total size
            header = bytearray(audio_data[0][:44])
            struct.pack_into(
                "<I", header, 4, total_audio_size + 36
            )  # Update RIFF chunk size
            struct.pack_into(
                "<I", header, 40, total_audio_size
            )  # Update data sub-chunk size

            # Yield updated header
            yield bytes(header)

            # Yield audio data
            for i, data in enumerate(audio_data):
                if i == 0:
                    yield data[44:]  # Skip original header for first file
                else:
                    yield data

        headers = {
            "Content-Type": "audio/wav",
        }
        return Response(generate(), headers=headers)

    except Exception as e:
        logger.exception("Error in /audio/speech endpoint")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    try:
        # Start Gradio in a separate daemon thread
        gradio_thread = threading.Thread(
            target=run_gradio, args=(ampManager.gradio_port, ampManager), daemon=True
        )
        gradio_thread.start()
        logger.debug("Gradio interface started")

        # Set up signal handler for graceful shutdown
        def signal_handler(sig, frame):
            logger.info("Shutting down...")
            shutdown_gradio()
            logger.info("Shutdown complete")
            os._exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        app.run(debug=False, host="0.0.0.0", port=17173)
        # Run Flask app using Waitress
        logger.info("Starting Flask server with Waitress")
        # serve(app, host="0.0.0.0", port=17173)
    except Exception as e:
        logger.exception(f"Unhandled exception in main: {str(e)}")
        traceback.print_exc()
