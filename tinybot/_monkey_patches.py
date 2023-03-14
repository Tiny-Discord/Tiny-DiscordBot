from typing import Any

import discord
from discord.ext import commands


_int = lambda self: self.id


__all__ = [
    '_apply_monkey_patches'
]


@property
def guild_jump_url(self) -> str:
    """
    Returns an URL that allows the client to jump to this guild.
    """
    return "https://discord.com/channels/{0.id}".format(self)


@property
def messageable_jump_url(self) -> str:
    """
    Returns a URL that allows the client to jump to this channel.
    """
    if isinstance(self, discord.abc.User):
        if self.dm_channel is None: # type: ignore
            raise AttributeError("Could not find DM channel for user '{0}'".format(self))
        
        channel_id = self.dm_channel.id # type: ignore
    else:
        channel_id = self.channel.id if hasattr(self, "channel") else self.id
        
    guild_id = self.guild.id if isinstance(self, discord.abc.GuildChannel) else "@me"
    
    return "https://discord.com/channels/{0}/{1}".format(guild_id, channel_id)


_old_delete = discord.Message.delete


async def delete(self, *, supress_error: bool = False, **kwargs: Any) -> None:
    try:
        await _old_delete(self, **kwargs)
    except Exception as e:
        if not supress_error:
            raise e
        

def wait_for(self, event: Any, *, check: Any = None, timeout: int = None) -> Any: # type: ignore
    actual_wait_for = self._state.dispatch.__self__.wait_for

    if check is None:

        def check(*args: Any):
            return True

    def actual_check(*args):
        for arg in args:
            if isinstance(arg, (discord.Message, commands.Context)):
                if arg.channel.id == self.id:
                    return check(*args)
            elif isinstance(arg, discord.abc.Messageable):
                if arg.id == self.id: # type: ignore
                    return check(*args)

    return actual_wait_for(event, check=actual_check, timeout=timeout)


def _apply_monkey_patches() -> None:
    discord.Message.delete = delete
    discord.Guild.jump_url = guild_jump_url # type: ignore
    discord.abc.Messageable.jump_url = messageable_jump_url # type: ignore
    discord.AuditLogEntry.__int__ = _int # type: ignore
    discord.emoji._EmojiTag.__int__ = _int # type: ignore
    discord.mixins.Hashable.__int__ = _int # type: ignore
    discord.Member.__int__ = _int # type: ignore
    discord.abc.Messageable.wait_for = wait_for # type: ignore
