from nonebot import on_command, logger, on_regex, export
from .data_source import get_price, update_buff_cookie
from nonebot.typing import T_State
from nonebot.adapters.cqhttp import Bot, MessageEvent, GroupMessageEvent
from nonebot.rule import to_me
from nonebot.permission import SUPERUSER
from .utils import UserExistLimiter
from skadi_core.utils.plugin_utils import init_export

__plugin_name__ = "查询皮肤价格"
__plugin_usage__ = "【查询皮肤价格】\n\n查询皮肤帮助:\n\t" "查询皮肤 [枪械名] [皮肤]\n\t" "示例: 查询皮肤 awp 二西莫夫"

_ulmt = UserExistLimiter()
init_export(export(), __plugin_name__, __plugin_usage__)
search_skin = on_regex("查询皮肤", priority=5, block=True)


@search_skin.args_parser
async def parse(bot: Bot, event: MessageEvent, state: T_State):
    args = str(event.get_plaintext()).strip().lower().split()
    if not args:
        await search_skin.reject('你似乎没有发送有效的参数呢QAQ, 请重新发送:')
    state[state["_current_key"]] = args[0]
    if state[state["_current_key"]] == '取消':
        await search_skin.finish('操作已取消')


@search_skin.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State):
    args = str(event.get_plaintext()).strip().lower().split()
    if _ulmt.check(event.user_id):
        await search_skin.finish("您有皮肤正在搜索，请稍等...", at_sender=True)
    if args:
        if len(args) >= 3:
            state["name"] = args[1]
            state["skin"] = args[2]


@search_skin.got("name", prompt="要查询什么武器呢？")
@search_skin.got("skin", prompt="要查询该武器的什么皮肤呢？")
async def arg_handle(bot: Bot, event: MessageEvent, state: T_State):
    result = ""
    _ulmt.set_True(event.user_id)
    if state["name"] in ["ak", "ak47"]:
        state["name"] = "ak-47"
    name = state["name"] + " | " + state["skin"]
    try:
        result, status_code = await get_price(name)
    except FileNotFoundError:
        await search_skin.finish(F'请先对夏浪说"/设置cookie"来设置cookie！')
    if status_code in [996, 997, 998]:
        _ulmt.set_False(event.user_id)
        await search_skin.finish(result)
    if result:
        logger.info(
            f"(USER {event.user_id}, GROUP "
            f"{event.group_id if isinstance(event, GroupMessageEvent) else 'private'}) 查询皮肤:"
            + name
        )
        _ulmt.set_False(event.user_id)
        await search_skin.finish(result)
    else:
        logger.info(
            f"USER {event.user_id}, GROUP "
            f"{event.group_id if isinstance(event, GroupMessageEvent) else 'private'}"
            f" 查询皮肤：{name} 没有查询到"
        )
        _ulmt.set_False(event.user_id)
        await search_skin.finish("没有查询到哦，请检查格式吧")


update_buff_session = on_command(
    "更新cookie", aliases={'设置cookie'}, permission=SUPERUSER, priority=1
)

@update_buff_session.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State):
    await update_buff_session.finish(
        update_buff_cookie(str(event.get_message())), at_sender=True
    )
