import os
import random
from .utils import ARK_GAMEDATA_PATH, insert_empty, chinese_to_digits, word_in_sentence
from ..bot_database import DBArknights, Result
from nonebot import logger
import re

avatar_resource = os.path.join(ARK_GAMEDATA_PATH, 'images', 'avatars')
gacha_result = os.path.join(ARK_GAMEDATA_PATH, 'message', 'Gacha')

class_index = {
    1: 'PIONEER',
    2: 'WARRIOR',
    3: 'TANK',
    4: 'SNIPER',
    5: 'CASTER',
    6: 'SUPPORT',
    7: 'MEDIC',
    8: 'SPECIAL'
}


def get_temp_operator():
    operators = {}
    temp_path = os.path.join(ARK_GAMEDATA_PATH, 'tempOperator.txt')
    if os.path.exists(temp_path):
        with open(temp_path, mode='r', encoding='utf-8') as tp:
            ct = [item.split(',') for item in tp.read().strip('\n').split('\n')]
            for item in ct:
                operators[item[0]] = {
                    'photo': 'None',
                    'rarity': item[1],
                    'class': class_index[int(item[2])].lower()
                }
    return operators


class ArkGaChaHandler:
    async def init(self, user_id, *args, **kwargs):
        if self.init_finish:
            return
        db_ark = DBArknights()

        _res = await db_ark.get_gacha_pool()
        if _res.success():
            logger.debug(f'ArkGaChaHandler | 卡池信息 成功')
        else:
            logger.debug(f'ArkGaChaHandler | 卡池信息 失败, error: {_res.info}')
        self.all_pools = _res.result

        _res = await db_ark.get_gacha_pool(user_id=user_id)
        if _res.success():
            logger.debug(f'ArkGaChaHandler | 获取用户 {user_id} 卡池信息 成功')
        else:
            logger.debug(f'ArkGaChaHandler | 获取用户 {user_id} 卡池信息 失败, error: {_res.info}')
        pool = _res.result
        if bool(pool) is False:
            pool = self.all_pools[0]

        special = pool['pickup_s'].split(',') if pool['pickup_s'] else []
        weight = {}
        for item in special:
            item = item.split('|')
            weight[item[0]] = int(item[1])

        _res = await db_ark.get_gacha_operator(extra=weight.keys())
        if _res.success():
            logger.debug(f'ArkGaChaHandler | 获取卡池 干员信息 成功')
        else:
            logger.debug(f'ArkGaChaHandler | 获取卡池 干员信息 失败, error: {_res.info}')
        operators = _res.result

        class_group = {}
        for item in operators:
            rarity = item['operator_rarity']
            name = item['operator_name']
            if rarity not in class_group:
                class_group[rarity] = {}
            class_group[rarity][name] = {
                'name': name,
                'rarity': rarity,
                'weight': weight[name] if name in weight else 1
            }

        self.user_id = user_id
        self.operator = class_group
        self.temp_operator = get_temp_operator()
        self.limit_pool = pool['limit_pool']
        self.pick_up_name = pool['pool_name']
        self.pick_up = {
            6: [i for i in pool['pickup_6'].split(',') if i != ''],
            5: [i for i in pool['pickup_5'].split(',') if i != ''],
            4: [i for i in pool['pickup_4'].split(',') if i != '']
        }
        self.rarity_range = {
            1: 3,
            41: 4,
            91: 5,
            99: 6
        }
        '''
        概率：
        3 星 40% 区间为 1 ~ 40
        4 星 50% 区间为 41 ~ 90
        5 星 8% 区间为 91 ~ 98
        6 星 2% 区间为 99 ~ 100
        '''
        self.init_finish = True

    def __init__(self):
        self.keyword = ['抽', '连', '寻访', '保底', '卡池']
        self.init_finish = False
        self.re_list = [
            "抽卡\\d+次",
            "寻访\\d+次",
            "抽\\d+次",
            "\\d+次寻访",
            "\\d+连寻访",
            "\\d+连抽",
            "\\d+连",
            "\\d+抽"
        ]

    def find_once(self, reg, text):
        r = re.compile(reg)
        f = r.findall(text)
        if len(f):
            return f[0]
        return ''

    async def action(self, data, user_id, *args, **kwargs) -> Result.AnyResult:
        if not self.init_finish:
            await self.init(user_id, *args, **kwargs)

        message = chinese_to_digits(data)
        message_ori = data

        for item in self.re_list:
            r = re.search(re.compile(item), message)
            if r:
                times = int(self.find_once(r'\d+', self.find_once(item, message)))

                if times <= 0:
                    return Result.AnyResult(error=False, info='', result='请输入0~300的正数')
                if times > 300:
                    return Result.AnyResult(error=False, info='', result='都说了请输入0~300的正数')

                if times <= 10:
                    res = await self.detailed_mode(times, ten_times=times == 10)
                else:
                    res = await self.continuous_mode(times)

                return res

        if '保底' in message:
            return Result.AnyResult(error=False, info='', result=self.check_break_even())

        if word_in_sentence(message_ori, ['切换', '更换']):
            r = re.search(r'(\d+)', message_ori)
            if r:
                idx = int(r.group(1)) - 1
                if 0 <= idx < len(self.all_pools):
                    message_ori = self.all_pools[idx]['pool_name']
            return await self.change_pool(user_id, message_ori)

        if word_in_sentence(message, ['查看', '卡池', '列表']):
            return self.pool_list()

        if word_in_sentence(message, ['抽', '寻访']):
            Result.AnyResult(error=False, info='', result='博士是想抽卡吗？说「抽卡 N 次」或「N 连抽」就可以了')

    def pool_list(self):
        text = '博士，这是可更换的卡池列表：\n\n'
        pools = []
        max_len = 0
        for index, item in enumerate(self.all_pools):
            pool = '%s [ %s ]' % (('' if index + 1 >= 10 else '0') + str(index + 1), item['pool_name'])
            if index % 2 == 0 and len(pool) > max_len:
                max_len = len(pool)
            pools.append(pool)

        pools_table = ''
        curr_row = 0
        for index, item in enumerate(pools):
            if index % 2 == 0:
                pools_table += item
                curr_row = len(item)
            else:
                spaces = max_len - curr_row + 2
                pools_table += '%s%s\n' % ('　' * spaces, item)
                curr_row = 0

        if curr_row != 0:
            pools_table += '\n'

        text += pools_table
        text += '\n要切换卡池，请说「切换卡池 "卡池名称" 」\n或「切换第 N 个卡池」'
        return Result.AnyResult(error=False, info='', result=text)

    async def change_pool(self, user_id, message):
        db_ark = DBArknights()
        for item in self.all_pools:
            if item['pool_name'] in message:
                _res = await db_ark.set_gacha_pool(user_id, item['pool_id'])
                if _res.success():
                    logger.debug(f'ArkGaChaHandler | 用户 {user_id} 切换卡池 {item["pool_name"]} 成功')
                else:
                    logger.debug(f'ArkGaChaHandler | 用户 {user_id} 切换卡池 {item["pool_name"]} 失败, error: {_res.info}')

                text = ['博士的卡池已切换为【%s】\n' % item['pool_name']]
                if item['pickup_6']:
                    text.append('[★★★★★★] %s' % item['pickup_6'].replace(',', '、'))
                if item['pickup_5']:
                    text.append('[★★★★★　] %s' % item['pickup_5'].replace(',', '、'))
                if item['pickup_4']:
                    text.append('[☆☆☆☆　　] %s' % item['pickup_4'].replace(',', '、'))
                text = '\n'.join(text)
                return Result.AnyResult(error=False, info='', result=text)

        return Result.AnyResult(error=False, info='', result='没有找到这个卡池')

    async def continuous_mode(self, times) -> Result.AnyResult:
        operators = await self.start_gacha(times)

        rarity_sum = [0, 0, 0, 0]
        high_star = {
            5: {},
            6: {}
        }

        ten_gacha = []
        purple_pack = 0
        multiple_rainbow = {}

        result = '投递了%d张简历...\n\n【%s】\n' % (times, self.pick_up_name)

        for item in operators:
            rarity = item['rarity']
            name = item['name']

            # 记录抽到的各星级干员的数量
            rarity_sum[rarity - 3] += 1

            # 记录抽中的高星干员
            if rarity >= 5:
                if name not in high_star[rarity]:
                    high_star[rarity][name] = 0
                high_star[rarity][name] += 1

            # 记录每十连的情况
            ten_gacha.append(rarity)
            if len(ten_gacha) >= 10:

                five = ten_gacha.count(5)
                six = ten_gacha.count(6)

                if five == 0 and six == 0:
                    purple_pack += 1

                if six > 1:
                    if six not in multiple_rainbow:
                        multiple_rainbow[six] = 0
                    multiple_rainbow[six] += 1
                ten_gacha = []

        for r in high_star:
            sd = high_star[r]
            if sd:
                result += '\n%s\n' % ('★' * r)
                operator_num = {}
                for i in sorted(sd, key=sd.__getitem__, reverse=True):
                    num = high_star[r][i]
                    if num not in operator_num:
                        operator_num[num] = []
                    operator_num[num].append(i)
                for num in operator_num:
                    result += '%s X %d\n' % ('、'.join(operator_num[num]), num)

        if rarity_sum[2] == 0 and rarity_sum[3] == 0:
            result += '\n然而并没有高星干员...'

        result += '\n三星：%s四星：%d\n五星：%s六星：%d\n' % (
            insert_empty(rarity_sum[0], 4),
            rarity_sum[1],
            insert_empty(rarity_sum[2], 4),
            rarity_sum[3])

        enter = True
        if purple_pack > 0:
            result += '\n'
            enter = False
            result += '出现了 %d 次十连紫气东来\n' % purple_pack
        for num in multiple_rainbow:
            if enter:
                result += '\n'
                enter = False
            result += '出现了 %d 次十连内 %d 个六星\n' % (multiple_rainbow[num], num)

        result += '\n%s' % await self.check_break_even()

        return Result.AnyResult(error=False, info='', result=result)

    async def detailed_mode(self, times, ten_times=False) -> Result.AnyResult:
        db_ark = DBArknights()
        operators = await self.start_gacha(times)

        result = '投递了%d张简历...\n\n【%s】\n\n' % (times, self.pick_up_name)

        _res = await db_ark.get_all_operator([item['name'] for item in operators])
        if _res.success():
            logger.debug(f'ArkGaChaHandler | 获取全干员信息 成功')
        else:
            logger.debug(f'ArkGaChaHandler | 获取全干员信息 失败, error: {_res.info}')
        operators_data = _res.result

        operator_avatars = {item['operator_name']: item['operator_avatar'] for item in operators_data}

        icons = []
        for index, item in enumerate(operators):
            star = '☆' if item['rarity'] < 5 else '★'
            result += '%s%s%s\n\n' % (' ' * 15, insert_empty(item['name'], 6, True), star * item['rarity'])

            if item['name'] in operator_avatars:
                avatar_path = '%s/%s.png' % (avatar_resource, operator_avatars[item['name']])
                if os.path.exists(avatar_path):
                    icons.append({
                        'path': avatar_path,
                        'size': (34, 34),
                        'pos': (10, 60 + 34 * index)
                    })

        result += '\n%s' % await self.check_break_even()

        if ten_times:
            operators_info = {
                item['operator_name']: {
                    'photo': item['operator_avatar'],
                    'rarity': item['operator_rarity'],
                    'class': class_index[item['operator_class']].lower()
                } for item in operators_data
            }
            result_list = []

            for item in operators:
                name = item['name']
                op_dt = None

                if name in operators_info:
                    op_dt = operators_info[name]
                elif name in self.temp_operator:
                    op_dt = self.temp_operator[name]

                result_list.append(op_dt)

            res_img = '%s/%s' % (gacha_result, create_gacha_result(result_list))
            reply.insert(0, Image(res_img))

        return Result.AnyResult(error=False, info='', result=result)

    async def check_break_even(self):
        db_ark = DBArknights()
        _res = await db_ark.get_gacha_user(self.user_id)
        if _res.success():
            logger.debug(f'ArkGaChaHandler | 获取用户 {self.user_id} 卡池信息 成功')
        else:
            logger.debug(f'ArkGaChaHandler | 获取用户 {self.user_id} 卡池信息 失败, error: {_res.info}')
        user = _res.result
        break_even = user['gacha_break_even']
        break_even_rate = 98
        if break_even > 50:
            break_even_rate -= (break_even - 50) * 2

        return '已经抽取了 %d 次而未获得六星干员\n当前抽出六星干员的概率为 %d' % (break_even, 100 - break_even_rate) + '%'

    async def start_gacha(self, times):
        operators = []
        db_ark = DBArknights()
        _res = await db_ark.get_gacha_user(self.user_id)
        if _res.success():
            logger.debug(f'ArkGaChaHandler | 获取用户 {self.user_id} 卡池信息 成功')
        else:
            logger.debug(f'ArkGaChaHandler | 获取用户 {self.user_id} 卡池信息 失败, error: {_res.info}')
        user = _res.result
        break_even = user['gacha_break_even']

        for i in range(0, times):

            random_num = random.randint(1, 100)
            rarity = 0
            break_even_rate = 98

            for less in self.rarity_range:
                if random_num >= less:
                    rarity = self.rarity_range[less]

            break_even += 1

            if break_even > 50:
                break_even_rate -= (break_even - 50) * 2

            if random_num >= break_even_rate:
                rarity = 6

            if rarity == 6:
                break_even = 0

            operator = self.get_operator(rarity)

            operators.append({
                'rarity': rarity,
                'name': operator
            })

        _res = await db_ark.set_break_even(self.user_id, break_even)
        if _res.success():
            logger.debug(f'ArkGaChaHandler | 用户 {self.user_id} 卡池信息 更新成功')
        else:
            logger.debug(f'ArkGaChaHandler | 用户 {self.user_id} 卡池信息 更新失败, error: {_res.info}')
        return operators

    def get_operator(self, rarity):
        operator_list = []
        for name, item in self.operator[rarity].items():
            for w in range(item['weight']):
                operator_list.append(name)

        if rarity in self.pick_up and self.pick_up[rarity]:
            for name in self.pick_up[rarity]:
                if name in operator_list:
                    operator_list.remove(name)

            group = [self.pick_up[rarity]]
            group += [operator_list] * (4 if rarity == 4 else 1)

            special = {
                6: {
                    1: lambda g: g[int((random.randint(1, 100) + 1) / 70)],
                    2: lambda g: g[0]
                },
                5: {
                    2: lambda g: g[0]
                }
            }

            if rarity in special and self.limit_pool in special[rarity]:
                choice = special[rarity][self.limit_pool](group)
            else:
                choice = random.choice(group)

            return random.choice(choice)

        return random.choice(operator_list)
