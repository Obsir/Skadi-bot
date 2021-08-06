import re
from .analysis_bilibili import b23_extract, bili_keyword
from nonebot import on_regex, export
from nonebot.adapters import Bot, Event
from skadi_core.utils.plugin_utils import init_export, init_permission_state
__plugin_name__ = 'nh'
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

analysis_bili = on_regex("(b23.tv)|(live.bilibili.com)|(bilibili.com/video)|(bilibili.com/read)|(bilibili.com/bangumi)|(^(CV|cv)(\d+))|(^(BV|bv)([0-9A-Za-z]{10}))|(^(av|AV)([0-9]+)(/.*|\\?.*|)$)|(\[\[QQ小程序\]哔哩哔哩\])|(QQ小程序&amp;#93;哔哩哔哩)|(QQ小程序&#93;哔哩哔哩)")

@analysis_bili.handle()
async def analysis_main(bot: Bot, event: Event, state: dict):
    text = str(event.message).strip()
    if "b23.tv" in text:
        # 提前处理短链接，避免解析到其他的
        text = await b23_extract(text)
    try:
        group_id = event.group_id
    except:
        group_id = "1"
    msg = await bili_keyword(group_id, text)
    if msg:
        try:
            await analysis_bili.send(msg)
        except:
            await analysis_bili.send("此次解析可能被风控，尝试去除简介后发送！")
            msg = re.sub(r"简介.*", "", msg)
            await analysis_bili.send(msg)
