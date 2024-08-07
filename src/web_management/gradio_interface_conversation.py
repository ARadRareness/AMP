import gradio as gr

amp_manager = None


def update_conversation_content(conversation_id):
    if not conversation_id:
        return ""

    if not amp_manager or conversation_id not in amp_manager.conversations:
        return "Conversation not found."

    conversation = amp_manager.conversations[conversation_id]
    content = ""
    for message in conversation.get_messages():
        content += f"{message.get_role().upper()}: {message.get_content()}\n\n"
    return content


def refresh_conversations():
    if amp_manager:
        return gr.update(choices=list(amp_manager.conversations.keys()))
    return gr.update(choices=[])


def refresh_current_conversation(conversation_id):
    return update_conversation_content(conversation_id)


def set_amp_manager(amp_manager_instance):
    global amp_manager
    amp_manager = amp_manager_instance


def create_interface():

    with gr.Blocks() as iface:
        gr.Markdown("# Conversation Viewer")

        conversation_dropdown = gr.Dropdown(
            choices=[],  # Start with an empty list
            label="Select Conversation",
        )

        conversation_content = gr.TextArea(
            label="Conversation Content", interactive=False
        )

        # Add a timer to auto-refresh the conversation content
        conversation_dropdown.change(
            fn=update_conversation_content,
            inputs=[conversation_dropdown],
            outputs=[conversation_content],
        )

        # Add a new button for refreshing the current conversation
        refresh_current_button = gr.Button("Refresh Current Conversation")
        refresh_current_button.click(
            fn=refresh_current_conversation,
            inputs=[conversation_dropdown],
            outputs=[conversation_content],
        )

        # Update the text for the existing refresh button
        refresh_available_button = gr.Button("Refresh Available Conversations")
        refresh_available_button.click(
            fn=refresh_conversations,
            inputs=[],
            outputs=[conversation_dropdown],
        )

        timer_conversation = gr.Timer(value=5)
        timer_conversation.tick(
            fn=refresh_current_conversation,
            inputs=[conversation_dropdown],
            outputs=[conversation_content],
        )

        timer_available_conversations = gr.Timer(value=5)
        timer_available_conversations.tick(
            fn=refresh_conversations,
            inputs=[],
            outputs=[conversation_dropdown],
        )

        # Add this line at the end of the Blocks context
        iface.load(fn=refresh_conversations, outputs=[conversation_dropdown])

    return iface
