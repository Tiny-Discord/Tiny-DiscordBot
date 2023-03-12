import logging
import platform
import traceback

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands


log = logging.getLogger("tinybot.bot")


class TinyBot(commands.AutoShardedBot):
    def __init__(self, prefix: str):
        super().__init__(
            command_prefix=commands.when_mentioned_or(prefix),
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=True, replied_user=True
            ),
            chunk_guilds_at_startup=True,
            intents=discord.Intents.all(),
            enable_debug_events=True,
        )
        self.session: aiohttp.ClientSession = aiohttp.ClientSession(
            headers={
                "User-Agent": f"TinyBot (Python/{platform.python_version()} aiohttp/{aiohttp.__version__})"
            }
        )
        self.color: discord.Color = discord.Color.dark_blue()

    async def setup_hook(self) -> None:
        for cog in ("tinybot.cogs.core",):
            await self.load_extension(cog)
            log.info("Loaded cog: %s", cog)

    async def sync_commands(self) -> None:
        self.tree.copy_global_to(guild=discord.Object(id=self.used_guild_id))
        await self.tree.sync(guild=discord.Object(id=self.used_guild_id))

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send_help(ctx.command)
        elif isinstance(error, commands.BadArgument):
            if error.args:
                await ctx.send(error.args[0], ephemeral=True)
            else:
                await ctx.send_help(ctx.command, ephemeral=True)
        elif isinstance(error, commands.CommandOnCooldown):
            if ctx.author.id in self.owner_ids:
                ctx.command.reset_cooldown(ctx)
                new_ctx = await self.get_context(ctx.message)
                await self.invoke(new_ctx)
                return

            cooldowns = {
                commands.BucketType.default: "globally",
                commands.BucketType.user: "for you globally",
                commands.BucketType.guild: "for this server",
                commands.BucketType.channel: "for this channel",
                commands.BucketType.member: "for you on this server",
                commands.BucketType.category: "for this channel category",
                commands.BucketType.role: "for your role",
            }
            await ctx.send(
                f"This command is on cooldown {cooldowns[error.type]}!\nTry again in {error.retry_after} seconds.",
                ephemeral=True,
            )
        elif isinstance(error, commands.CommandInvokeError):
            log.exception(
                "Exception in command '%s'", ctx.command.qualified_name, exc_info=error.original
            )
            exception_log = "Exception in command '{}'\n" "".format(ctx.command.qualified_name)
            exception_log += "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )

            await ctx.send(
                "Oops, something went wrong! This error has been forwarded to the bot owner.",
                ephemeral=True,
            )
        elif isinstance(error, commands.HybridCommandError):
            if isinstance(
                error.original, (commands.CommandInvokeError, app_commands.CommandInvokeError)
            ):
                log.exception(
                    "Exception in command '%s'", ctx.command.qualified_name, exc_info=error
                )
                exception_log = "Exception in command '{}'\n" "".format(ctx.command.qualified_name)
                exception_log += "".join(
                    traceback.format_exception(type(error), error, error.__traceback__)
                )

                await ctx.send(
                    "Oops, something went wrong! This error has been forwarded to the bot owner.",
                    ephemeral=True,
                )
            else:
                await ctx.send(error.original.args[0], ephemeral=True)
        elif isinstance(error, commands.CommandNotFound):
            pass
        else:
            log.error(type(error).__name__, exc_info=error)

    async def on_ready(self) -> None:
        log.info("Logged in as %s", str(self.user))
        log.info("TinyBot ready!")

    async def close(self) -> None:
        await self.session.close()
        await super().close()
