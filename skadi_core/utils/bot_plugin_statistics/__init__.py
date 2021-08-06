"""
插件命令统计系统
"""
from nonebot import get_plugin, get_driver, logger
from nonebot.adapters.cqhttp import MessageSegment, Message
from nonebot.exception import IgnoredException
from nonebot.message import run_postprocessor
from nonebot.typing import T_State
from nonebot.matcher import Matcher
from nonebot.adapters.cqhttp.bot import Bot
from nonebot.adapters.cqhttp.event import MessageEvent
from ..plugin_utils import add_plugin_use_count


@run_postprocessor
async def handle_plugin_use_count(matcher: Matcher, bot: Bot, event: MessageEvent, state: T_State):
    plugin_name = matcher.module
    res = await add_plugin_use_count(plugin_name)

    if res.error:
        group_id = event.dict().get('group_id')
        user_id = event.dict().get('user_id')
        logger.error(f'插件调用次数统计异常 group: {group_id}, user: {user_id}, error: {res.info}')
