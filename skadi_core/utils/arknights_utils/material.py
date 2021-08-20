import os
from .utils import ARK_GAMEDATA_PATH, find_similar_string, create_image
from ..bot_database import DBArknights, Result
import asyncio
from nonebot import logger
import aiofiles
import jieba
from nonebot.adapters.cqhttp import MessageSegment

material_images_source = os.path.join(ARK_GAMEDATA_PATH, 'images', 'materials')
if not os.path.exists(material_images_source):
    os.makedirs(material_images_source)


class ArkMaterialHandler:
    def __init__(self):
        self.init_finish = False

    async def init(self, *args, **kwargs):
        if self.init_finish:
            return
        self.keywords = []
        self.material_list = []
        db_ark = DBArknights()
        _res = await db_ark.get_all_material()
        if _res.success():
            logger.debug(f'ArkMaterialHandler | 初始化获取全材料 成功')
        else:
            logger.error(f'ArkMaterialHandler | 初始化获取全材料 失败')
        materials = _res.result
        for item in materials:
            self.keywords.append('%s 100 n' % item.material_name)
            self.material_list.append(item.material_name)

        async with aiofiles.open(os.path.join(ARK_GAMEDATA_PATH, 'materials.txt'), mode='w', encoding='utf-8') as file:
            await file.write('\n'.join(self.keywords))
        jieba.load_userdict(os.path.join(ARK_GAMEDATA_PATH, 'materials.txt'))
        self.keyword = self.material_list + ['材料']
        self.init_finish = True

    async def action(self, name, *args, **kwargs) -> Result.AnyResult:
        if not self.init_finish:
            await self.init()
        msg_words = sorted(
            jieba.lcut_for_search(name),
            reverse=True,
            key=lambda i: len(i)
        )
        name = ''
        rate = 0
        for item in msg_words:
            n, r = find_similar_string(item, self.material_list, return_rate=True)
            if rate < r:
                name = n
                rate = r
        if not name:
            return Result.AnyResult(error=True, info="", result='博士，没有找到%s的资料呢 >.<' % name)

        return await self.check_material(name)

    async def check_material(self, name):
        db_ark = DBArknights()
        pl = {
            'SOMETIMES': '罕见',
            'OFTEN': '小概率',
            'USUAL': '中概率',
            'ALMOST': '大概率',
            'ALWAYS': '固定'
        }
        ty = {
            'WORKSHOP': ('加工站', '合成'),
            'MANUFACTURE': ('制造站', '生产')
        }

        _res = await db_ark.find_material_made(name)
        made = _res.result
        if _res.success():
            logger.debug(f'ArkMaterialHandler | 获取材料组成 - {name} 成功')
        else:
            logger.error(f'ArkMaterialHandler | 获取材料组成 - {name} 失败')
            return _res

        _res = await db_ark.find_material_source(name, only_main=True)
        source = _res.result
        if _res.success():
            logger.debug(f'ArkMaterialHandler | 获取材料来源 - {name} 成功')
        else:
            logger.error(f'ArkMaterialHandler | 获取材料来源 - {name} 失败')
            return _res

        _res = await db_ark.get_material(name)
        material = _res.result
        if _res.success():
            logger.debug(f'ArkMaterialHandler | 获取材料数据 - {name} 成功')
        else:
            logger.error(f'ArkMaterialHandler | 获取材料数据 - {name} 失败')
            return _res

        text = '博士，为你找到材料【%s】的档案\n\n\n\n\n\n\n' % name
        icons = [
            {
                'path': os.path.join(material_images_source, material.material_icon + '.png'),
                'size': (80, 80),
                'pos': (10, 30)
            }
        ]

        if made or source:
            material_images = []

            if made:
                text += '可在【%s】通过以下配方%s：\n\n' % ty[made[0]['made_type']]
                for item in made:
                    text += '%s%s X %s\n\n' % (' ' * 12, item['material_name'], item['use_number'])
                    material_images.append(os.path.join(material_images_source, item['material_icon'] + '.png'))
            if source:
                text += '可在以下非活动地图掉落：\n\n'
                source = {item['stage_code']: item for item in source}
                for code in sorted(source):
                    stage = source[code]
                    text += '【%s %s】 %s\n' % (stage['stage_code'], stage['stage_name'], pl[stage['source_rate']])

            for index, item in enumerate(material_images):
                if os.path.exists(item):
                    icons.append({
                        'path': item,
                        'size': (35, 35),
                        'pos': (5, 145 + index * 34)
                    })

        text += '\n' + material.material_desc
        result = await asyncio.get_event_loop().run_in_executor(None, create_image, text, icons)
        return Result.AnyResult(error=False, info="", result=MessageSegment.image(result))
