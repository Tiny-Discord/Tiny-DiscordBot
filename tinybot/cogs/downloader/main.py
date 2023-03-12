import logging

from discord.ext import commands

from tinybot.bot import TinyBot

log = logging.getLogger("tinybot.cogs.owner")


class Downloader(commands.Cog):
    def __init__(self, bot: TinyBot):
        self.bot: TinyBot = bot
