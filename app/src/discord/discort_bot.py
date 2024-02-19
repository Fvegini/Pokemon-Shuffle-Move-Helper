import discord
from discord.ext import commands
import os
from pathlib import Path
from src import match_icons, shuffle_config_files
from src.discord import bot_processor
import requests
import numpy as np
import cv2
from io import BytesIO

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_user = None

        @self.command(name="team")
        async def custom_command(ctx, *, text=""):
            if text.strip() != "":
                await bot_processor.register_team(ctx.message.author.global_name, text, ctx)
            else:
                await bot_processor.show_team(ctx.message.author.global_name, ctx)

    async def on_ready(self):
        self.target_user = await self.fetch_user(int(os.getenv("DISCORD_ID")))
        print(f'Logged in as {self.user}!')

    @commands.Cog.listener()
    async def on_message(self, message):
        await bot.process_commands(message)
        if message.author.bot and message.author.name != "WebhookTest":
            return
        if not message.content and len(message.attachments) > 0:
            ctx = await self.get_context(message)
            username = ctx.message.author.global_name
            if not username:
                username = "Vegini"
            attachment_url = message.attachments[0].url
            result, image = await bot_processor.process_with_image_url(attachment_url, ctx, username, message.content)
            if message.author.name == "WebhookTest" and self.target_user:
                # image_bytes = cv2.imencode('.png', image)[1].tobytes()
                # image_file = BytesIO(image_bytes)
                # await self.target_user.send(file=discord.File(image_file, "final_image.png"))
                await self.target_user.send(result)
            else:
                image_bytes = cv2.imencode('.png', image)[1].tobytes()
                image_file = BytesIO(image_bytes)
                await ctx.send(file=discord.File(image_file, "final_image.png"))
                await ctx.send(f"Result: {result}")
        return

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = MyBot(command_prefix='!', intents=intents)

bot.run(os.getenv("DISCORD_TOKEN"))





# import os
# import discord
# from discord.ext import commands
# from pathlib import Path
# from src import match_icons, shuffle_config_files
# from src.discord import bot_processor
# import requests
# import numpy as np
# import cv2
# from io import BytesIO

# TOKEN = os.getenv('DISCORD_TOKEN')

# intents = discord.Intents.default()
# intents.members = True
# intents.message_content = True

# # Create a bot instance
# bot = commands.Bot(command_prefix='!', intents=intents)
# main_user = None

# class MyBot(commands.Bot):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.target_user = None
        
        
#     async def on_ready(self):
#         self.target_user = await self.fetch_user(int(os.getenv("DISCORD_ID")))
#         print(f'Logged in as {self.user}!')

# @bot.event
# async def on_ready():
#     global main_user
#     print(f'We have logged in as {bot.user}')
#     main_user = await bot.fetch_user(os.getenv("DISCORD_ID"))
#     print(f'We have logged in as {main_user}')

# @bot.command()
# async def text(ctx, *, text):
#     # Command to handle text input
#     await ctx.send(f"Hello {ctx.message.author.global_name}")
#     await ctx.send(f"You entered: {text}")

# @bot.command()
# async def team(ctx, *, text=""):
#     # Command to handle text input
#     if text.strip() != "":
#         await bot_processor.register_team(ctx.message.author.global_name, text, ctx)
#     else:
#         await bot_processor.show_team(ctx.message.author.global_name, ctx)
#     # await ctx.send(f"Hello {ctx.message.author.global_name}")
#     # await ctx.send(f"You entered: {text}")
    
# # @bot.command()
# # async def image(ctx, *, text=""):
# #     # Command to handle image input
# #     if len(ctx.message.attachments) > 0:
# #         print("image received")
# #         attachment_url = ctx.message.attachments[0].url
# #         result, image = bot_processor.process_with_image_url(attachment_url, ctx, ctx.message.author.global_name, text)

# #         image_bytes = cv2.imencode('.jpg', image)[1].tobytes()
# #         image_file = BytesIO(image_bytes)
# #         await ctx.send(file=discord.File(image_file, "final_image.jpg"))
# #         await ctx.send(f"Result: {result}")
# #     else:
# #         await ctx.send("Please attach an image with your command.")

# @bot.listen('on_message')
# async def my_function(message):
#     if message.author.bot and message.author.name != "WebhookTest":
#         return
#     if not message.content and len(message.attachments) > 0:
#         ctx = await bot.get_context(message)
#         username = ctx.message.author.global_name
#         if not username:
#             username = "Vegini"
#         attachment_url = message.attachments[0].url
#         result, image = bot_processor.process_with_image_url(attachment_url, ctx, username, message.content)
#         image_bytes = cv2.imencode('.jpg', image)[1].tobytes()
#         image_file = BytesIO(image_bytes)
#         await ctx.send(file=discord.File(image_file, "final_image.jpg"))
#         await ctx.send(f"Result: {result}")
#         if main_user:
#             await main_user.send(result)
#     return

# bot.run(TOKEN)