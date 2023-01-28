from tinybot.bot import TinyBot

from .main import Owner


async def setup(bot: TinyBot):
    await bot.add_cog(Owner(bot))
