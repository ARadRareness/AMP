import gradio as gr

# import gradio_interface_greeting
from web_management import (
    gradio_interface_conversation,
    gradio_interface_greeting,
    gradio_interface_model,
    gradio_interface_chat,
)

amp_manager = None


def run_gradio(port=5005, amp_manager=None):
    global iface

    gradio_interface_chat.set_amp_manager(amp_manager)
    gradio_interface_conversation.set_amp_manager(amp_manager)
    gradio_interface_model.set_amp_manager(amp_manager)

    iface.launch(server_name="0.0.0.0", server_port=port, share=False)


def shutdown_gradio():
    if hasattr(gr, "close_all"):
        gr.close_all()


# Create a tabbed interface
with gr.Blocks() as iface:
    gr.Markdown("# Main Interface")

    with gr.Tabs():

        with gr.Tab("Greeting"):
            greeting_iface = gradio_interface_greeting.create_interface()

        with gr.Tab("Chat"):
            chat_iface = gradio_interface_chat.create_interface()

        with gr.Tab("Conversations"):
            conversation_iface = gradio_interface_conversation.create_interface()

        with gr.Tab("Model"):
            model_iface = gradio_interface_model.create_interface()
