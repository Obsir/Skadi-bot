from nonebot import on_command, on_regex, logger, export
from nonebot.rule import to_me
from .query_resource import get_resource_type_list, query_resource, init
from ..utils import get_message_text, scheduler
from nonebot.adapters.cqhttp import Bot, MessageEvent, GroupMessageEvent, Message
from nonebot.typing import T_State
from skadi_core.utils.plugin_utils import init_export
from nonebot.permission import SUPERUSER
from nonebot.adapters.cqhttp.permission import GROUP, PRIVATE_FRIEND
import re

try:
    import ujson as json
except ModuleNotFoundError:
    import json

__plugin_name__ = "原神资源查询"

__plugin_usage__ = (
    "【原神资源查询】\n 用法：\n" "\t原神资源查询 [消息]\n" "\t原神资源列表\n" "\t[消息]在哪\n" "\t哪有[消息]\n" "[消息] = 资源名称"
)
init_export(export(), __plugin_name__, __plugin_usage__)
qr = on_regex("原神资源查询", priority=5, block=True)
qr_lst = on_regex("原神资源列表", priority=5, block=True)
rex_qr = on_regex(".*?(在哪|在哪里|哪有|哪里有).*?", permission=GROUP | PRIVATE_FRIEND, priority=5, block=True)
update_info = on_command('更新原神资源信息', permission=SUPERUSER, priority=1, block=True)


@qr.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State):
    resource_name = str(event.get_message()).strip()
    await qr.send('正在生成位置....')
    rst = await query_resource(resource_name)
    await qr.send(Message(rst), at_sender=True)
    logger.info(
        f"(USER {event.user_id}, GROUP {event.group_id if isinstance(event, GroupMessageEvent) else 'private'})"
        f" 查询原神材料:" + resource_name
    )


@rex_qr.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State):
    msg = str(event.get_message()).strip()
    if msg.find("在哪") != -1:
        rs = re.search("(.*)在哪.*?", msg)
        resource_name = rs.group(1) if rs else ""
    else:
        rs = re.search(".*?(哪有|哪里有)(.*)", msg)
        resource_name = rs.group(2) if rs else ""
    if resource_name:
        await qr.send('正在生成位置....')
        msg = await query_resource(resource_name)
        await rex_qr.send(Message(msg), at_sender=True)
        logger.info(
            f"(USER {event.user_id}, GROUP {event.group_id if isinstance(event, GroupMessageEvent) else 'private'})"
            f" 查询原神材料:" + resource_name
        )


@qr_lst.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State):
    mes_list = []
    txt = get_resource_type_list()
    txt_list = txt.split("\n")
    if event.message_type == "group":
        for txt in txt_list:
            data = {
                "type": "node",
                "data": {
                    "name": f"这里是{list(bot.config.nickname)[0]}酱",
                    "uin": f"{bot.self_id}",
                    "content": txt,
                },
            }
            mes_list.append(data)
    if isinstance(event, GroupMessageEvent):
        await bot.send_group_forward_msg(group_id=event.group_id, messages=mes_list)
    else:
        rst = ""
        for i in range(len(txt_list)):
            rst += txt_list[i] + "\n"
            if i % 5 == 0:
                if rst:
                    await qr_lst.send(rst)
                rst = ""


@update_info.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State):
    await init(True)
    await update_info.send('更新原神资源信息完成...')


@scheduler.scheduled_job(
    'cron',
    hour=5,
    minute=1,
)
async def _():
    try:
        await init()
        logger.info(f'每日更新原神材料信息成功！')
    except Exception as e:
        logger.error(f'每日更新原神材料信息错误：{e}')
