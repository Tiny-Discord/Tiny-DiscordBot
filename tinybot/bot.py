from __future__ import annotations

import os
import logging
import datetime
import platform
import traceback
import collections
from typing import Any, Optional, Set, Union, TypeVar, Sequence, Type, Callable, Coroutine

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands


log: logging.Logger = logging.getLogger("tinybot.bot")


InteractionChannel = Union[
    discord.channel.VoiceChannel, 
    discord.channel.StageChannel, 
    discord.channel.TextChannel,
    discord.channel.ForumChannel,
    discord.channel.CategoryChannel,
    discord.threads.Thread,
    discord.channel.PartialMessageable,
]


class _InteractionT(discord.Interaction):
    bot: "TinyBot"
    response: discord.InteractionResponse
    followup: discord.Webhook
    command: Union[app_commands.Command[Any, ..., Any], app_commands.ContextMenu, None]
    channel: Union[InteractionChannel, None]
 
    
InteractionT = TypeVar("InteractionT", bound="Union[_InteractionT, discord.Interaction]")


class TinyBot(commands.AutoShardedBot):
    user: discord.ClientUser
    socket_stats: collections.Counter[str]
    bot_app_info: discord.AppInfo
    old_tree_errror: Callable[[discord.Interaction, discord.app_commands.AppCommandError], Coroutine[Any, Any, None]]
    
    cached_messages: Sequence[discord.Message]
    
    tree_cls: Type[app_commands.CommandTree]
    tree: app_commands.CommandTree
    
    def __init__(
        self,
        *args,
        prefix: str,
        owner_ids: Set[int] = set(),
        **kwargs: Any,
    ):
        self.is_ready: bool = False
        
        self.start_time: datetime.datetime = discord.utils.utcnow()
        
        self.startup_time: Optional[datetime.timedelta] = None
        
        intents: discord.Intents = discord.Intents.all()
        
        super().__init__(
            *args,
            command_prefix=commands.when_mentioned_or(prefix),
            member_cache_flags=discord.MemberCacheFlags.from_intents(intents),
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=True, replied_user=True
            ),
            chunk_guilds_at_startup=True,
            enable_debug_events=True,
            intents=intents,
            **kwargs,
        )
        
        self.owner_ids.update(owner_ids)
        
        self.session: aiohttp.ClientSession = aiohttp.ClientSession(
            headers={
                "User-Agent": f"TinyBot (Python/{platform.python_version()} aiohttp/{aiohttp.__version__})"
            }
        )
        
        self.color: discord.Color = discord.Color.dark_blue()
        
        if not hasattr(self, 'socket_stats'):
            self.socket_stats: collections.Counter[str] = collections.Counter()
        
        self.resumes: collections.defaultdict[int, list[datetime.datetime]] = collections.defaultdict(list)
        self.identifies: collections.defaultdict[int, list[datetime.datetime]] = collections.defaultdict(list)

    async def get_context(
        self, message: Union[discord.Message, InteractionT], /, *, cls: Optional[commands.Context] = None
    ) -> commands.Context:
        return await super(self.__class__, self).get_context(message, cls=cls if cls else commands.Context) # noqa
    
    @property
    def all_cogs(self) -> collections.ChainMap[Any, Any]:
        return collections.ChainMap(self.cogs)
    
    def _clear_gateway_data(self) -> None:
        one_week_ago = discord.utils.utcnow() - datetime.timedelta(days=7)
        for shard_id, dates in self.identifies.items():
            to_remove = [index for index, dt in enumerate(dates) if dt < one_week_ago]
            for index in reversed(to_remove):
                del dates[index]

        for shard_id, dates in self.resumes.items():
            to_remove = [index for index, dt in enumerate(dates) if dt < one_week_ago]
            for index in reversed(to_remove):
                del dates[index]
                
    async def on_shard_resumed(self, shard_id: int) -> None:
        self.resumes[shard_id].append(discord.utils.utcnow())
                
    async def before_identify_hook(self, shard_id: int, *, initial: bool) -> None:
        self._clear_gateway_data()
        self.identifies[shard_id].append(discord.utils.utcnow())
        await super().before_identify_hook(shard_id, initial=initial)
    
    async def setup_hook(self) -> None:
        cogs = [
            f"tinybot.cogs.{cog if not cog.endswith('.py') else cog[:-3]}"
            for cog in os.listdir(f'tinybot/cogs')
            if not cog.startswith("_")
        ]
        for cog in cogs:
            try:
                await self.load_extension(cog)
                log.info(f"Loaded cog: {cog}")
            except Exception:
                log.exception(f"Failed to load cog: {cog}", exc_info=True)

    async def sync_commands(self, guild: discord.Guild | None) -> None:
        if guild:
            self.tree.copy_global_to(guild=discord.Object(id=guild.id))
        await self.tree.sync(guild=discord.Object(id=guild.id) if guild else None)

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send_help(ctx.command)
        elif isinstance(error, commands.BadArgument):
            if error.args:
                await ctx.send(error.args[0], ephemeral=True)
            else:
                await ctx.send_help(ctx.command)
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
        if not hasattr(self, 'uptime'):
            self.uptime = discord.utils.utcnow()
        
        if not hasattr(self, 'appinfo'):
            self.appinfo = (await self.application_info())
            
        if self.is_ready:
            log.info(f'[ {self.user} ] reconnected at {datetime.datetime.now().strftime("%b %d %Y %H:%M:%S")}')
        else:
            self.is_ready = True
            self.startup_time = discord.utils.utcnow() - self.start_time
            log.info('--------------------------------------------------------------------------------------------------------------------')
            log.info("|████████╗██╗███╗   ██╗██╗   ██╗     ██████╗ ██╗███████╗ ██████╗ ██████╗ ██████╗ ██████╗ ██████╗  ██████╗ ████████╗|")
            log.info("|╚══██╔══╝██║████╗  ██║╚██╗ ██╔╝     ██╔══██╗██║██╔════╝██╔════╝██╔═══██╗██╔══██╗██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝|")
            log.info("|   ██║   ██║██╔██╗ ██║ ╚████╔╝█████╗██║  ██║██║███████╗██║     ██║   ██║██████╔╝██║  ██║██████╔╝██║   ██║   ██║   |")
            log.info("|   ██║   ██║██║╚██╗██║  ╚██╔╝ ╚════╝██║  ██║██║╚════██║██║     ██║   ██║██╔══██╗██║  ██║██╔══██╗██║   ██║   ██║   |")
            log.info("|   ██║   ██║██║ ╚████║   ██║        ██████╔╝██║███████║╚██████╗╚██████╔╝██║  ██║██████╔╝██████╔╝╚██████╔╝   ██║   |")
            log.info("|   ╚═╝   ╚═╝╚═╝  ╚═══╝   ╚═╝        ╚═════╝ ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚═════╝  ╚═════╝    ╚═╝   |")
            log.info('--------------------------------------------------------------------------------------------------------------------')
            log.info(f"Discord.py: {discord.__version__} | Servers: {len(self.guilds)} | Users: {(sum(len(i.members) for i in self.guilds)):,}")
            log.info('--------------------------------------------------------------------------------------------------------------------')
            log.info(f'Startup Time: {self.startup_time.total_seconds():.2f} seconds')
            log.info('--------------------------------------------------------------------------------------------------------------------')
            log.info(f'Owners: {", ".join(str(i) for i in self.owner_ids)}')
            log.info('--------------------------------------------------------------------------------------------------------------------')

    async def close(self) -> None:
        await self.session.close()
        await super().close()
