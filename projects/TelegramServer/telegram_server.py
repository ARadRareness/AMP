import os
import uuid
import datetime
from dotenv import load_dotenv
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ParseMode,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler,
)

from amp_lib import AmpClient

"""
This project implements a Telegram bot server using the python-telegram-bot library.
It features:
- A conversation system using AmpClient for generating responses
- Example menu navigation with inline buttons
- Command handlers for /menu and /new (to start a new conversation)
- Environment variable configuration for bot token and chat ID
- A system prompt that can be customized and includes the current time

The bot can engage in conversations, provide menu options, and handle user interactions
through both text messages and button clicks.
"""

# Load environment variables from .env file
load_dotenv()

# Initialize AmpClient
client = AmpClient()

# Bot configuration
BOT_TOKEN = os.getenv("TELEGRAM.BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM.CHAT_ID")


class TelegramServer:
    def __init__(self):
        self.client = AmpClient()
        self.conversation_id = str(uuid.uuid4())
        self.add_system_message()

    def setup_handlers(self, dispatcher):
        dispatcher.add_handler(CommandHandler("menu", self.menu))
        dispatcher.add_handler(CallbackQueryHandler(self.button_tap))
        dispatcher.add_handler(MessageHandler(~Filters.command, self.echo))
        dispatcher.add_handler(CommandHandler("new", self.new_conversation))

    def add_system_message(self):
        system_prompt = os.environ.get(
            "TELEGRAM.SYSTEM_PROMPT", "You are a helpful assistant."
        ).replace("{time}", datetime.datetime.now().strftime("%H:%M"))

        self.client.add_system_message(self.conversation_id, system_prompt)

    def echo(self, update: Update, context: CallbackContext) -> None:
        user_message = update.message.text

        response = self.client.generate_response(self.conversation_id, user_message)

        update.message.reply_text(response)

    def new_conversation(self, update: Update, context: CallbackContext) -> None:
        self.conversation_id = str(uuid.uuid4())
        self.add_system_message()
        update.message.reply_text(
            f"Started a new conversation with ID: {self.conversation_id}"
        )

    def menu(self, update: Update, context: CallbackContext) -> None:
        context.bot.send_message(
            update.message.from_user.id,
            FIRST_MENU,
            parse_mode=ParseMode.HTML,
            reply_markup=FIRST_MENU_MARKUP,
        )

    def button_tap(self, update: Update, context: CallbackContext) -> None:
        data = update.callback_query.data
        text = ""
        markup = None

        if data == NEXT_BUTTON:
            text = SECOND_MENU
            markup = SECOND_MENU_MARKUP
        elif data == BACK_BUTTON:
            text = FIRST_MENU
            markup = FIRST_MENU_MARKUP

        update.callback_query.answer()
        update.callback_query.message.edit_text(
            text, ParseMode.HTML, reply_markup=markup
        )


def main():
    if not BOT_TOKEN or not CHAT_ID:
        print(
            "You need to set the TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in your .env file to use the Telegram bot"
        )
        return

    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher
    telegram_server = TelegramServer()
    telegram_server.setup_handlers(dispatcher)

    print("Telegram bot activated")
    updater.start_polling()
    updater.idle()


# Constants for menus and buttons
FIRST_MENU = "<b>Menu 1</b>\n\nA beautiful menu with a shiny inline button."
SECOND_MENU = "<b>Menu 2</b>\n\nA better menu with even more shiny inline buttons."
NEXT_BUTTON = "Next"
BACK_BUTTON = "Back"
TUTORIAL_BUTTON = "Tutorial"

FIRST_MENU_MARKUP = InlineKeyboardMarkup(
    [[InlineKeyboardButton(NEXT_BUTTON, callback_data=NEXT_BUTTON)]]
)
SECOND_MENU_MARKUP = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(BACK_BUTTON, callback_data=BACK_BUTTON)],
        [
            InlineKeyboardButton(
                TUTORIAL_BUTTON, url="https://core.telegram.org/bots/api"
            )
        ],
    ]
)

if __name__ == "__main__":
    main()
