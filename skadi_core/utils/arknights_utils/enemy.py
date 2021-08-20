import re
from nonebot import logger
from nonebot.adapters.cqhttp import MessageSegment
from .game_data import ArkGameData
from .utils import *
from ..bot_database import Result
import asyncio

class ArkEnemyHandler:
    def __init__(self):
        self.init_finish = False

    async def init(self, *args, **kwargs):
        if self.init_finish:
            return
        # TODO async init
        self.function_id = 'checkEnemy'
        self.keyword = ['敌人', '敌方']
        self.enemies = None
        try:
            self.enemies = ArkGameData().init_enemies()
        except Exception as e:
            logger.error(f"ArkEnemyHandler | {e.__repr__()} 请更新明日方舟数据")
        self.init_finish = True

    async def action(self, enemy_name, *args, **kwargs) -> Result.AnyResult:
        if not self.init_finish:
            await self.init()

        for reg in ['敌人(.*)', '敌方(.*)']:
            r = re.search(re.compile(reg), enemy_name)
            if r:
                enemy_name = r.group(1)
                result = await self.find_enemy(enemy_name)
                if result.success():
                    return result

        return Result.AnyResult(error=True, info="无数据", result='博士，没有找到%s的资料呢' % enemy_name)

    async def find_enemy(self, enemy_name):
        name = find_similar_string(enemy_name, list(self.enemies.keys()))
        if name:
            try:
                data = self.enemies[name]['info']
                detail = self.enemies[name]['data']

                text = '博士，这是找到的敌方档案\n\n\n\n\n\n\n'
                text += '【%s】\n\n' % name
                text += '%s\n\n' % data['description']
                text += '[能力]\n%s\n\n' % remove_xml_tag(data['ability'] or '无')
                text += '[属性]\n耐久 %s | 攻击力 %s | 防御力 %s | 法术抗性 %s\n' % \
                        (data['endure'],
                         data['attack'],
                         data['defence'],
                         data['resistance'])

                key_map = {
                    'attributes.maxHp': {'title': '生命值', 'value': ''},
                    'attributes.atk': {'title': '攻击力', 'value': ''},
                    'attributes.def': {'title': '物理防御', 'value': ''},
                    'attributes.magicResistance': {'title': '魔法抗性', 'value': ''},
                    'attributes.moveSpeed': {'title': '移动速度', 'value': ''},
                    'attributes.baseAttackTime': {'title': '攻击间隔', 'value': ''},
                    'attributes.hpRecoveryPerSec': {'title': '生命回复/秒', 'value': ''},
                    'attributes.massLevel': {'title': '重量', 'value': ''},
                    'rangeRadius': {'title': '攻击距离/格', 'value': ''},
                    'lifePointReduce': {'title': '进点损失', 'value': ''}
                }

                for item in detail:
                    text += '\n[等级 %s 数值]\n' % (item['level'] + 1)
                    detail_data = item['enemyData']
                    key_index = 0
                    for key in key_map:
                        defined, value = self.get_value(key, detail_data)
                        if defined:
                            key_map[key]['value'] = value
                        else:
                            value = key_map[key]['value']

                        text += '%s：%s%s' % (key_map[key]['title'], value, '    ' if key_index % 2 == 0 else '\n')
                        key_index += 1
                    if detail_data['skills']:
                        text += '技能冷却时间：\n'
                        for sk in detail_data['skills']:
                            sk_info = (sk['prefabKey'], sk['initCooldown'], sk['cooldown'])
                            text += '    - [%s]\n    -- 初始冷却 %ss，后续冷却 %ss\n' % sk_info

                icons = [
                    {

                        'path': os.path.join(ARK_GAMEDATA_PATH, 'images', 'enemy', '%s.png' % data['enemyId']),
                        'size': (80, 80),
                        'pos': (10, 30)
                    }
                ]
                result = await asyncio.get_event_loop().run_in_executor(None, create_image, text, icons)
                return Result.AnyResult(error=False, info="", result=MessageSegment.image(result))
            except Exception as e:
                logger.error(f'ArkEnemyHandler | error: {e}')
                return Result.AnyResult(error=True, info=e.__repr__(), result=None)
        else:
            return Result.AnyResult(error=True, info="ArkEnemyHandler | 敌人名称无匹配", result=None)

    @staticmethod
    def get_value(key, source):
        for item in key.split('.'):
            if item in source:
                source = source[item]
        return source['m_defined'], source['m_value']
