from nonebot import on_notice, export
from nonebot.adapters.cqhttp import Bot, PokeNotifyEvent
from nonebot.typing import T_State
import random
from skadi_core.utils.plugin_utils import init_export, init_permission_state
from collections import defaultdict
from typing import Union

__plugin_name__ = '戳一戳 [Hidden]'
__plugin_usage__ = r'''戳一戳就行'''

# Init plugin export
init_export(export(), __plugin_name__, __plugin_usage__)

poke__reply = [
    "你再戳！",
    "？再戳试试？",
    "别戳了别戳了再戳就坏了555",
    "我爪巴爪巴，球球别再戳了",
    "你戳你🐎呢？！",
    "那...那里...那里不能戳...绝对...",
    "(。´・ω・)ん?",
    "有事恁叫我，别天天一个劲戳戳戳！",
    "欸很烦欸！你戳🔨呢",
    "?",
    "再戳一下试试？",
    "???",
    "正在关闭对您的所有服务...关闭成功",
    "啊呜，太舒服刚刚竟然睡着了。什么事？",
    "正在定位您的真实地址...定位成功。轰炸机已起飞",
]


class CountLimiter:
    """
    次数检测工具，检测调用次数是否超过设定值
    """

    def __init__(self, max_count: int):
        self.count = defaultdict(int)
        self.max_count = max_count

    def add(self, key: Union[str, int, float]):
        self.count[key] += 1

    def check(self, key: Union[str, int, float]) -> bool:
        if self.count[key] >= self.max_count:
            self.count[key] = 0
            return True
        return False


_clmt = CountLimiter(3)

poke_ = on_notice(priority=5, block=False, state=init_permission_state(
        name='poke',
        level=10))


@poke_.handle()
async def _poke_(bot: Bot, event: PokeNotifyEvent, state: T_State):
    if event.self_id == event.target_id:
        _clmt.add(event.user_id)
        if _clmt.check(event.user_id) or random.random() < 0.3:
            await poke_.finish(random.choice(poke__reply), at_sender=True)
