import os
import threading
from telegram import (
    Bot,
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


class TelegramManager:
    def __init__(self):
        self.bot_token = os.environ.get("TELEGRAM.BOT_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM.CHAT_ID")

        if self.bot_token and self.chat_id:
            print("Telegram bot activated")
            self.bot = Bot(token=self.bot_token)
            self.updater = Updater(self.bot_token)
            self.dispatcher = self.updater.dispatcher
            self._setup_handlers()
        else:
            print("Telegram bot not activated")
            self.bot = None
            self.updater = None
            self.dispatcher = None

        self.screaming = False

    def _setup_handlers(self):
        self.dispatcher.add_handler(CommandHandler("scream", self.scream))
        self.dispatcher.add_handler(CommandHandler("whisper", self.whisper))
        self.dispatcher.add_handler(CommandHandler("menu", self.menu))
        self.dispatcher.add_handler(CallbackQueryHandler(self.button_tap))
        self.dispatcher.add_handler(MessageHandler(~Filters.command, self.echo))

    def send_message(self, message: str) -> bool:
        if not self.bot:
            print(
                "You need to set the TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables to use the Telegram bot"
            )
            return False
        try:
            self.bot.send_message(chat_id=self.chat_id, text=message)
            return True
        except Exception as e:
            print(f"Failed to send message: {str(e)}")
            return False

    def start_thread(self):
        if not self.updater:
            print("Telegram bot is not activated. Cannot start thread.")
            return

        def run_bot():
            self.updater.start_polling()

        self.bot_thread = threading.Thread(target=run_bot)
        self.bot_thread.start()
        print("Telegram bot thread started")

    def end_thread(self):
        if not self.updater:
            return

        self.updater.stop()
        self.bot_thread.join()

    def echo(self, update: Update, context: CallbackContext) -> None:
        print(f"{update.message.from_user.first_name} wrote {update.message.text}")
        print(f"Chat ID: {update.message.chat_id}")

        if self.screaming and update.message.text:
            context.bot.send_message(
                update.message.chat_id,
                update.message.text.upper(),
                entities=update.message.entities,
            )
        else:
            update.message.copy(update.message.chat_id)

    def scream(self, update: Update, context: CallbackContext) -> None:
        self.screaming = True

    def whisper(self, update: Update, context: CallbackContext) -> None:
        self.screaming = False

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
