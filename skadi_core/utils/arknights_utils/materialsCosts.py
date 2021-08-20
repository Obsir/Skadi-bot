import os

from .initData import InitData
from .utils import text_to_pinyin, remove_punctuation, create_image
from .utils import ARK_GAMEDATA_PATH
import aiofiles
from ..bot_database import DBArknights, Result
from nonebot import logger
from nonebot.adapters.cqhttp import MessageSegment
import asyncio

material_images_source = os.path.join(ARK_GAMEDATA_PATH, 'images', 'materials')
skill_images_source = os.path.join(ARK_GAMEDATA_PATH, 'images', 'skills')


class ArkMaterialCostsHandler:
    def __init__(self):
        self.keywords = []
        self.operator_list = []
        self.operator_map = {}
        self.skill_list = []
        self.skill_map = {}
        self.level_list = {
            '精1': -1, '精英1': -1,
            '精2': -2, '精英2': -2,
            '1级': 1, '等级1': 1,
            '2级': 2, '等级2': 2,
            '3级': 3, '等级3': 3,
            '4级': 4, '等级4': 4,
            '5级': 5, '等级5': 5,
            '6级': 6, '等级6': 6,
            '7级': 7, '等级7': 7,
            '专1': 8, '专精1': 8,
            '专2': 9, '专精2': 9,
            '专3': 10, '专精3': 10
        }
        self.skill_index_list = {
            '1技能': 1, '2技能': 2, '3技能': 3
        }
        self.init_finish = False

    async def init(self):
        if self.init_finish:
            return
        db_ark = DBArknights()
        keywords = [] + ['%s 100 n' % key for key in InitData.voices]

        def append_search_word(text):
            keywords.append('%s 100 n' % text)

        # 初始化专精和等级关键词
        for key in self.level_list:
            append_search_word(text=key)
            self.keywords.append(key)
        for key in self.skill_index_list:
            append_search_word(text=key)
            self.keywords.append(key)

        # 初始化干员名关键词
        _res = await db_ark.get_all_operator()
        if _res.success():
            logger.debug(f'ArkMaterialCostsHandler | 获取全干员 成功')
        else:
            logger.error(f'ArkMaterialCostsHandler | 获取全干员 失败, error: {_res.info}')

        operators = _res.result
        for item in operators:
            name = item.operator_name
            append_search_word(text=name)
            self.operator_list.append(name)
            self.keywords.append(name)

            name = item.operator_en_name.lower()
            append_search_word(text=name)
            self.operator_map[name] = item.operator_name
            self.keywords.append(name)

            name = text_to_pinyin(item.operator_name)
            append_search_word(text=name)
            self.operator_map[name] = item.operator_name
            self.keywords.append(name)

        # 初始化技能关键词
        _res = await db_ark.get_all_operator_skill()
        if _res.success():
            logger.debug(f'ArkMaterialCostsHandler | 获取全干员技能 成功')
        else:
            logger.error(f'ArkMaterialCostsHandler | 获取全干员技能 失败, error: {_res.info}')

        skills = _res.result
        for item in skills:
            name = remove_punctuation(item.skill_name)
            append_search_word(text=name)
            self.skill_map[name] = item.skill_name
            self.keywords.append(name)

            pin_name = text_to_pinyin(name)
            append_search_word(text=pin_name)
            self.skill_map[pin_name] = item.skill_name
            self.keywords.append(pin_name)

        async with aiofiles.open(os.path.join(ARK_GAMEDATA_PATH, 'operators.txt')
                , mode='w', encoding='utf-8') as file:
            await file.write('\n'.join(keywords))

        self.init_finish = True

    @staticmethod
    async def find_repeat_skill_name(name, skill, skill_index):

        text = ''
        db_ark = DBArknights()

        if skill and skill_index == 0:
            _res = await db_ark.get_operator_skill_by_name(skill)
            if _res.success():
                logger.debug(f'ArkMaterialCostsHandler | 获取全干员技能 {skill} 成功')
            else:
                logger.error(f'ArkMaterialCostsHandler | 获取全干员技能 {skill} 失败, error: {_res.info}')
            skill_info = _res.result

            if len(skill_info):
                if name == '' and len(skill_info) > 1:
                    text += '博士，目前存在 %d 个干员拥有【%s】这个技能哦，请用比如「干员一技能专三」这种方式和我描述吧' % (len(skill_info), skill)
                item = skill_info[0]
                if name == '':
                    name = item.operator_name
                    skill_index = item.skill_index
                else:
                    if name == item.operator_name:
                        skill_index = item.skill_index

        return text, name, skill_index

    @staticmethod
    async def check_evolve_costs(name, level) -> Result.AnyResult:
        evolve = {1: '一', 2: '二'}
        db_ark = DBArknights()
        _res = await db_ark.find_operator_evolve_costs(name, level)
        if _res.success():
            logger.debug(f'ArkMaterialCostsHandler | 获取干员 {name} - 精英化{level}阶段材料 成功')
        else:
            logger.error(
                f'ArkMaterialCostsHandler | 获取干员 {name} - 精英化{level}阶段材料 失败, error: {_res.info}, error: {_res.info}')
        result = _res.result

        text = ''
        if len(result):
            text += '博士，这是干员%s精英%s需要的材料清单\n\n' % (name, evolve[level])
            images = []
            material_name = []
            for item in result:
                if item['material_name'] not in material_name:
                    text += '%s%s X %s\n\n' % (' ' * 12, item['material_name'], item['use_number'])
                    images.append(os.path.join(material_images_source, item['material_icon'] + '.png'))
                    material_name.append(item['material_name'])

            icons = []
            for index, item in enumerate(images):
                if os.path.exists(item):
                    icons.append({
                        'path': item,
                        'size': (35, 35),
                        'pos': (5, 26 + index * 34)
                    })

            text = MessageSegment.image(await asyncio.get_event_loop().run_in_executor(None, create_image, text, icons))
        else:
            text += '博士，暂时没有找到相关的档案哦~'

        return Result.AnyResult(error=False, info="", result=text)

    async def check_mastery_costs(self, name, skill, level, skill_index=0) -> Result.AnyResult:
        if not self.init_finish:
            await self.init()
        mastery = {1: '一', 2: '二', 3: '三'}
        db_ark = DBArknights()
        text, name, skill_index = await self.find_repeat_skill_name(name, skill, skill_index)

        if text:
            return text
        _res = await db_ark.find_operator_skill_mastery_costs(name, level, skill_index)
        if _res.success():
            logger.debug(f'ArkMaterialCostsHandler | 获取干员 {name} - 技能专精{level}阶段材料 成功')
        else:
            logger.error(f'ArkMaterialCostsHandler | 获取干员 {name} - 技能专精{level}阶段材料 失败, error: {_res.info}')

        result = _res.result

        if len(result):
            text += '博士，这是干员%s技能专精%s需要的材料清单\n\n' % (name, mastery[level])
            skills = {}
            skill_images = []
            material_images = []
            icons = []

            for item in result:
                skill_name = item['skill_name']
                if skill_name not in skills:
                    skills[skill_name] = []
                    skill_images.append(os.path.join(skill_images_source, item['skill_icon'] + '.png'))

                skills[skill_name].append(item)
            for name in skills:
                text += '%s%s\n\n' % (' ' * 15, name)
                for item in skills[name]:
                    text += '————%s%s X %s\n\n' % (' ' * 15, item['material_name'], item['use_number'])
                    material_images.append(os.path.join(material_images_source, item['material_icon'] + '.png'))

            for index, item in enumerate(skill_images):
                if os.path.exists(item):
                    icons.append({
                        'path': item,
                        'size': (35, 35),
                        'pos': (10, 28 + 136 * index)
                    })

            i, n = 0, 34
            for index, item in enumerate(material_images):
                if index and index % 3 == 0:
                    i += n
                if os.path.exists(item):
                    icons.append({
                        'path': item,
                        'size': (35, 35),
                        'pos': (55, 60 + i)
                    })
                i += n

            text = MessageSegment.image(await asyncio.get_event_loop().run_in_executor(None, create_image, text, icons))
        else:
            text += '博士，没有找到干员%s技能专精%s需要的材料清单' % (name, mastery[level])

        return Result.AnyResult(error=False, info="", result=text)
