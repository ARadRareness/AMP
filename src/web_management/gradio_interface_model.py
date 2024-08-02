import gradio as gr
from amp_manager import AmpManager

amp_manager = None


def set_amp_manager(amp_manager_instance):
    global amp_manager
    amp_manager = amp_manager_instance


def get_current_model_name():
    if amp_manager:
        return (
            amp_manager.llamacpp_manager.active_models[0].get_model_path()
            if amp_manager.llamacpp_manager.active_models
            else "No model loaded"
        )
    return "No model loaded"


def create_interface():
    with gr.Blocks() as iface:
        gr.Markdown("# Conversation Viewer")

        current_model = gr.Textbox(
            label="Current Model",
            value=lambda: get_current_model_name(),
            interactive=False,
        )

        unload_button = gr.Button("Unload Model")
        unload_button.click(fn=unload_model, inputs=[], outputs=[current_model])

        timer_available_conversations = gr.Timer(value=5)
        timer_available_conversations.tick(
            fn=get_current_model_name,
            inputs=[],
            outputs=[current_model],
        )

        # iface.load(fn=initialize_conversations, outputs=[conversation_dropdown])

    return iface


def unload_model():
    if amp_manager.llamacpp_manager.active_models:
        amp_manager.llamacpp_manager.unload_model()
    return "No model loaded"
