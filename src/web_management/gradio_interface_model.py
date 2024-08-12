import gradio as gr

from amp_manager.amp_manager import AmpManager

amp_manager = None


def set_amp_manager(amp_manager_instance: AmpManager):
    global amp_manager
    amp_manager = amp_manager_instance


def create_interface():
    with gr.Blocks() as iface:
        gr.Markdown("# Model information")

        create_llamacpp_interface()
        create_whisper_interface()
        create_xtts_interface()

        # iface.load(fn=initialize_conversations, outputs=[conversation_dropdown])

    return iface


def create_llamacpp_interface():
    current_llamacpp_model = gr.Textbox(
        label="Current llama.cpp Model",
        value=lambda: get_current_llamacpp_model_name(),
        interactive=False,
    )

    unload_llamacpp_model_button = gr.Button("Unload Model")
    unload_llamacpp_model_button.click(
        fn=unload_llamacpp_model, inputs=[], outputs=[current_llamacpp_model]
    )

    timer_update_llamacpp_model = gr.Timer(value=5)
    timer_update_llamacpp_model.tick(
        fn=get_current_llamacpp_model_name,
        inputs=[],
        outputs=[current_llamacpp_model],
    )

    return current_llamacpp_model


def create_whisper_interface():
    whisper_model_loaded = gr.Textbox(
        label="Whisper",
        value=lambda: get_is_whisper_model_loaded(),
        interactive=False,
    )

    unload_whisper_model_button = gr.Button("Unload Whisper Model")
    unload_whisper_model_button.click(
        fn=unload_whisper_model, inputs=[], outputs=[whisper_model_loaded]
    )

    timer_update_whisper_model = gr.Timer(value=5)
    timer_update_whisper_model.tick(
        fn=get_is_whisper_model_loaded,
        inputs=[],
        outputs=[whisper_model_loaded],
    )

    return whisper_model_loaded


def create_xtts_interface():
    xtts_model_loaded = gr.Textbox(
        label="XTTS",
        value=lambda: get_is_xtts_model_loaded(),
        interactive=False,
    )

    unload_xtts_model_button = gr.Button("Unload XTTS Model")
    unload_xtts_model_button.click(
        fn=unload_xtts_model, inputs=[], outputs=[xtts_model_loaded]
    )

    timer_update_xtts_model = gr.Timer(value=5)
    timer_update_xtts_model.tick(
        fn=get_is_xtts_model_loaded,
        inputs=[],
        outputs=[xtts_model_loaded],
    )

    return xtts_model_loaded


def get_current_llamacpp_model_name():
    if amp_manager:
        return (
            amp_manager.llamacpp_manager.active_models[0].get_model_path()
            if amp_manager.llamacpp_manager.active_models
            else "No model loaded"
        )
    return "No model loaded"


def unload_llamacpp_model():
    if amp_manager.llamacpp_manager.active_models:
        amp_manager.llamacpp_manager.unload_model()
    return "No model loaded"


def get_is_whisper_model_loaded():
    if amp_manager:
        return (
            "Loaded" if amp_manager.whisper_manager.model_is_loaded() else "Not loaded"
        )
    return "Not loaded"


def unload_whisper_model():
    if amp_manager.whisper_manager.model_is_loaded():
        amp_manager.whisper_manager.unload_model()
    return "Not loaded"


def get_is_xtts_model_loaded():
    if amp_manager:
        return "Loaded" if amp_manager.xtts_manager.model_is_loaded() else "Not loaded"
    return "Not loaded"


def unload_xtts_model():
    if amp_manager.xtts_manager.model_is_loaded():
        amp_manager.xtts_manager.unload_model()
    return "Not loaded"
