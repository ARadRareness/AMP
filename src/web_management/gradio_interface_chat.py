import gradio as gr
import uuid

amp_manager = None


def update_conversation_content(conversation_id):
    if not conversation_id:
        return ""

    if not amp_manager or conversation_id not in amp_manager.conversations:
        return ""

    conversation = amp_manager.conversations[conversation_id]
    messages = conversation.get_messages()
    formatted_messages = []
    for i in range(0, len(messages), 2):
        user_message = messages[i].get_content() if i < len(messages) else None
        bot_message = messages[i + 1].get_content() if i + 1 < len(messages) else None
        if user_message is not None:
            formatted_messages.append(
                f"<div style='background-color: #F9FAFB; padding: 10px; border-radius: 10px; margin-bottom: 10px; display: block; width: fit-content; max-width: 80%;'>"
                f"User: {user_message}</div>"
            )
        if bot_message is not None:
            formatted_messages.append(
                f"<div style='background-color: #FFF7ED; padding: 10px; border-radius: 10px; margin-bottom: 10px; display: block; width: fit-content; max-width: 80%;'>"
                f"Bot: {bot_message}</div>"
            )
    return "\n\n".join(formatted_messages)


def refresh_conversations():
    global all_conversations
    if amp_manager:
        # Update all_conversations with amp_manager conversations
        all_conversations.update(amp_manager.conversations.keys())
        return gr.update(choices=list(all_conversations))
    return gr.update(choices=[])


def set_amp_manager(amp_manager_instance):
    global amp_manager
    amp_manager = amp_manager_instance


def start_new_conversation():
    global all_conversations
    new_conversation_id = f"amp_{uuid.uuid4()}"
    all_conversations.add(new_conversation_id)
    return (
        gr.update(choices=list(all_conversations), value=new_conversation_id),
        "",
    )


def send_message(conversation_id, message):
    if not conversation_id or not amp_manager:
        return "", ""

    # Check if the message is empty or only contains whitespace
    if not message.strip():
        return "", gr.Warning("Please enter a message before sending.")

    success, response = amp_manager.generate_response(
        {
            "conversation_id": conversation_id,
            "message": message,
            "max_tokens": 1000,  # You can adjust this value as needed
            "single_message_mode": False,
        }
    )

    if success:
        return update_conversation_content(conversation_id), ""
    else:
        return current_conversation, gr.Warning(
            "An error occurred while generating the response. Please try again."
        )


def create_interface():

    with gr.Blocks() as iface:
        gr.Markdown("# AI Chat Interface")

        with gr.Row():
            global conversation_dropdown  # Add this line to make conversation_dropdown global
            conversation_dropdown = gr.Dropdown(
                choices=[],
                label="Select Conversation",
            )
            new_conversation_btn = gr.Button("Start New Conversation")

        # Replace gr.HTML with gr.Markdown
        conversation_display = gr.Markdown(label="Conversation")

        with gr.Row():
            message_input = gr.Textbox(
                label="Your message", placeholder="Type your message here..."
            )
            send_btn = gr.Button("Send")

        new_conversation_btn.click(
            fn=start_new_conversation, outputs=[conversation_dropdown, message_input]
        )

        conversation_dropdown.change(
            fn=update_conversation_content,
            inputs=[conversation_dropdown],
            outputs=[conversation_display],
        )

        # Add this new line to handle the submit event of the message_input
        message_input.submit(
            fn=send_message,
            inputs=[conversation_dropdown, message_input],
            outputs=[conversation_display, message_input],
        )

        send_btn.click(
            fn=send_message,
            inputs=[conversation_dropdown, message_input],
            outputs=[conversation_display, message_input],
        )

        # Auto-refresh available conversations
        timer_available_conversations = gr.Timer(value=5)
        timer_available_conversations.tick(
            fn=refresh_conversations, outputs=[conversation_dropdown]
        )

        iface.load(fn=refresh_conversations, outputs=[conversation_dropdown])

    return iface


all_conversations = set()
