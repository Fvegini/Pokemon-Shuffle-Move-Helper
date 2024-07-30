from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import threading
import asyncio
import os
from src.execution_variables import current_run
from src import log_utils, custom_utils, config_utils, adb_commands

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
USER_ID = os.getenv("DISCORD_USER_ID")

class TelegramBot:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.application = Application.builder().token(BOT_TOKEN).build()

        self.application.add_handler(CommandHandler("pause_loop", self.pause_loop))
        self.application.add_handler(CommandHandler("pause_sleep", self.disable_sleep))
        self.application.add_handler(MessageHandler(filters.TEXT, self.handle_message))

        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.run_bot, daemon=True)
        self.thread.start()

    async def send_to_telegram(self, text):
        await self.bot.send_message(chat_id=USER_ID, text=text)

    async def handle_message(self, update: Update, context: CallbackContext):
        await self.bot.send_message(chat_id=USER_ID, text="The commands you must input are: /pause_loop or /pause_sleep")
    
    async def pause_loop(self, update: Update, context: CallbackContext):
        current_run.disable_loop = True
        await self.bot.send_message(chat_id=USER_ID, text="The Loop Was Paused")

    async def disable_sleep(self, update: Update, context: CallbackContext):
        config_utils.update_config("sleep_machine", False)
        await self.bot.send_message(chat_id=USER_ID, text="The Sleep Was Disabled")

    def run_bot(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.application.run_polling())

    def send_message(self, text):
        asyncio.run_coroutine_threadsafe(self.send_to_telegram(text), self.loop)

current_bot = TelegramBot()