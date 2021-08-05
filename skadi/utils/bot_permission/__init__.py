from nonebot import get_driver, logger
from nonebot.exception import IgnoredException
from nonebot.message import run_preprocessor
from nonebot.typing import T_State
from nonebot.matcher import Matcher
from nonebot.adapters.cqhttp.bot import Bot
from nonebot.adapters.cqhttp.event import MessageEvent, GroupMessageEvent, PrivateMessageEvent
from ..plugin_utils import \
    check_command_permission, check_permission_level, check_auth_node, check_friend_private_permission


@run_preprocessor
async def handle_plugin_permission(matcher: Matcher, bot: Bot, event: MessageEvent, state: T_State):
    if isinstance(event, PrivateMessageEvent):
        private_mode = True
    elif isinstance(event, GroupMessageEvent):
        private_mode = False
    else:
        private_mode = False

    group_id = event.dict().get('group_id')
    user_id = event.dict().get('user_id')

    global_config = get_driver().config
    superusers = global_config.superusers

    # 忽略超级用户
    if user_id in [int(x) for x in superusers]:
        return

    matcher_default_state = matcher.state
    matcher_command_permission = matcher_default_state.get('_command_permission')
    matcher_permission_level = matcher_default_state.get('_permission_level')
    matcher_auth_node = matcher_default_state.get('_auth_node')

    # 检查command/friend_private权限
    if private_mode:
        if matcher_command_permission:
            command_checker = await check_friend_private_permission(user_id=user_id)
            if command_checker:
                pass
            else:
                await bot.send(event=event, message=f'没有好友命令权限QAQ, 请添加好友后使用"/skadi enable"或"/skadi init"启用')
                raise IgnoredException('没有好友命令权限')
    else:
        if matcher_command_permission:
            command_checker = await check_command_permission(group_id=group_id)
            if command_checker:
                pass
            else:
                await bot.send(event=event, message=f'没有群组命令权限QAQ')
                raise IgnoredException('没有群组命令权限')

    # 检查权限等级 好友私聊跳过
    if matcher_permission_level:
        if private_mode:
            level_checker = True
        else:
            level_checker = await check_permission_level(group_id=group_id, level=matcher_permission_level)
    else:
        level_checker = False

    # 检查权限节点
    if matcher_auth_node:
        auth_node = '.'.join([matcher.module, matcher_auth_node])
        # 分别检查用户及群组权限节点
        user_auth_checker = await check_auth_node(auth_id=user_id, auth_type='user', auth_node=auth_node)
        if private_mode:
            group_auth_checker = 0
        else:
            group_auth_checker = await check_auth_node(auth_id=group_id, auth_type='group', auth_node=auth_node)
        # 优先级: 用户权限节点>群组权限节点>权限等级
        if user_auth_checker == -1 or group_auth_checker == -1:
            await bot.send(event=event, message=f'权限受限QAQ')
            raise IgnoredException('被deny的权限节点')
        if user_auth_checker == 1:
            return
        elif group_auth_checker == 1:
            return
        elif level_checker:
            return
        else:
            await bot.send(event=event, message=f'权限不足QAQ')
            raise IgnoredException('权限不足')
    elif matcher_permission_level and level_checker:
        return
    elif matcher_permission_level and not level_checker:
        await bot.send(event=event, message=f'群组权限等级不足QAQ')
        raise IgnoredException('群组权限等级不足')
