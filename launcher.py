from __future__ import annotations

import asyncio
import contextlib
import logging
from logging.handlers import RotatingFileHandler

import click
import discord
from decouple import config

from bot import CustomBot

log_path = (config("LOG_PATH", cast=str))

try:
    import uvloop  # type: ignore
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


class RemoveNoise(logging.Filter):
    def __init__(self):
        super().__init__(name='discord.state')

    def filter(self, record: logging.LogRecord) -> bool:
        return (
                record.levelname != 'WARNING'
                or 'referencing an unknown' not in record.msg
        )


@contextlib.contextmanager
def setup_logging():
    log = logging.getLogger()

    try:
        discord.utils.setup_logging()
        # __enter__
        max_bytes = 32 * 1024 * 1024  # 32 MiB
        logging.getLogger('discord').setLevel(logging.INFO)
        logging.getLogger('discord.http').setLevel(logging.WARNING)
        logging.getLogger('discord.state').addFilter(RemoveNoise())

        handler = RotatingFileHandler(filename=f"{log_path}/root.log", encoding='utf-8', mode='w', maxBytes=max_bytes,
                                      backupCount=5)
        handler.setLevel(logging.DEBUG)
        dt_fmt = '%Y-%m-%d %H:%M:%S'
        fmt = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')
        handler.setFormatter(fmt)
        log.addHandler(handler)

        handler = RotatingFileHandler(filename=f"{log_path}/error.log", encoding='utf-8', mode='w', maxBytes=max_bytes,
                                      backupCount=5)
        handler.setLevel(logging.ERROR)
        handler.setFormatter(fmt)
        log.addHandler(handler)

        yield
    finally:
        # __exit__
        handlers = log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            log.removeHandler(hdlr)


async def run_bot():
    log = logging.getLogger()

    async with CustomBot() as bot:
        await bot.start()


@click.group(invoke_without_command=True, options_metavar='[options]')
@click.pass_context
def main(ctx):
    """Launches the bot."""
    if ctx.invoked_subcommand is None:
        with setup_logging():
            asyncio.run(run_bot())


if __name__ == '__main__':
    main()
