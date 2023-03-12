from tinybot.bot import TinyBot

from .main import Downloader


async def setup(bot: TinyBot):
    await bot.add_cog(Downloader(bot))
