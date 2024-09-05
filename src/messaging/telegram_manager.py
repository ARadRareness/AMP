import os
from telegram import Bot


class TelegramManager:
    def __init__(self):
        self.bot_token = os.environ.get("TELEGRAM.BOT_TOKEN")
        self.chat_id = os.environ.get("TELEGRAM.CHAT_ID")

        if self.bot_token and self.chat_id:
            print("Telegram bot activated")
            self.bot = Bot(token=self.bot_token)
        else:
            print("Telegram bot not activated")
            self.bot = None

    def send_message(self, message: str) -> bool:
        if not self.bot:
            print(
                "You need to set the TELEGRAM.BOT_TOKEN and TELEGRAM.CHAT_ID environment variables to use the Telegram bot"
            )
            return False
        try:
            self.bot.send_message(chat_id=self.chat_id, text=message)
            return True
        except Exception as e:
            print(f"Failed to send message: {str(e)}")
            return False
