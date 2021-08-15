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
from nonebot.adapters.cqhttp.event import Event, PrivateMessageEvent, GroupMessageEvent
from ..plugin_utils import add_plugin_use_count
from typing import Optional


@run_postprocessor
async def handle_plugin_use_count(matcher: Matcher, exception: Optional[Exception], bot: Bot, event: Event,
                                  state: T_State):
    plugin_name = matcher.module.__plugin_name__
    res = await add_plugin_use_count(plugin_name)
    if res.error:
        if isinstance(event, PrivateMessageEvent):
            private_mode = True
        elif isinstance(event, GroupMessageEvent):
            private_mode = False
        else:
            private_mode = False
        group_id = None
        if not private_mode:
            group_id = event.group_id
        user_id = event.user_id
        logger.error(f'插件调用次数统计异常 group: {group_id}, user: {user_id}, error: {res.info}')
