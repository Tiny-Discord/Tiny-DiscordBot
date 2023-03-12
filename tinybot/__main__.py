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

if sys.implementation.name == "cpython":
    try:
        import uvloop as _uvloop  # type: ignore
    except ImportError:
        pass
    else:
        asyncio.set_event_loop_policy(_uvloop.EventLoopPolicy())


def run_bot() -> None:
    if sys.platform.startswith("win"):
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    bot = TinyBot(cli_flags.prefix)
    try:
        log.info("Starting TinyBot")
        loop.run_until_complete(bot.start(os.getenv("DISCORD_TOKEN")))
    except discord.LoginFailure:
        log.exception("Failed to login to Discord:")
    except discord.PrivilegedIntentsRequired:
        log.error(
            "You are missing one of the privileged intents. Please review on the developer Portal."
        )
    except KeyboardInterrupt:
        print("CTRL+C received, exiting...")
    finally:
        log.info("Shutting down")
        loop.run_until_complete(bot.close())
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.run_until_complete(asyncio.sleep(2))
        asyncio.set_event_loop(None)
        loop.stop()
        loop.close()

        sys.exit()


if __name__ == "__main__":
    run_bot()
