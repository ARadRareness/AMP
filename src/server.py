from flask import Flask, Response, jsonify, render_template_string, request
import threading
import signal
from amp_manager import AmpManager
from web_management.gradio_interface import (
    run_gradio,
    get_current_name,
    shutdown_gradio,
)

ampManager = AmpManager()

app = Flask(__name__)


@app.route("/greet")
def greet():
    return f"Hello, {get_current_name()}!"


@app.route("/manage")
def manage():
    return render_template_string(ampManager.gradio_html_iframe)


@app.route("/add_system_message", methods=["POST"])
def add_system_message() -> Response:
    result, response = ampManager.add_system_message(request.get_json())
    return jsonify({"result": result, "response": response})


@app.route("/get_available_models", methods=["GET"])
def get_available_models():
    return ampManager.get_available_models()


@app.route("/get_model_info", methods=["GET"])
def get_model_info():
    conversation_id = request.args.get("conversation_id")
    result, response = ampManager.get_model_info(conversation_id)
    return jsonify({"result": result, "info": response})


@app.route("/generate_response", methods=["POST"])
def generate_response() -> Response:
    result, response = ampManager.generate_response(request.get_json())
    return jsonify({"result": result, "response": response})


if __name__ == "__main__":

    # Start Gradio in a separate daemon thread
    gradio_thread = threading.Thread(
        target=run_gradio, args=(ampManager.gradio_port,), daemon=True
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
