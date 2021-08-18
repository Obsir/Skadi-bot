from .alc import get_almanac_base64_str, load_data
import os
from nonebot import on_command, logger, get_driver, on_regex, export
from nonebot.typing import T_State
from nonebot.adapters.cqhttp import Bot, GroupMessageEvent, MessageEvent
from ..utils import image
from skadi_core.utils.plugin_utils import init_export
from nonebot.adapters.cqhttp.permission import GROUP, PRIVATE_FRIEND
from nonebot.permission import SUPERUSER

FILE_PATH = os.path.dirname(__file__)
__plugin_name__ = '原神黄历'
__plugin_usage__ = r'''【原神黄历】

群组/私聊可用


**Usage**
原神黄历
'''

# Init plugin export
init_export(export(), __plugin_name__, __plugin_usage__)
almanac = on_regex("原神黄历", priority=5, permission=GROUP | PRIVATE_FRIEND, block=True)
reload = on_regex("重载原神黄历(数据)?", priority=5, permission=SUPERUSER, block=True)


@almanac.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State):
    almanac_base64 = get_almanac_base64_str()
    mes = image(b64=almanac_base64) + "\n ※ 黄历数据来源于 genshin.pub"
    await almanac.send(mes)
    logger.info(
        f"(USER {event.user_id}, GROUP {event.group_id if isinstance(event, GroupMessageEvent) else 'private'})"
        f" 发送查看原神黄历"
    )


@reload.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State):
    global_config = get_driver().config
    superusers = global_config.superusers
    if event.user_id in [int(x) for x in superusers]:
        load_data()
        await reload.send("重载成功")
