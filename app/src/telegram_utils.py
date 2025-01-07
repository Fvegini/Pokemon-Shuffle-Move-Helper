from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import threading
import asyncio
import os
from src.execution_variables import current_run
from src import log_utils, custom_utils, config_utils, adb_commands
from io import BytesIO
import time

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main import ImageSelectorApp

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
USER_ID = os.getenv("TELEGRAM_USER_ID", "")

class TelegramBot:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.root: "ImageSelectorApp" = None # type: ignore
        self.application = Application.builder().token(BOT_TOKEN).build()

        self.commands = [
            "disable_loop",
            "activate_loop",
            "disable_sleep",
            "activate_sleep",
            "disable_next_stage",
            "activate_next_stage",
            "disable_pause_survival_mode",
            "activate_pause_survival_mode",
            "get_current_screen_image",
            "execute_move",
            "execute_helper"
        ]

        for command in self.commands:
            handler_name = f"{command}"
            handler_function = getattr(self, handler_name)
            self.application.add_handler(CommandHandler(command, handler_function))

        # self.application.add_handler(MessageHandler(filters.TEXT, self.handle_message))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.UpdateType.EDITED_MESSAGE, self.handle_message))

        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.run_bot, daemon=True)
        self.thread.start()
        

    async def send_to_telegram(self, text):
        await self.bot.send_message(chat_id=USER_ID, text=text)

    async def handle_message(self, update: Update, context: CallbackContext):
        message_text: str = update.message.text # type: ignore
        # Check if the message starts with '/' and is a valid command
        if message_text.startswith("/") and message_text[1:] in self.commands:
            command_name = message_text[1:]
            handler_function = getattr(self, command_name)
            await handler_function(update, context)
        else:
            message = "The commands you must input are: /" + " /".join(self.commands)
            await self.bot.send_message(chat_id=USER_ID, text=message)
    
    async def disable_loop(self, update: Update, context: CallbackContext):
        self.root.disable_switch("control_loop")
        await self.bot.send_message(chat_id=USER_ID, text="The Loop Was Disabled")

    async def activate_loop(self, update: Update, context: CallbackContext):
        self.root.activate_switch("control_loop")
        await self.bot.send_message(chat_id=USER_ID, text="The Loop Was Activated")

    async def disable_sleep(self, update: Update, context: CallbackContext):
        self.root.disable_switch("sleep_machine")
        await self.bot.send_message(chat_id=USER_ID, text="The Sleep Was Disabled")

    async def activate_sleep(self, update: Update, context: CallbackContext):
        self.root.activate_switch("sleep_machine")
        await self.bot.send_message(chat_id=USER_ID, text="The Sleep Was Activated")

    async def disable_next_stage(self, update: Update, context: CallbackContext):
        self.root.disable_switch("auto_next_stage")
        await self.bot.send_message(chat_id=USER_ID, text="Auto next stage was Disabled")

    async def activate_next_stage(self, update: Update, context: CallbackContext):
        self.root.activate_switch("auto_next_stage")
        await self.bot.send_message(chat_id=USER_ID, text="Auto next stage was Activated")

    async def activate_pause_survival_mode(self, update: Update, context: CallbackContext):
        self.root.activate_switch("pause_survival")
        await self.bot.send_message(chat_id=USER_ID, text="The Survival Mode will be paused")

    async def disable_pause_survival_mode(self, update: Update, context: CallbackContext):
        self.root.disable_switch("pause_survival")
        await self.bot.send_message(chat_id=USER_ID, text="The Survival Mode pause was deactivated")

    async def get_current_screen_image(self, update: Update, context: CallbackContext):
        photo = self.get_current_screen_screenshot()
        await self.bot.send_photo(chat_id=USER_ID, photo=photo)

    async def execute_move(self, update: Update, context: CallbackContext):
        if len(context.args) != 2: # type: ignore
            await self.bot.send_message(chat_id=USER_ID, text="Please provide two arguments.")
            return
        arg1, arg2 = context.args # type: ignore
        self.root.adb_utils.execute_play(f"{custom_utils.convert_position(arg1)} -> {custom_utils.convert_position(arg2)}", None, "manual")
        await self.bot.send_message(chat_id=USER_ID, text=f"Executing move: {arg1} -> {arg2}")
        time.sleep(4)
        photo = self.get_current_screen_screenshot()
        await self.bot.send_photo(chat_id=USER_ID, photo=photo)

    def execute_helper(self, update: Update, context: CallbackContext):
        result = self.root.execute_board_analysis(source="manual")
        # if result and result.result:
            # await self.bot.send_message(chat_id=USER_ID, text=f"{result.result}")


    def get_current_screen_screenshot(self):
        screenshot = self.root.adb_utils.get_new_screenshot()
        pil_screenshot = custom_utils.cv2_to_pil(screenshot)
        bio = BytesIO()
        bio.name = 'image.png'
        pil_screenshot.save(bio, 'PNG')
        bio.seek(0)
        return bio

    def run_bot(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.application.run_polling()) # type: ignore

    def send_message(self, text):
        asyncio.run_coroutine_threadsafe(self.send_to_telegram(text), self.loop)

current_bot = TelegramBot()
