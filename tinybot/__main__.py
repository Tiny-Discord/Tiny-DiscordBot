import asyncio
import logging
import os
import sys

import discord
from dotenv import load_dotenv

from .bot import TinyBot
from .cli import parse_cli_flags
from .logger import init_logging

init_logging()
log = logging.getLogger("tinybot.main")

cli_flags, _ = parse_cli_flags()
load_dotenv(cli_flags.dotenvfile_path)

UVLOOP_INSTALLED: bool = False

def _update_event_loop_policy(_asyncio) -> None:
    if sys.implementation.name == "cpython":
        try:
            import uvloop as _uvloop # type: ignore
            UVLOOP_INSTALLED = True
        except ImportError:
            pass
        else:
            if not isinstance(_asyncio.get_event_loop_policy(), _uvloop.EventLoopPolicy()):
                _asyncio.set_event_loop_policy(_uvloop.EventLoopPolicy())


async def run_bot() -> None:
    if sys.platform.startswith("win"):
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.new_event_loop()
    
    asyncio.set_event_loop(loop)
    
    if UVLOOP_INSTALLED:
        _update_event_loop_policy(_asyncio=asyncio)
    else:
        pass
    
    async with TinyBot(
        prefix=cli_flags.prefix,
        owner_ids=cli_flags.owner,
    ) as bot:
        try:
            log.info("Starting Tiny-DicordBot!")
            await bot.start(os.environ['DISCORD_TOKEN'])
        except discord.LoginFailure:
            log.exception("Failed to login to Discord:", exc_info=True)
        except discord.PrivilegedIntentsRequired:
            log.error(
                "You are missing one of the privileged intents. Please review on the developer Portal."
            )
        except KeyboardInterrupt:
            print("CTRL + C received, exiting gracefully...")
        finally:
            log.info("Shutting down")
            
            await bot.close()
            
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(asyncio.sleep(2))
            
            asyncio.set_event_loop(None)
            
            loop.stop()
            loop.close()
    
            sys.exit()


if __name__ == "__main__":
    asyncio.run(run_bot())
