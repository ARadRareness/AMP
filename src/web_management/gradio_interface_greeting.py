import gradio as gr

name = "ABC"


def update_name(new_name):
    global name
    name = new_name
    return f"Name updated to: {name}"


def get_current_name():
    global name
    return name


def create_interface():
    # Create Gradio interface with a static greeting
    iface = gr.Interface(
        fn=lambda: "Welcome to the AMP manager!",
        inputs=None,
        outputs=gr.Label(label=""),  # Use Label component with label=False
        title="",
        description="",
        live=True,  # Ensures the output is always shown
        allow_flagging="never",  # Disables the flag button
    )
    return iface
