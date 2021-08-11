from nonebot import logger, get_driver
import os
import json
from .utils import *
from ..plugin_utils import HttpFetcher
import re
import aiofiles
from .builder import Operator, OperatorTags
from ..bot_database import DBArknights

global_config = get_driver().config
ARK_GAMEDATA_PATH = global_config.ark_gamedata_path


class ArkGameData:
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) '
                      'AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1'
    }
    GITHUB_SOURCE = 'https://cdn.jsdelivr.net/gh/Kengxxiao/ArknightsGameData@master/zh_CN/gamedata'
    RESOURCE = [
        'levels/enemydata/enemy_database',
        'excel/enemy_handbook_table',
        'excel/handbook_info_table',
        'excel/character_table',
        'excel/char_meta_table',
        'excel/charword_table',
        'excel/building_data',
        'excel/gacha_table',
        'excel/stage_table',
        'excel/skill_table',
        'excel/skin_table',
        'excel/item_table'
    ]
    PICS_SOURCE = 'https://andata.somedata.top/dataX'
    RESOURCE_PATH = os.path.join(ARK_GAMEDATA_PATH, 'data')
    PICS_PATH = os.path.join(ARK_GAMEDATA_PATH, 'images')
    if not os.path.exists(RESOURCE_PATH):
        os.makedirs(RESOURCE_PATH)
    if not os.path.exists(PICS_PATH):
        os.makedirs(PICS_PATH)

    def __init__(self):
        pass

    def get_recruit_operators(self):
        recruit_detail = remove_xml_tag(get_json_data('gacha_table')['recruitDetail'])
        recruit_group = re.findall(r'★\\n(.*)', recruit_detail)
        recruit_operators = []

        for item in recruit_group:
            recruit_operators += item.replace(' ', '').split('/')

        return recruit_operators

    async def init_operator_gacha_config(self):
        db_ark = DBArknights()
        _res = await db_ark.delete_gacha_config_and_pool()
        if _res.success():
            logger.debug(f'ArkGameData | 重置卡池配置和信息 - 成功')
        else:
            logger.error(f'ArkGameData | 重置卡池配置和信息 - 失败, error: {_res.info}')

        for operator_pool in operator_pool_list:
            _res = await db_ark.add_operator_pool(**operator_pool)
            if _res.success():
                logger.debug(f'ArkGameData | 更新卡池 - {operator_pool["pool_name"]} 成功')
            else:
                logger.error(
                    f'ArkGameData | 更新卡池 - {operator_pool["pool_name"]} 失败, error: {_res.info}')

        for operator_gacha_config in operator_gacha_config_list:
            _res = await db_ark.add_operator_gacha_config(**operator_gacha_config)
            if _res.success():
                logger.debug(f'ArkGameData | 更新卡池配置 - {operator_gacha_config["operator_name"]} 成功')
            else:
                logger.error(
                    f'ArkGameData | 更新卡池 - {operator_gacha_config["operator_name"]} 失败, error: {_res.info}')

    def init_operators(self):
        logger.debug('ArkGameData | 初始化全干员数据')

        time_rec = TimeRecord()
        recruit_operators = self.get_recruit_operators()
        operators_data = get_json_data('character_table')
        voice_data = get_json_data('charword_table')
        skins_data = get_json_data('skin_table')['charSkins']

        operators = []
        voice_map = {}
        skins_map = {}

        map_data = (
            (voice_data, voice_map),
            (skins_data, skins_map)
        )

        for map_item in map_data:
            for n, item in map_item[0].items():
                char_id = item['charId']
                if char_id not in map_item[1]:
                    map_item[1][char_id] = []

                map_item[1][char_id].append(item)

        for code, item in operators_data.items():
            if item['profession'] not in Config.classes:
                continue

            operators.append(
                Operator(
                    code=code,
                    data=item,
                    voice_list=voice_map[code] if code in voice_map else [],
                    skins_list=skins_map[code] if code in skins_map else [],
                    recruit=item['name'] in recruit_operators
                )
            )

        logger.debug('ArkGameData | 全干员数据更新耗时 %s ms' % time_rec.rec(millisecond=True))
        return operators

    def init_enemies(self):
        enemies_info = get_json_data('enemy_handbook_table')
        enemies_data = get_json_data('enemy_database')['enemies']

        data = {}
        for item in enemies_data:
            if item['Key'] in enemies_info:
                info = enemies_info[item['Key']]
                data[info['name']] = {
                    'info': info,
                    'data': item['Value']
                }

        return data

    @staticmethod
    async def save_operator_data(operator):
        rarity = operator.rarity
        time_rec = TimeRecord()
        db_ark = DBArknights()
        _res = await db_ark.get_operator_gacha_config()
        limit = _res.result
        _res = await db_ark.get_operator_gacha_config(group='unavailable')
        unavailable = _res.result
        # todo 保存基础信息
        new_operator = {
            'operator_no': operator.id,
            'operator_name': operator.name,
            'operator_en_name': operator.en_name,
            'operator_rarity': rarity,
            'operator_avatar': operator.id,
            'operator_class': operator.classes_code,
            'available': 1 if rarity >= 2 and operator.name not in unavailable else 0,
            'in_limit': 1 if operator.name in limit else 0
        }
        _res = await db_ark.add_operator(**new_operator)
        if _res.success():
            logger.debug(f'ArkGameData | 更新干员 - {operator.name} 成功')
        else:
            logger.error(f'ArkGameData | 更新干员 - {operator.name} 失败, error: {_res.info}')

        # todo 保存公招 Tags 信息
        if operator.recruit:
            operator_tags = OperatorTags(operator.name, rarity)
            operator_tags.append(operator.classes)
            operator_tags.append(operator.type)

            if str(rarity) in Config.high_star:
                operator_tags.append(Config.high_star[str(rarity)])

            for tag in operator.tags:
                operator_tags.append(tag)

            for new_tag in operator_tags.tags:
                _res = await db_ark.add_operator_tags_relation(**new_tag)
                if _res.success():
                    logger.debug(f'ArkGameData | 更新干员 - {operator.name} - 公招信息 - {new_tag["operator_tags"]} 成功')
                else:
                    logger.error(
                        f'ArkGameData | 更新干员 - {operator.name} - 公招信息 - {new_tag["operator_tags"]} 失败, error: {_res.info}')

        # todo 保存详细资料
        operator_result = await db_ark.get_operator_id(operator_no=operator.id)
        if operator_result.success():
            logger.debug(f'ArkGameData | 获取干员ID - {operator.name} 成功')
        else:
            logger.error(f'ArkGameData | 获取干员ID - {operator.name} 失败, error: {operator_result.info}')
        operator_id = operator_result.result
        skins = operator.skins(operator_id)
        detail = operator.detail(operator_id)
        voices = operator.voices(operator_id)
        stories = operator.stories(operator_id)
        talents = operator.talents(operator_id)
        potentials = operator.potential(operator_id)
        evolve_costs = operator.evolve_costs(operator_id)
        building_skills = operator.building_skills(operator_id)
        skills, skills_id, skills_cost, skills_desc = operator.skills(operator_id)

        _res = await db_ark.add_operator_detail(**detail)
        if _res.success():
            logger.debug(f'ArkGameData | 更新干员 - {operator.name} - 详细信息 成功')
        else:
            logger.error(
                f'ArkGameData | 更新干员 - {operator.name} - 详细信息 失败, error: {_res.info}')

        if skins:
            for skin in skins:
                _res = await db_ark.add_operator_skin(**skin)
                if _res.success():
                    logger.debug(f'ArkGameData | 更新干员 - {operator.name} - 皮肤数据 {skin["skin_name"]} 成功')
                else:
                    logger.error(
                        f'ArkGameData | 更新干员 - {operator.name} - 皮肤数据 {skin["skin_name"]} 失败, error: {_res.info}')
        if voices:
            for voice in voices:
                _res = await db_ark.add_operator_voice(**voice)
                if _res.success():
                    logger.debug(f'ArkGameData | 更新干员 - {operator.name} - 语音信息 {voice["voice_title"]} 成功')
                else:
                    logger.error(
                        f'ArkGameData | 更新干员 - {operator.name} - 语音信息 {voice["voice_title"]} 失败, error: {_res.info}')
        if stories:
            for story in stories:
                _res = await db_ark.add_operator_story(**story)
                if _res.success():
                    logger.debug(f'ArkGameData | 更新干员 - {operator.name} - 干员背景 {story["story_title"]} 成功')
                else:
                    logger.error(
                        f'ArkGameData | 更新干员 - {operator.name} - 干员背景 {story["story_title"]} 失败, error: {_res.info}')
        if talents:
            for talent in talents:
                _res = await db_ark.add_operator_talent(**talent)
                if _res.success():
                    logger.debug(f'ArkGameData | 更新干员 - {operator.name} - 干员天赋 {talent["talents_name"]} 成功')
                else:
                    logger.error(
                        f'ArkGameData | 更新干员 - {operator.name} - 干员天赋 {talent["talents_name"]} 失败, error: {_res.info}')
        if potentials:
            for potential in potentials:
                _res = await db_ark.add_operator_potential(**potential)
                if _res.success():
                    logger.debug(f'ArkGameData | 更新干员 - {operator.name} - 干员潜能 {potential["potential_rank"]} 成功')
                else:
                    logger.error(
                        f'ArkGameData | 更新干员 - {operator.name} - 干员潜能 {potential["potential_rank"]} 失败, error: {_res.info}')
        if evolve_costs:
            for evolve_cost in evolve_costs:
                _res = await db_ark.add_operator_evolve_cost(**evolve_cost)
                if _res.success():
                    logger.debug(f'ArkGameData | 更新干员 - {operator.name} - 干员晋升 {evolve_cost["evolve_level"]} 成功')
                else:
                    logger.error(
                        f'ArkGameData | 更新干员 - {operator.name} - 干员晋升 {evolve_cost["evolve_level"]} 失败, error: {_res.info}')
        if building_skills:
            for building_skill in building_skills:
                _res = await db_ark.add_operator_building_skill(**building_skill)
                if _res.success():
                    logger.debug(f'ArkGameData | 更新干员 - {operator.name} - 基建技能 {building_skill["bs_name"]} 成功')
                else:
                    logger.error(
                        f'ArkGameData | 更新干员 - {operator.name} - 基建技能 {building_skill["bs_name"]} 失败, error: {_res.info}')

        if skills:
            for skill in skills:
                _res = await db_ark.add_operator_skill(**skill)
                if _res.success():
                    logger.debug(f'ArkGameData | 更新干员 - {operator.name} - 干员技能 {skill["skill_name"]} 成功')
                else:
                    logger.error(
                        f'ArkGameData | 更新干员 - {operator.name} - 干员技能 {skill["skill_name"]} 失败, error: {_res.info}')

        skills_dict = {}
        for no in skills_id:
            _res = await db_ark.get_skill_id(no, operator_id)
            if _res.success():
                logger.debug(f'ArkGameData | 查询干员 - {operator.name} - 干员技能ID {no} 成功')
                skills_dict[no] = _res.result
            else:
                logger.error(
                    f'ArkGameData | 更新干员 - {operator.name} - 干员技能ID {no} 失败, error: {_res.info}')

        task_list = [
            (skills_cost, db_ark.add_operator_skill_mastery_cost),
            (skills_desc, db_ark.add_operator_skill_description)
        ]
        for task in task_list:
            save_list = []
            for sk_no, sk_list in task[0].items():
                for item in sk_list:
                    item['skill_id'] = skills_dict[sk_no]
                    save_list.append(item)
            if save_list:
                for data in save_list:
                    _res = await task[1](**data)
                    if _res.success():
                        logger.debug(f'ArkGameData | 更新干员 - {operator.name} - 干员技能升级和描述 成功')
                    else:
                        logger.error(
                            f'ArkGameData | 更新干员 - {operator.name} - 干员技能升级和描述 失败, error: {_res.info}')

        logger.debug(f'ArkGameData | 更新干员 - {operator.name} 耗时 {time_rec.rec(millisecond=True)} ms')

    def get_json_data(self, name):
        path = '%s/%s.json' % (self.RESOURCE_PATH, name)
        with open(path, mode='r', encoding='utf-8') as src:
            return json.load(src)

    async def get_pic(self, name, _type, _param=''):
        url = '%s/%s.png%s' % (self.PICS_SOURCE, name, _param)
        dir_path = '%s/%s' % (self.PICS_PATH, _type)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        path = '%s/%s.png' % (dir_path, name.split('/')[-1])
        fetcher = HttpFetcher(timeout=30, flag='arknights_game_data', headers=self.HEADERS)
        if os.path.exists(path) is False:
            data = await fetcher.get_bytes(url)
            if data.success():
                async with aiofiles.open(path, mode='wb') as _pic:
                    await _pic.write(data.result)
                logger.debug(f'ArkGameData | 资源下载成功: [{name}]')
                return True
            else:
                logger.error(f'ArkGameData | 资源下载失败: [{name}], error: {data.info}')
                return False
        else:
            logger.error(f'ArkGameData | 资源已存在: [{name}]')
            return True

    async def save_operator_photo(self, operators=None):
        if operators is None:
            operators = self.init_operators()

        logger.debug('ArkGameData | 开始下载干员图片资源')
        avatars_count = 0
        photo_count = 0
        skills_count = 0
        skills_total = 0
        skins_count = 0
        skins_total = 0
        for operator in operators:
            logger.debug('ArkGameData | 正在下载干员 [%s] 图片资源' % operator.name)

            logger.debug('ArkGameData | 正在下载干员 [%s] 图片资源 - 头像' % operator.name)
            res = await self.get_pic('char/profile/' + operator.id, 'avatars')
            avatars_count += 1 if res else 0

            logger.debug('ArkGameData | 正在下载干员 [%s] 图片资源 - 半身照' % operator.name)
            res = await self.get_pic('char/halfPic/%s_1' % operator.id, 'photo', '?x-oss-process=style/small-test')
            photo_count += 1 if res else 0

            skills_list = operator.skills(None)[0]
            skills_total += len(skills_list)
            for skill in skills_list:
                logger.debug(f'ArkGameData | 正在下载干员 [{operator.name}] 图片资源 - 技能图标 [{skill["skill_name"]}]')
                res = await self.get_pic('skills/pics/' + skill['skill_icon'], 'skills')
                skills_count += 1 if res else 0

            skins_list = operator.skins(None)
            skins_total += len(skins_list)
            for skin in skins_list:
                logger.debug(
                    f'ArkGameData | 正在下载干员 [{operator.name}] 图片资源 - 立绘 [{skin["skin_group"]}][{skin["skin_name"]}]')
                res = await self.get_pic('char/set/' + skin['skin_image'], 'picture')
                skins_count += 1 if res else 0

        logger.debug('ArkGameData | 干员图片资源下载完成')
        return ('%d/%d' % (avatars_count, len(operators)),
                '%d/%d' % (photo_count, len(operators)),
                '%d/%d' % (skills_count, skills_total),
                '%d/%d' % (skins_count, skins_total))

    async def save_materials_data(self):
        db_ark = DBArknights()
        building_data = get_json_data('building_data')
        item_data = get_json_data('item_table')
        formulas = {
            'WORKSHOP': building_data['workshopFormulas'],
            'MANUFACTURE': building_data['manufactFormulas']
        }

        materials = []
        materials_made = []
        materials_source = []
        for item_id, item in item_data['items'].items():
            if item_id.isdigit():
                material_name = item['name'].strip()
                icon_name = item['iconId']
                logger.debug(f'ArkGameData | 构建材料数据 [{material_name}]')

                materials.append({
                    'material_id': item_id,
                    'material_name': material_name,
                    'material_icon': icon_name,
                    'material_desc': item['usage']
                })
                await self.get_pic('item/pic/' + icon_name, 'materials')

                for drop in item['stageDropList']:
                    materials_source.append({
                        'material_id': item_id,
                        'source_place': drop['stageId'],
                        'source_rate': drop['occPer']
                    })

                for build in item['buildingProductList']:
                    if build['roomType'] in formulas and build['formulaId'] in formulas[build['roomType']]:
                        build_cost = formulas[build['roomType']][build['formulaId']]['costs']
                        for build_item in build_cost:
                            materials_made.append({
                                'material_id': item_id,
                                'use_material_id': build_item['id'],
                                'use_number': build_item['count'],
                                'made_type': build['roomType']
                            })

                logger.debug(f'ArkGameData | 构建材料数据 [{material_name}] 完成')

        logger.debug(f'ArkGameData | 保存全部材料数据')
        if materials:
            for material in materials:
                _res = await db_ark.add_material(**material)
                if _res.success():
                    logger.debug(f'ArkGameData | 更新材料 - {material["material_name"]} 成功')
                else:
                    logger.error(
                        f'ArkGameData | 更新材料 - {material["material_name"]} 失败, error: {_res.info}')

        if materials_made:
            for made in materials_made:
                _res = await db_ark.add_material_made(**made)
                if _res.success():
                    logger.debug(f'ArkGameData | 更新材料组成 - {made["material_id"]} 成功')
                else:
                    logger.error(
                        f'ArkGameData | 更新材料组成 - {made["material_id"]} 失败, error: {_res.info}')

        if materials_source:
            for source in materials_source:
                _res = await db_ark.add_material_source(**source)
                if _res.success():
                    logger.debug(f'ArkGameData | 更新材料来源 - {source["material_id"]} 成功')
                else:
                    logger.error(
                        f'ArkGameData | 更新材料来源 - {source["material_id"]} 失败, error: {_res.info}')

        logger.debug(f'ArkGameData | 保存全部材料数据 完成')
        return len(materials)

    async def save_stages_data(self):
        db_ark = DBArknights()
        stage_data = get_json_data('stage_table')['stages']
        stage_list = []

        for stage_id, item in stage_data.items():
            if '#f#' not in stage_id and item['name']:
                stage_list.append({
                    'stage_id': stage_id,
                    'stage_code': item['code'],
                    'stage_name': item['name']
                })

        logger.debug(f'ArkGameData | 更新关卡数据')

        _res = await db_ark.update_stage(stage_list)
        if _res.success():
            logger.debug(f'ArkGameData | 更新关卡数据 成功')
        else:
            logger.error(
                f'ArkGameData | 更新关卡数据 失败, error: {_res.info}')

        return len(stage_list)

    async def save_enemies_photo(self):
        enemies = self.init_enemies()

        success = 0
        total = 0
        for name, item in enemies.items():
            logger.debug(f'ArkGameData | 正在下载敌人 [{name}] 图片资源 成功')

            res = await self.get_pic('enemy_name/pic/' + item['info']['enemyId'], 'enemy_name', '?x-oss-process=style/jpg-test')
            success += 1 if res else 0
            total += 1

        return '%d/%d' % (success, total)

    async def update(self, refresh=True, cache=False):
        logger.debug('ArkGameData | 准备开始全量更新')
        time_rec = TimeRecord()
        await self.download_resource(cache)
        db_ark = DBArknights()
        await self.init_operator_gacha_config()
        if refresh:
            logger.debug('ArkGameData | 删除历史数据')
            _res = await db_ark.delete_all_material_data()
            if _res.success():
                logger.debug(f'ArkGameData | 删除所有材料数据 成功')
            else:
                logger.error(f'ArkGameData | 删除所有材料数据 失败, error: {_res.info}')
            _res = await db_ark.delete_all_operator_data()
            if _res.success():
                logger.debug(f'ArkGameData | 删除所有干员数据 成功')
            else:
                logger.error(f'ArkGameData | 删除所有干员数据 失败, error: {_res.info}')

        logger.debug('ArkGameData | 开始更新干员数据')
        operators = self.init_operators()
        for index, item in enumerate(operators):
            logger.debug('ArkGameData | 保存干员 [%d/%d][%s]' % (index + 1, len(operators), item.name))
            await self.save_operator_data(item)
        avatars, photo, skills, skins = await self.save_operator_photo(operators)

        logger.debug('ArkGameData | 开始更新敌人数据')
        enemies = await self.save_enemies_photo()

        logger.debug('ArkGameData | 开始更新材料数据')
        materials = await self.save_materials_data()

        logger.debug('ArkGameData | 开始更新关卡数据')
        stages = await self.save_stages_data()

        totals = (time_rec.total(),
                  len(operators),
                  avatars,
                  photo,
                  skills,
                  skins,
                  enemies,
                  materials,
                  stages)
        message = '数据更新完毕，总耗时%s' \
                  '\n -- %s 位干员' \
                  '\n -- %s 个干员头像' \
                  '\n -- %s 张干员半身照' \
                  '\n -- %s 个技能图标' \
                  '\n -- %s 张干员皮肤' \
                  '\n -- %s 张敌人图片' \
                  '\n -- %s 个材料' \
                  '\n -- %s 个关卡' % totals

        logger.debug(f'ArkGameData | {message}')
        return message

    async def download_resource(self, use_cache):
        logger.debug('ArkGameData | 检查JSON资源')

        for name in self.RESOURCE:
            url = '%s/%s.json' % (self.GITHUB_SOURCE, name)
            path = '%s/%s.json' % (self.RESOURCE_PATH, name.split('/')[-1])
            fetcher = HttpFetcher(timeout=30, flag='arknights_game_data', headers=self.HEADERS)
            if os.path.exists(path) is False or not use_cache:
                logger.debug(f'ArkGameData | 资源下载中: [{name}]')
                data = await fetcher.get_json(url)
                if data.success():
                    async with aiofiles.open(path, mode='w+', encoding='utf-8') as src:
                        await src.write(json.dumps(data.result, ensure_ascii=False))
                    logger.debug(f'ArkGameData | 资源下载成功: [{name}]')
                else:
                    logger.error(f'ArkGameData | 资源下载失败: [{name}], error: {data.info}')
            else:
                logger.error(f'ArkGameData | 资源已存在: [{name}]')



