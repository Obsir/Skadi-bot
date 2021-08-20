import os
import re
from .utils import ARK_GAMEDATA_PATH, chinese_to_digits, split_text, create_image, picpath2b64
from nonebot.adapters.cqhttp import MessageSegment
from ..bot_database import DBArknights, Result
from .initData import InitData
from .materialsCosts import ArkMaterialCostsHandler, skill_images_source
from nonebot import logger
import aiofiles
import asyncio

avatars_images_source = os.path.join(ARK_GAMEDATA_PATH, 'images', 'avatars')
if not os.path.exists(avatars_images_source):
    os.makedirs(avatars_images_source)


class ArkOperatorInfoHandler:
    def __init__(self):
        self.skins_table = {}
        self.skins_keywords = []
        self.stories_title = {}

        self.init_finish = False

    async def init(self):
        if self.init_finish:
            return
        await self.init_skins_table()
        await self.init_stories_titles()
        self.init_finish = True

    async def init_skins_table(self):
        db_ark = DBArknights()
        _res = await db_ark.get_all_skins()
        if _res.success():
            logger.debug(f'ArkOperatorInfoHandler | 初始化获取全干员皮肤 成功')
        else:
            logger.error(f'ArkOperatorInfoHandler | 初始化获取全干员皮肤 失败, error: {_res.info}')
        skins_data = _res.result
        skins_table = {}
        skins_keywords = []

        for item in skins_data:
            if item.operator_id not in skins_table:
                skins_table[item.operator_id] = []
            skins_table[item.operator_id].append(item)
            skins_keywords.append(item.skin_name)

        self.skins_table = skins_table
        self.skins_keywords = skins_keywords

        async with aiofiles.open(os.path.join(ARK_GAMEDATA_PATH, 'skins.txt'), mode='w', encoding='utf-8') as file:
            await file.write('\n'.join([n + ' 100 n' for n in skins_keywords]))

    async def init_stories_titles(self):
        db_ark = DBArknights()
        _res = await db_ark.get_all_stories_title()
        if _res.success():
            logger.debug(f'ArkOperatorInfoHandler | 初始化获取全干员简历 成功')
        else:
            logger.error(f'ArkOperatorInfoHandler | 初始化获取全干员简历 失败, error: {_res.info}')
        stories_titles = _res.result
        self.stories_title = {chinese_to_digits(item): item for item in stories_titles}

        stories_keyword = []
        for index, item in self.stories_title.items():
            item = re.compile(r'？+', re.S).sub('', item)
            if item:
                stories_keyword.append(item + ' 100 n')

        async with aiofiles.open(os.path.join(ARK_GAMEDATA_PATH, 'stories.txt'), mode='w', encoding='utf-8') as file:
            await file.write('\n'.join(stories_keyword))

    async def get_detail_info(self, name) -> Result.AnyResult:
        if not self.init_finish:
            await self.init()
        db_ark = DBArknights()
        _res = await db_ark.get_operator_id(operator_name=name)
        if _res.success():
            logger.debug(f'ArkOperatorInfoHandler | 获取干员 {name} ID 成功')
        else:
            logger.error(f'ArkOperatorInfoHandler | 获取干员 {name} ID 失败, error: {_res.info}')

        operator_id = _res.result

        _res = await db_ark.find_operator_all_detail(operator_id)
        if _res.success():
            logger.debug(f'ArkOperatorInfoHandler | 获取干员 {name} 详细信息 成功')
        else:
            logger.error(f'ArkOperatorInfoHandler | 获取干员 {name} 详细信息 失败, error: {_res.info}')

        base, detail, talents, potential, building_skill = _res.result

        text = '博士，为您找到以下干员资料\n\n\n\n\n\n\n'
        icons = [
            {
                'path': os.path.join(avatars_images_source, base.operator_avatar + '.png'),
                'size': (80, 80),
                'pos': (10, 30)
            }
        ]

        text += '%s [%s]\n%s\n\n' % (base.operator_name,
                                     base.operator_en_name,
                                     '★' * base.operator_rarity)

        text += '【%s干员】\n%s\n\n' % (InitData.class_type[base.operator_class], detail.operator_desc)
        text += '%s\n -- 「%s」\n\n' % (detail.operator_usage, detail.operator_quote)

        text += '【信物】\n%s\n\n' % detail.operator_token if detail.operator_token else ''

        text += '【精英%s级属性】\n' % detail.max_level
        text += ' -- 生命值：%s\n' % detail.max_hp
        text += ' -- 攻击力：%s\n' % detail.attack
        text += ' -- 防御力：%s\n' % detail.defense
        text += ' -- 魔法抗性：%s\n' % detail.magic_resistance
        text += ' -- 费用：%s\n' % detail.cost
        text += ' -- 阻挡数：%s\n' % detail.block_count
        text += ' -- 基础攻击间隔：%ss\n' % detail.attack_time
        text += ' -- 再部署时间：%ss\n\n' % detail.respawn_time

        talents_text = ''
        for item in talents:
            talents_text += '<%s>\n%s\n' % (item.talents_name, item.talents_desc)
        text += ('【天赋】\n%s\n' % talents_text) if talents_text else ''

        potential_text = ''
        for item in potential:
            potential_text += '[%s] %s\n' % (InitData.potential_rank[item.potential_rank], item.potential_desc)
        text += ('【潜能】\n%s\n' % potential_text) if potential_text else ''

        building_text = ''
        for item in building_skill:
            building_text += '<%s>[精英%s解锁]\n%s\n' % (item.bs_name, item.bs_unlocked, item.bs_desc)
        text += ('【基建技能】\n%s\n' % building_text) if building_text else ''

        _res = await db_ark.find_operator_skill_description(name, level=7)
        if _res.success():
            logger.debug(f'ArkOperatorInfoHandler | 获取干员 {name} 技能描述 成功')
        else:
            logger.error(f'ArkOperatorInfoHandler | 获取干员 {name} 技能描述 失败, error: {_res.info}')
        result = _res.result
        if result:
            text += '【7级技能】\n\n'
            top = len(split_text(text)) * 17 + 11

            content, skill_icons = self.load_skill_content(result, top)

            text += content
            icons += skill_icons
            result = MessageSegment.image(
                await asyncio.get_event_loop().run_in_executor(None, create_image, text, icons))
        return Result.AnyResult(error=False, info="", result=result)

    async def get_skill_data(self, name, skill, level, skill_index=0) -> Result.AnyResult:
        if not self.init_finish:
            await self.init()
        db_ark = DBArknights()
        text, name, skill_index = await ArkMaterialCostsHandler.find_repeat_skill_name(name, skill, skill_index)

        if text:
            return text

        _res = await db_ark.find_operator_skill_description(name, level, skill_index)
        if _res.success():
            logger.debug(f'ArkOperatorInfoHandler | 获取干员 {name} 技能数据 成功')
        else:
            logger.error(f'ArkOperatorInfoHandler | 获取干员 {name} 技能数据 失败, error: {_res.info}')
        result = _res.result

        if len(result):
            text += '博士，这是干员%s技能%s的数据\n\n' % (name, InitData.skill_level[level])

            content, icons = self.load_skill_content(result, 28)

            text += content
            result = MessageSegment.image(
                await asyncio.get_event_loop().run_in_executor(None, create_image, text, icons))
            return Result.AnyResult(error=False, info="", result=result)
        else:
            return Result.AnyResult(error=False, info="",
                                    result='博士，没有找到干员%s技能%s的数据' % (name, InitData.skill_level[level]))

    @staticmethod
    def load_skill_content(result, position):
        text = ''
        skills = {}
        skill_images = []
        icons = []

        y = position
        yl = []

        for item in result:
            skill_name = item['skill_name']
            if skill_name not in skills:
                skills[skill_name] = []
                skill_images.append(os.path.join(skill_images_source, item['skill_icon'] + '.png'))
            skills[skill_name].append(item)

        for name in skills:
            text += '%s%s\n\n' % (' ' * 15, name)
            content = ''
            index = list(skills.keys()).index(name)

            y += 51 if index else 0
            yl.append(y)

            for item in skills[name]:
                content += '%s / %s' % (InitData.sp_type[item['sp_type']], InitData.skill_type[item['skill_type']])
                content += '%sSP：%s / %s\n' % (' ' * 5, item['sp_init'], item['sp_cost'])
                if item['duration'] > 0:
                    content += '持续时间：%ss\n' % item['duration']
                content += '%s\n\n' % item['description']
                text += content

                y += len(split_text(content)) * 17

        for index, item in enumerate(skill_images):
            if os.path.exists(item):
                icons.append({
                    'path': item,
                    'size': (35, 35),
                    'pos': (10, yl[index])
                })

        return text, icons

    @staticmethod
    async def find_skin(skin_name) -> Result.AnyResult:
        db_ark = DBArknights()
        _res = await db_ark.find_operator_skin(skin_name)
        if _res.success():
            logger.debug(f'ArkOperatorInfoHandler | 获取干员皮肤 {skin_name} 成功')
        else:
            logger.error(f'ArkOperatorInfoHandler | 获取干员皮肤 {skin_name} 失败, error: {_res.info}')

        skin = _res.result
        if skin:
            _res = await db_ark.get_operator_by_id(skin.operator_id)
            if _res.success():
                logger.debug(f'ArkOperatorInfoHandler | 获取干员皮肤 {_res.result.operator_name} 信息 成功')
            else:
                logger.error(f'ArkOperatorInfoHandler | 获取皮肤 {skin_name} 信息 失败, error: {_res.info}')
            opt = _res.result

            text = '博士，为您找到干员%s的皮肤档案：\n\n【%s - %s】\n\n' % (opt.operator_name, skin.skin_group, skin.skin_name)
            text += skin.skin_source + '\n\n'
            text += skin.skin_usage + '\n'
            text += skin.skin_content + '\n\n'
            text += ' -- ' + skin.skin_desc

            pic = os.path.join(ARK_GAMEDATA_PATH, 'images', 'picture', '%s.png' % skin.skin_image)

            if os.path.exists(pic):
                text = MessageSegment.image(picpath2b64(pic))
            else:
                text = '暂时无法获取到立绘图片'

            return Result.AnyResult(error=False, info='', result=text)

    @staticmethod
    async def find_voice(name, voice) -> Result.AnyResult:
        db_ark = DBArknights()
        _res = await db_ark.find_operator_voice(name, voice)
        if _res.success():
            logger.debug(f'ArkOperatorInfoHandler | 获取干员语音 {name} 成功')
        else:
            logger.error(f'ArkOperatorInfoHandler | 获取干员语音 {name} 失败, error: {_res.info}')
        result = _res.result
        if result:
            text = '博士，为您找到干员%s的语音档案：\n\n【%s】\n%s' % (name, voice, result['voice_text'])
            return Result.AnyResult(error=False, info='', result=text)
        return Result.AnyResult(error=False, info='', result='抱歉博士，没有找到干员%s%s相关的语音档案' % (name, voice))
