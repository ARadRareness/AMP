import gradio as gr

name = "ABC"


def update_name(new_name):
    global name
    name = new_name
    return f"Name updated to: {name}"


def get_current_name():
    global name
    return name


def shutdown_gradio():
    if hasattr(gr, "close_all"):
        gr.close_all()
    # Add any additional cleanup if necessary


def create_interface():
    # Create Gradio interface
    iface = gr.Interface(
        fn=update_name,
        inputs="text",
        outputs="text",
        title="Update Greeting Name",
        description="Enter a new name to be greeted",
    )
    return iface


def run_gradio(port=5005):
    iface.launch(server_name="0.0.0.0", server_port=port, share=False)
