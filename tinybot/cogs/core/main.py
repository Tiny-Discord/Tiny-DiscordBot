import logging

from discord.ext import commands

from tinybot.bot import TinyBot

log = logging.getLogger("tinybot.cogs.owner")


class Owner(commands.Cog):
    def __init__(self, bot: TinyBot):
        self.bot: TinyBot = bot

    @commands.command(name="test")
    @commands.is_owner()
    async def test_command(self, ctx: commands.Context):
        await ctx.send("Beep Boop")

    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx: commands.Context):
        log.info("Shutting down...")
        await ctx.send("Shutting down...")
        await self.bot.close()

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx: commands.Context, cog_name: str):
        try:
            await self.bot.reload_extension(f"tinybot.cogs.{cog_name}")
        except commands.ExtensionNotLoaded:
            await ctx.send(f"Cog `{cog_name}` was not loaded.")
        except commands.ExtensionNotFound:
            await ctx.send(f"Cannot find cog with name `{cog_name}`.")
        except commands.NoEntryPointError:
            await ctx.send(f"Cog `{cog_name}` does not includes a `setup()` function.")
        except commands.ExtensionFailed as e:
            await ctx.send(
                f"Cog with name `{cog_name}` could not be reloaded. See logs for more details."
            )
            log.error(
                "Cog package with name `%s` could not be reloaded.",
                cog_name,
                exc_info=e.original,
            )
        else:
            await ctx.send(f"Reloaded `{cog_name}`.")

    @commands.is_owner()
    @commands.command()
    async def unload(self, ctx: commands.Context, cog_name: str) -> None:
        try:
            await self.bot.unload_extension(f"tinybot.cogs.{cog_name}")
        except commands.ExtensionNotLoaded:
            await ctx.send(f"Cog `{cog_name}` was not loaded.")
        else:
            await ctx.send(f"Unloaded `{cog_name}`.")

    @commands.is_owner()
    @commands.command()
    async def load(self, ctx: commands.Context, cog_name: str) -> None:
        try:
            await self.bot.load_extension(f"tinybot.cogs.{cog_name}")
        except commands.ExtensionAlreadyLoaded:
            await ctx.send(f"Cog `{cog_name}` is already loaded.")
        except commands.ExtensionNotFound:
            await ctx.send(f"Cannot find cog with name `{cog_name}.")
        except commands.NoEntryPointError:
            await ctx.send(f"Cog `{cog_name}` does not have a `setup()` function.")
        except commands.ExtensionFailed as e:
            await ctx.send(f"Cog `{cog_name}` could not be loaded. See logs for more details.")
            log.error(
                "Cog `%s` could not be loaded.",
                cog_name,
                exc_info=e.original,
            )
        else:
            await ctx.send(f"Loaded `{cog_name}`.")

    @commands.is_owner()
    @commands.command()
    async def sync(self, ctx: commands.Context):
        await self.bot.sync_commands()
        await ctx.send("Done.")
