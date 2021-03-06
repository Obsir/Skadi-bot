import asyncio
from nonebot import CommandGroup, on_command, export, logger, get_driver
from nonebot.rule import to_me
from nonebot.permission import SUPERUSER
from nonebot.typing import T_State
from nonebot.adapters.cqhttp.bot import Bot
from nonebot.adapters.cqhttp.event import MessageEvent, GroupMessageEvent, PrivateMessageEvent
from nonebot.adapters.cqhttp.permission import GROUP, PRIVATE_FRIEND
from nonebot.adapters.cqhttp import MessageSegment
from skadi_core.utils.plugin_utils import init_export, init_permission_state, PluginCoolDown
from skadi_core.utils.arknights_utils import ArkGameData, ArkEnemyHandler, ArkOperatorHandler, ArkMaterialHandler, \
    utils, ArkGaChaHandler
import re

# Custom plugin usage text
__plugin_name__ = '明日方舟插件包'
__plugin_usage__ = r'''【明日方舟插件包】

群组/私聊可用

**Permission**
Friend Private
Command & Lv.20
or AuthNode

**AuthNode**
setu
moepic


**Usage**
/ark [十]连
/ark 查询敌人[名称]
/ark 查询材料[名称]
/ark 更新 - 超级管理员限定
'''

# 声明本插件可配置的权限节点
__plugin_auth_node__ = [
    # PluginCoolDown.skip_auth_node,
    # 'setu',
    # 'moepic'
]
global_config = get_driver().config
superusers = global_config.superusers
# Init plugin export
init_export(export(), __plugin_name__, __plugin_usage__, __plugin_auth_node__)

# 注册事件响应器
ark = on_command('arknights', aliases={'ark', 'ARK'}, permission=GROUP | PRIVATE_FRIEND | SUPERUSER,
                 priority=20,
                 block=True, state=init_permission_state(
        name='arknights',
        command=True,
        level=20), )

ark_data_handler = ArkGameData()

ark_enemy_handler = ArkEnemyHandler()
ark_material_handler = ArkMaterialHandler()
ark_operator_handler = ArkOperatorHandler()
ark_gacha_handler = ArkGaChaHandler()
handlers = [
    ark_operator_handler,
    ark_material_handler,
    ark_enemy_handler,
    ark_gacha_handler,
]


# 修改默认参数处理
@ark.args_parser
async def parse(bot: Bot, event: MessageEvent, state: T_State):
    args = str(event.get_plaintext()).strip().lower().split()
    if not args:
        await ark.reject('你似乎没有发送有效的参数呢QAQ, 请重新发送:')
    state[state["_current_key"]] = args[0]
    if state[state["_current_key"]] == '取消':
        await ark.finish('操作已取消')


@ark.handle()
async def handle_first_receive(bot: Bot, event: MessageEvent, state: T_State):
    args = str(event.get_plaintext()).strip().lower().split()
    if not args:
        pass
    elif args and len(args) == 1:
        state['sub_command'] = args[0]
    else:
        await ark.finish('参数错误QAQ')


@ark.got('sub_command', prompt='执行操作?\n')
async def handle_sub_command_args(bot: Bot, event: MessageEvent, state: T_State):
    sub_command = state['sub_command']
    if sub_command in ["更新", 'update']:
        if event.user_id not in [int(x) for x in superusers]:
            await ark.finish('该命令仅超级管理员可用哦')
            return
        result = await ark_data_handler.update()
        await ark.finish(result)
    else:
        for handler in handlers:
            await handler.init(event.user_id)
            if utils.word_in_sentence(sub_command, handler.keyword):
                result = await handler.action(sub_command, event.user_id)
                await ark.finish(result.result)
