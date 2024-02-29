import discord
from discord.ext import commands
import os
from src.discord import bot_processor
import cv2
from io import BytesIO
from typing import Any, Coroutine

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_user = None

        @self.command(aliases=["stage", "team"]) #type: ignore
        async def set_stage(ctx, *, text=""):
            if text.strip() != "":
                await bot_processor.set_team_stage(ctx, text)
            else:
                await bot_processor.show_team(ctx)

        @self.command(aliases=["add", "insert"]) #type: ignore
        async def add_pokemon(ctx, *, text=""):
            if text.strip() != "":
                await bot_processor.add_to_team(ctx, text)
            else:
                await ctx.send("Missing Pokemon Name to Add")

        @self.command(aliases=['delete', "remove", "del"]) #type: ignore
        async def remove_pokemon(ctx, *, text=""):
            if text.strip() != "":
                await bot_processor.remove_from_team(ctx, text)
            else:
                await ctx.send("Missing Pokemon Name to Remove")

    async def on_ready(self):
        self.target_user = await self.fetch_user(int(os.getenv("DISCORD_ID", "")))
        print(f'Logged in as {self.user}!')

    @commands.Cog.listener()
    async def on_message(self, message):
        await bot.process_commands(message)
        if message.author.bot and message.author.name != "WebhookTest":
            return
        if not message.content and len(message.attachments) > 0:
            ctx = await self.get_context(message)
            attachment_url = message.attachments[0].url
            await bot_processor.process_with_image_url(ctx, attachment_url, self.target_user)
        return

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = MyBot(command_prefix='!', intents=intents)

bot.run(os.getenv("DISCORD_TOKEN", "")) 