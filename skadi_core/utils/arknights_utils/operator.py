from nonebot import logger
from .material import ArkMaterialHandler
from .materialsCosts import ArkMaterialCostsHandler
from .operatorInfo import ArkOperatorInfoHandler
import jieba
from .utils import remove_punctuation, chinese_to_digits, word_in_sentence
from .initData import InitData
from ..bot_database import DBArknights, Result
import copy
import re
import os
from .utils import ARK_GAMEDATA_PATH


class LoopBreak(Exception):
    def __init__(self, name=None, value=None):
        self.name = name
        self.value = value

    def __str__(self):
        return '%s = %s' % (self.name, self.value)


class ArkOperatorHandler:
    def __init__(self):
        self.ark_operator_info_handler = ArkOperatorInfoHandler()
        self.ark_material_costs_handler = ArkMaterialCostsHandler()
        self.ark_material_handler = ArkMaterialHandler()

        self.init_finish = False

    async def init(self, *args, **kwargs):
        if self.init_finish:
            return
        await self.ark_material_costs_handler.init()
        await self.ark_material_handler.init()
        await self.ark_operator_info_handler.init()
        jieba.load_userdict(os.path.join(ARK_GAMEDATA_PATH, 'operators.txt'))
        jieba.load_userdict(os.path.join(ARK_GAMEDATA_PATH, 'stories.txt'))
        jieba.load_userdict(os.path.join(ARK_GAMEDATA_PATH, 'skins.txt'))
        self.keyword = InitData.voices + self.ark_material_costs_handler.keywords + self.ark_operator_info_handler.skins_keywords
        self.stories_title = list(self.ark_operator_info_handler.stories_title.keys()) + [i for k, i in
                                                                                          self.ark_operator_info_handler.stories_title.items()]

        self.init_finish = True

    async def action(self, data, *args, **kwargs) -> Result.AnyResult:
        if not self.init_finish:
            await self.init()
        db_ark = DBArknights()
        message = chinese_to_digits(data)
        message_ori = remove_punctuation(data)

        words = jieba.lcut(
            message.lower().replace(' ', '')
        )
        words += jieba.lcut(
            message_ori.lower().replace(' ', '')
        )
        words = sorted(words, reverse=True, key=lambda i: len(i))

        operator_id = None
        info = {
            'name': '',
            'level': 0,
            'skill': '',
            'skin_key': '',
            'voice_key': '',
            'skill_index': 0,
            'stories_key': ''
        }
        info_source = {
            'name': [self.ark_material_costs_handler.operator_map, self.ark_material_costs_handler.operator_list],
            'level': [self.ark_material_costs_handler.level_list],
            'skill': [self.ark_material_costs_handler.skill_map],
            'skill_index': [self.ark_material_costs_handler.skill_index_list],
            'skin_key': [self.ark_operator_info_handler.skins_keywords],
            'voice_key': [InitData.voices],
            'stories_key': [self.stories_title]
        }
        info_key = list(info.keys())

        for item in words:
            try:
                # ?????? info_key ????????? info_source ????????????????????????
                for name in copy.deepcopy(info_key):
                    for source in info_source[name]:

                        # info_source ????????????????????????????????????
                        if item in source:
                            if type(source) is dict:
                                info[name] = source[item]
                            if type(source) is list:
                                info[name] = item

                            if name == 'name':
                                _res = await db_ark.get_operator_id(operator_name=info[name])
                                operator_id = _res.result
                            # ?????????????????????????????? key??????????????????????????? key ?????????
                            info_key.remove(name)

                            raise LoopBreak(name=name, value=info[name])
            except LoopBreak as value:
                # print(value)
                continue

        # todo ????????????
        if info['skin_key']:
            return await self.ark_operator_info_handler.find_skin(info['skin_key'])

        if info['name'] == '' and info['skill'] == '':
            return Result.AnyResult(error=False, info='', result='?????????????????????????????????????????????')

        if info['level'] != 0:
            if info['level'] < 0:
                # todo ???????????????
                info['level'] = abs(info['level'])
                result = await self.ark_material_costs_handler.check_evolve_costs(info['name'], info['level'])
            else:
                if info['level'] >= 8 and '??????' in message:
                    # todo ????????????
                    info['level'] -= 7
                    result = await self.ark_material_costs_handler.check_mastery_costs(info['name'], info['skill'],
                                                                                       info['level'],
                                                                                       skill_index=info['skill_index'])
                else:
                    # todo ????????????
                    result = await self.ark_operator_info_handler.get_skill_data(info['name'], info['skill'],
                                                                                 info['level'],
                                                                                 skill_index=info['skill_index'])
            return result

        if info['name']:
            # todo ????????????
            if info['stories_key']:
                _res = await db_ark.find_operator_stories(info['name'], info['stories_key'])
                story = _res.result
                if story:
                    text = '?????????????????????%s??????%s?????????\n\n' % (info['name'], info['stories_key'])
                    return Result.AnyResult(error=False, info='', result=text + story['story_text'])
                else:
                    return Result.AnyResult(error=False, info='',
                                            result='???????????????????????????%s??????%s?????????' % (info['name'], info['stories_key']))

            # todo ????????????
            if info['voice_key']:
                return await self.ark_operator_info_handler.find_voice(info['name'], info['voice_key'])

            # todo ????????????
            if word_in_sentence(message, ['??????', '??????']):
                if operator_id not in self.ark_operator_info_handler.skins_table:
                    _res = await db_ark.get_operator_id(operator_name='?????????')
                    amiya_id = _res.result
                    no_skin = '???????????????%s??????????????????????????????????????????%d???????????? ^.^???' % (
                        info['name'], len(self.ark_operator_info_handler.skins_table[amiya_id]))
                    return Result.AnyResult(error=False, info='', result=no_skin)

                skin_list = self.ark_operator_info_handler.skins_table[operator_id]

                r = re.search(re.compile(r'???(\d+)?????????'), message)
                if r:
                    index = abs(int(r.group(1))) - 1
                    if index >= len(skin_list):
                        index = len(skin_list) - 1

                    return await self.ark_operator_info_handler.find_skin(skin_list[index]['skin_name'])
                else:
                    text = '???????????????????????????%s???????????????\n\n' % info['name']

                    for index, item in enumerate(skin_list):
                        idx = ('' if index + 1 >= 10 else '0') + str(index + 1)
                        text += '%s [ %s - %s ] %s\n' % (idx, item['skin_group'], item['skin_name'], item['skin_usage'])

                    text += '\n?????????????????????%s??? N ???????????????????????????' % info['name']

                    return Result.AnyResult(error=False, info='', result=text)

            if word_in_sentence(message, ['??????', '??????']):
                return Result.AnyResult(error=False, info='', result='?????????????????????????????????????????????')

            if word_in_sentence(message, ['??????']):
                return Result.AnyResult(error=False, info='', result='?????????????????????????????????????????????')

            if info['skill'] or info['skill_index']:
                return Result.AnyResult(error=False, info='', result='?????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????????')

            return await self.ark_operator_info_handler.get_detail_info(info['name'])
