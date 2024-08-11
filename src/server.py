import struct
import traceback
from flask import Flask, Response, jsonify, render_template_string, request
import threading
import signal
from amp_manager.amp_manager import AmpManager
from web_management.gradio_interface_greeting import (
    get_current_name,
)

from web_management.gradio_interface import (
    run_gradio,
    shutdown_gradio,
)

import os

os.environ["KMP_DUPLICATE_LIB_OK"] = (
    "TRUE"  # Fix for OMP: Error #15: Initializing libiomp5md.dll, but found libomp140.x86_64.dll already initialized.
)

ampManager = AmpManager()

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
        data = request.get_json()
        text = data.get("text")

        if not text:
            raise ValueError("Missing 'text' in the request.")

        wav_file_paths = ampManager.text_to_speech_with_split(text)

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


if __name__ == "__main__":

    # Start Gradio in a separate daemon thread
    gradio_thread = threading.Thread(
        target=run_gradio, args=(ampManager.gradio_port, ampManager), daemon=True
    )
    gradio_thread.start()

    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("Shutting down...")
        shutdown_gradio()
        exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    # Run Flask app
    app.run(debug=False, host="0.0.0.0", port=17173)
