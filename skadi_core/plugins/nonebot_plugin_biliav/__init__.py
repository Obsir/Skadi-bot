# import nonebot
from nonebot import get_driver, on_regex, export

from .config import Config
from nonebot.typing import T_State
from nonebot.adapters import Bot, Event, Message
from skadi_core.utils.plugin_utils import init_export, init_permission_state
global_config = get_driver().config
config = Config(**global_config.dict())

from .data_source import get_av_data
import re
__plugin_name__ = '转换bilibili的小程序/链接'
__plugin_usage__ = r'''【bilibili的小程序/链接】
群聊/私聊

**Usage**
发送BV号或链接
'''

# 声明本插件可配置的权限节点
__plugin_auth_node__ = [
]

# Init plugin export
init_export(export(), __plugin_name__, __plugin_usage__, __plugin_auth_node__)
biliav = on_regex("av(\d{1,12})|BV(1[A-Za-z0-9]{2}4.1.7[A-Za-z0-9]{2})", priority=10)


@biliav.handle()
async def handle(bot: Bot, event: Event, state: T_State):
    avcode = re.search('av(\d{1,12})|BV(1[A-Za-z0-9]{2}4.1.7[A-Za-z0-9]{2})', str(event.get_message()))
    if avcode == None:
        return
    rj = await get_av_data(avcode[0])
    await biliav.send(rj)
