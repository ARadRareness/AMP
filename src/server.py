import struct
import traceback
from flask import Flask, Response, jsonify, render_template_string, request
import threading
import signal
import shutil
from dotenv import load_dotenv
from amp_manager.amp_manager import AmpManager
from messaging.telegram_manager import TelegramManager
from web_management.gradio_interface_greeting import (
    get_current_name,
)

from web_management.gradio_interface import (
    run_gradio,
    shutdown_gradio,
)

import os
import base64
from io import BytesIO


os.environ["KMP_DUPLICATE_LIB_OK"] = (
    "TRUE"  # Fix for OMP: Error #15: Initializing libiomp5md.dll, but found libomp140.x86_64.dll already initialized.
)

if not os.path.exists(".env"):
    shutil.copy(".env_defaults", ".env")

load_dotenv()

ampManager = AmpManager()
telegramManager = TelegramManager(ampManager)

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
    return jsonify({"result": result, "response": response})


@app.route("/add_user_message", methods=["POST"])
def add_user_message() -> Response:
    result, response = ampManager.add_user_message(request.get_json())
    return jsonify({"result": result, "response": response})


@app.route("/add_assistant_message", methods=["POST"])
def add_assistant_message() -> Response:
    result, response = ampManager.add_assistant_message(request.get_json())
    return jsonify({"result": result, "response": response})


@app.route("/get_available_models", methods=["GET"])
def get_available_models():
    result, response = ampManager.get_available_models()
    return jsonify({"result": result, "response": response})


@app.route("/get_model_info", methods=["GET"])
def get_model_info():
    conversation_id = request.args.get("conversation_id")
    result, response = ampManager.get_model_info(conversation_id)
    return jsonify({"result": result, "info": response})


@app.route("/generate_response", methods=["POST"])
def generate_response() -> Response:
    result, response = ampManager.generate_response(request.get_json())
    return jsonify({"result": result, "response": response})


@app.route("/stt", methods=["POST"])
def speech_to_text():
    result, response = ampManager.speech_to_text(request)
    print(result, response)
    return jsonify({"result": result, **response})


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
        return jsonify({"result": False, "error_message": str(e)})


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
            return jsonify({"result": False, "error_message": result})

        buffered = BytesIO()
        result.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return jsonify({"result": True, "image": img_str})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"result": False, "error_message": str(e)})


@app.route("/telegram_message", methods=["POST"])
def send_telegram_message() -> Response:
    try:
        data = request.get_json()
        message = data.get("message")

        if not message:
            return jsonify(
                {"result": False, "error_message": "Missing 'message' in the request."}
            )

        success = telegramManager.send_message(message)

        if success:
            return jsonify({"result": True, "response": "Message sent successfully"})
        else:
            return jsonify({"result": False, "error_message": "Failed to send message"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"result": False, "error_message": str(e)})


if __name__ == "__main__":

    # Start TelegramManager thread
    telegramManager.start_thread()

    # Start Gradio in a separate daemon thread
    gradio_thread = threading.Thread(
        target=run_gradio, args=(ampManager.gradio_port, ampManager), daemon=True
    )
    gradio_thread.start()

    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("Shutting down...")
        shutdown_gradio()
        telegramManager.end_thread()
        print("Shutdown complete")
        os._exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Run Flask app
    app.run(debug=False, host="0.0.0.0", port=17173)
