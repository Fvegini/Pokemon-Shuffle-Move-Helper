import discord
from discord.ext import commands
import os
from src.discord import bot_processor
from io import BytesIO
from typing import TYPE_CHECKING
import threading
import asyncio
from src import log_utils

if TYPE_CHECKING:
    from main import ImageSelectorApp

log = log_utils.get_logger()

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_user = None
        self.root: "ImageSelectorApp" = None  # type: ignore

        # Define commands
        @self.command(aliases=["stage", "team"])  # type: ignore
        async def set_stage(ctx, *, text=""):
            if text.strip() != "":
                await bot_processor.set_team_stage(ctx, text)
            else:
                await bot_processor.show_team(ctx)

        @self.command(aliases=["add", "insert"])  # type: ignore
        async def add_pokemon(ctx, *, text=""):
            if text.strip() != "":
                await bot_processor.add_to_team(ctx, text)
            else:
                await ctx.send("Missing Pokemon Name to Add")

        @self.command(aliases=['delete', "remove", "del"])  # type: ignore
        async def remove_pokemon(ctx, *, text=""):
            if text.strip() != "":
                await bot_processor.remove_from_team(ctx, text)
            else:
                await ctx.send("Missing Pokemon Name to Remove")

        @self.command(aliases=['execute'])  # type: ignore
        async def execute_helper(ctx, *, text=""):
            result = self.root.execute_board_analysis(source="manual")
            await ctx.send(f"{result.result}")

    async def on_ready(self):
        self.target_user = await self.fetch_user(int(os.getenv("DISCORD_ID", "")))
        log.info(f'Logged in as {self.user}!')

    @commands.Cog.listener()
    async def on_message(self, message):
        await discord_bot.process_commands(message)
        if message.author.bot and message.author.name != "WebhookTest":
            return
        elif message.content == "!execute":
            ctx = await self.get_context(message)
            discord_bot.root.execute_board_analysis(source="manual")
            # await ctx.send(f"{result.result}")
        elif not message.content and len(message.attachments) > 0:
            ctx = await self.get_context(message)
            attachment_url = message.attachments[0].url
            await bot_processor.process_with_image_url(ctx, attachment_url, self.target_user)
        return

# Define the bot globally
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

discord_bot = MyBot(command_prefix='!', intents=intents)

def run_discord_bot():
    discord_bot.run(os.getenv("DISCORD_TOKEN", ""))

# Running the bot in a separate thread
discord_thread = threading.Thread(target=run_discord_bot, daemon=True)
# discord_thread.start()