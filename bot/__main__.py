import asyncio
import logging

import discord
import sentry_sdk
from async_rediscache import RedisSession
from discord.ext.commands import when_mentioned_or
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from bot import constants, patches
from bot.bot import Bot

sentry_logging = LoggingIntegration(
    level=logging.DEBUG,
    event_level=logging.WARNING
)

sentry_sdk.init(
    dsn=constants.Bot.sentry_dsn,
    integrations=[
        sentry_logging,
        AioHttpIntegration(),
        RedisIntegration(),
    ]
)

# Create the redis session instance.
redis_session = RedisSession(
    address=(constants.Redis.host, constants.Redis.port),
    password=constants.Redis.password,
    minsize=1,
    maxsize=20,
    use_fakeredis=constants.Redis.use_fakeredis,
    global_namespace="bot",
)

# Connect redis session to ensure it's connected before we try to access Redis
# from somewhere within the bot. We create the event loop in the same way
# discord.py normally does and pass it to the bot's __init__.
loop = asyncio.get_event_loop()
loop.run_until_complete(redis_session.connect())


allowed_roles = [discord.Object(id_) for id_ in constants.MODERATION_ROLES]
bot = Bot(
    redis_session=redis_session,
    loop=loop,
    command_prefix=when_mentioned_or(constants.Bot.prefix),
    activity=discord.Game(name="Commands: !help"),
    case_insensitive=True,
    max_messages=10_000,
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=allowed_roles)
)

# Internal/debug
bot.load_extension("bot.cogs.config_verifier")
bot.load_extension("bot.cogs.error_handler")
bot.load_extension("bot.cogs.filtering")
bot.load_extension("bot.cogs.logging")
bot.load_extension("bot.cogs.security")

# Commands, etc
bot.load_extension("bot.cogs.antimalware")
bot.load_extension("bot.cogs.antispam")
bot.load_extension("bot.cogs.bot")
bot.load_extension("bot.cogs.clean")
bot.load_extension("bot.cogs.doc")
bot.load_extension("bot.cogs.extensions")
bot.load_extension("bot.cogs.help")
bot.load_extension("bot.cogs.verification")

# Feature cogs
bot.load_extension("bot.cogs.alias")
bot.load_extension("bot.cogs.defcon")
bot.load_extension("bot.cogs.dm_relay")
bot.load_extension("bot.cogs.duck_pond")
bot.load_extension("bot.cogs.eval")
bot.load_extension("bot.cogs.filter_lists")
bot.load_extension("bot.cogs.information")
bot.load_extension("bot.cogs.jams")
bot.load_extension("bot.cogs.moderation")
bot.load_extension("bot.cogs.off_topic_names")
bot.load_extension("bot.cogs.python_news")
bot.load_extension("bot.cogs.reddit")
bot.load_extension("bot.cogs.reminders")
bot.load_extension("bot.cogs.site")
bot.load_extension("bot.cogs.snekbox")
bot.load_extension("bot.cogs.source")
bot.load_extension("bot.cogs.stats")
bot.load_extension("bot.cogs.sync")
bot.load_extension("bot.cogs.tags")
bot.load_extension("bot.cogs.token_remover")
bot.load_extension("bot.cogs.utils")
bot.load_extension("bot.cogs.watchchannels")
bot.load_extension("bot.cogs.webhook_remover")

if constants.HelpChannels.enable:
    bot.load_extension("bot.cogs.help_channels")

# Apply `message_edited_at` patch if discord.py did not yet release a bug fix.
if not hasattr(discord.message.Message, '_handle_edited_timestamp'):
    patches.message_edited_at.apply_patch()

bot.run(constants.Bot.token)
