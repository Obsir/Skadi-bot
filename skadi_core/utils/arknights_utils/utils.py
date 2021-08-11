import time
import datetime
import re
import json
import difflib
from PIL import Image, ImageDraw, ImageFont
import os
from nonebot import get_driver
import base64
from io import BytesIO
import pypinyin
from string import punctuation
from zhon.hanzi import punctuation as punctuation_cn

font_file = './AdobeHeitiStd-Regular.otf'
logo_file = './rabbit.png'
logo_file_white = './rabbit-white.png'
global_config = get_driver().config
ARK_GAMEDATA_PATH = global_config.ark_gamedata_path
RESOURCE_PATH = os.path.join(ARK_GAMEDATA_PATH, 'data')
resource = '%s/message' % ARK_GAMEDATA_PATH
if not os.path.exists(resource):
    os.makedirs(resource)
punctuation = r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""


class Config:
    high_star = {
        '5': '资深干员',
        '6': '高级资深干员'
    }
    classes = {
        'PIONEER': '先锋',
        'WARRIOR': '近卫',
        'TANK': '重装',
        'SNIPER': '狙击',
        'CASTER': '术师',
        'SUPPORT': '辅助',
        'MEDIC': '医疗',
        'SPECIAL': '特种'
    }
    types = {
        'MELEE': '近战',
        'RANGED': '远程'
    }


def string_equal_rate(str1: str, str2: str):
    return difflib.SequenceMatcher(None, str1, str2).quick_ratio()


def text_to_pinyin(text: str):
    return ''.join([item[0] for item in pypinyin.pinyin(text, style=pypinyin.NORMAL)]).lower()


def find_similar_string(text: str, text_list: list, hard=0.4, return_rate=False):
    r = 0
    t = ''
    for item in text_list:
        rate = float(string_equal_rate(text, item))
        if rate > r and rate >= hard:
            r = rate
            t = item
    return (t, r) if return_rate else t


def get_json_data(name):
    path = '%s/%s.json' % (RESOURCE_PATH, name)
    with open(path, mode='r', encoding='utf-8') as src:
        return json.load(src)


class TimeRecord:
    def __init__(self):
        self.time = time.time()

    def rec(self, millisecond=False):
        mil = 1000 if millisecond else 1
        return int(time.time() * mil - self.time * mil)

    def total(self):
        return self.calc_time_total(self.rec())

    def calc_time_total(self, seconds):
        timedelta = datetime.timedelta(seconds=seconds)
        day = timedelta.days
        hour, mint, sec = tuple([
            int(n) for n in str(timedelta).split(',')[-1].split(':')
        ])
        total = ''
        if day:
            total += '%d天' % day
        if hour:
            total += '%d小时' % hour
        if mint:
            total += '%d分钟' % mint
        if sec and not (day or hour or mint):
            total += '%d秒' % sec
        return total


def remove_xml_tag(text: str):
    return re.compile(r'<[^>]+>', re.S).sub('', text)


def split_text(text):
    text = text.strip('\n').split('\n')

    new_text = []
    for item in text:
        if len(item) > 38:
            for sub_item in cut_code(item, 38):
                if sub_item:
                    new_text.append(sub_item)
        else:
            new_text.append(item)

    return new_text


def create_image(text: str, message, images=None):
    text = '\n'.join(split_text(text))
    height = len(text.split('\n')) + 1
    image = Image.new('RGB', (550, height * 18), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_file, 14)
    draw.text((10, 5), text, font=font, fill='#000000')

    icon = Image.open(logo_file)
    icon = icon.resize(size=(30, 30))
    image.paste(icon, box=(520, 0), mask=icon)

    if images:
        for item in images:
            if os.path.exists(item['path']) is False:
                continue
            img = Image.open(item['path']).convert('RGBA')
            img = img.resize(size=item['size'])
            image.paste(img, box=item['pos'], mask=img)

    path = '%s/%s' % (resource, message)
    if os.path.exists(path) is False:
        os.mkdir(path)

    name = '%s.png' % datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
    path = '%s/%s' % (path, name)
    image.save(path)

    return pic2b64(image)


def orm_get(entity, target: str):
    try:
        return eval(f"entity.{target}")
    except Exception as e:
        print(e)
        return entity[target]


def pic2b64(pic: Image) -> str:
    """
    说明：
        PIL图片转base64
    参数：
        :param pic: 通过PIL打开的图片文件
    """
    buf = BytesIO()
    pic.save(buf, format="PNG")
    base64_str = base64.b64encode(buf.getvalue()).decode()
    return "base64://" + base64_str


character_relation = {
    '零': 0,
    '一': 1,
    '二': 2,
    '两': 2,
    '三': 3,
    '四': 4,
    '五': 5,
    '六': 6,
    '七': 7,
    '八': 8,
    '九': 9,
    '十': 10,
    '百': 100,
    '千': 1000,
    '万': 10000,
    '亿': 100000000
}
start_symbol = ['一', '二', '两', '三', '四', '五', '六', '七', '八', '九', '十']
more_symbol = list(character_relation.keys())

def word_in_sentence(sentence: str, words: list):
    for word in words:
        if word in sentence:
            return True
    return False

def chinese_to_digits(text: str):
    symbol_str = ''
    found = False
    for item in text:
        if item in start_symbol:
            if not found:
                found = True
            symbol_str += item
        else:
            if found:
                if item in more_symbol:
                    symbol_str += item
                    continue
                else:
                    digits = str(_digits(symbol_str))
                    text = text.replace(symbol_str, digits, 1)
                    symbol_str = ''
                    found = False

    if symbol_str:
        digits = str(_digits(symbol_str))
        text = text.replace(symbol_str, digits, 1)

    return text


def remove_punctuation(text: str):
    for i in punctuation:
        text = text.replace(i, '')
    for i in punctuation_cn:
        text = text.replace(i, '')
    return text


def cut_code(code, length):
    code_list = re.findall('.{' + str(length) + '}', code)
    code_list.append(code[(len(code_list) * length):])
    res_list = []
    for n in code_list:
        if n != '':
            res_list.append(n)
    return res_list


def _digits(chinese: str):
    total = 0
    r = 1
    for i in range(len(chinese) - 1, -1, -1):
        val = character_relation[chinese[i]]
        if val >= 10 and i == 0:
            if val > r:
                r = val
                total = total + val
            else:
                r = r * val
                # total = total + r * x
        elif val >= 10:
            if val > r:
                r = val
            else:
                r = r * val
        else:
            total = total + r * val
    return total


operator_pool_list = [
    {"pool_name": "常驻寻访", "pickup_6": "塞雷娅,嵯峨", "pickup_5": "食铁兽,灰喉,四月", "pickup_4": "", "pickup_s": "",
     "limit_pool": 0},
    {"pool_name": "联合行动", "pickup_6": "棘刺,夜莺,铃兰,温蒂", "pickup_5": "临光,安哲拉,赫默,芙兰卡,极境,莱恩哈特", "pickup_4": "",
     "pickup_s": None,
     "limit_pool": 2},
    {"pool_name": "银灰色的荣耀", "pickup_6": "银灰", "pickup_5": "初雪,崖心", "pickup_4": "角峰",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "搅动潮汐之剑", "pickup_6": "斯卡蒂", "pickup_5": "夜魔,临光", "pickup_4": "猎蜂,暗索",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "鞘中赤红", "pickup_6": "陈", "pickup_5": "诗怀雅,食铁兽", "pickup_4": "格雷伊",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "龙门特别行动专员寻访", "pickup_6": "星熊", "pickup_5": "雷蛇,陨星", "pickup_4": "",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "深夏的守夜人", "pickup_6": "黑", "pickup_5": "格劳克斯,蓝毒", "pickup_4": "苏苏洛",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "久铸尘铁", "pickup_6": "赫拉格", "pickup_5": "星极,可颂", "pickup_4": "桃金娘",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "火舞之人", "pickup_6": "艾雅法拉", "pickup_5": "普罗旺斯,幽灵鲨", "pickup_4": "",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "冰封原野", "pickup_6": "麦哲伦", "pickup_5": "送葬人,赫默", "pickup_4": "红云",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "锁与匙的守卫者", "pickup_6": "莫斯提马", "pickup_5": "槐琥,守林人", "pickup_4": "梅",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "凝电之钻", "pickup_6": "能天使", "pickup_5": "布洛卡,苇草", "pickup_4": "",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "热情，膨胀，爆发", "pickup_6": "煌", "pickup_5": "灰喉,天火", "pickup_4": "安比尔",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "地生五金", "pickup_6": "年,阿", "pickup_5": "吽", "pickup_4": "",
     "pickup_s": None,
     "limit_pool": 1},
    {"pool_name": "百种兵器", "pickup_6": "刻俄柏", "pickup_5": "拉普兰德,惊蛰", "pickup_4": "",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "草垛上的风笛声", "pickup_6": "风笛", "pickup_5": "慑砂,凛冬", "pickup_4": "宴",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "往日幻象", "pickup_6": "傀影", "pickup_5": "巫恋,白面鸮", "pickup_4": "刻刀",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "遗愿焰火", "pickup_6": "W,温蒂", "pickup_5": "极境", "pickup_4": "",
     "pickup_s": None,
     "limit_pool": 1},
    {"pool_name": "雾漫荒林", "pickup_6": "", "pickup_5": "石棉,月禾", "pickup_4": "",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "雪落晨心", "pickup_6": "早露", "pickup_5": "莱恩哈特,真理", "pickup_4": "波登可",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "君影轻灵", "pickup_6": "铃兰", "pickup_5": "断崖,夜魔", "pickup_4": "卡达",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "流沙涡旋", "pickup_6": "", "pickup_5": "蜜蜡,贾维", "pickup_4": "",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "不羁逆流", "pickup_6": "棘刺", "pickup_5": "安哲拉,普罗旺斯", "pickup_4": "孑",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "燃钢之心，暴躁铁皮", "pickup_6": "森蚺", "pickup_5": "燧石,陨星", "pickup_4": "酸糖",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "无拘熔火", "pickup_6": "史尔特尔", "pickup_5": "四月,极境", "pickup_4": "芳汀",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "瑕光微明", "pickup_6": "瑕光", "pickup_5": "奥斯塔,白金", "pickup_4": "泡泡",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "勿忘我", "pickup_6": "迷迭香,泥岩", "pickup_5": "絮雨", "pickup_4": "杰克",
     "pickup_s": None,
     "limit_pool": 1},
    {"pool_name": "自由的囚徒", "pickup_6": "山", "pickup_5": "卡夫卡,赫默", "pickup_4": "松果",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "麦穗与赞美诗", "pickup_6": "空弦", "pickup_5": "爱丽丝,贾维", "pickup_4": "豆苗",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "月隐晦明", "pickup_6": "夕,嵯峨", "pickup_5": "乌有", "pickup_4": "",
     "pickup_s": "年|5",
     "limit_pool": 0},
    {"pool_name": "进攻、防守、战术交汇", "pickup_6": "灰烬", "pickup_5": "霜华,闪击", "pickup_4": "",
     "pickup_s": None,
     "limit_pool": 1},
    {"pool_name": "沙海过客", "pickup_6": "异客", "pickup_5": "熔泉", "pickup_4": "",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "深悼", "pickup_6": "浊心斯卡蒂,凯尔希", "pickup_5": "赤冬", "pickup_4": "",
     "pickup_s": 'W|5',
     "limit_pool": 1},
    {"pool_name": "革新交响曲", "pickup_6": "卡涅利安", "pickup_5": "绮良,崖心", "pickup_4": "深靛",
     "pickup_s": None,
     "limit_pool": 0},
    {"pool_name": "从星火中来", "pickup_6": "帕拉斯", "pickup_5": "幽灵鲨,红", "pickup_4": "",
     "pickup_s": None,
     "limit_pool": 0},
]
operator_gacha_config_list = [
    {"operator_name": "年", "operator_type": 0},
    {"operator_name": "W", "operator_type": 0},
    {"operator_name": "迷迭香", "operator_type": 0},
    {"operator_name": "夕", "operator_type": 0},
    {"operator_name": "浊心斯卡蒂", "operator_type": 0},
    {"operator_name": "假日威龙陈", "operator_type": 0},
    {"operator_name": "灰烬", "operator_type": 1},
    {"operator_name": "霜华", "operator_type": 1},
    {"operator_name": "闪击", "operator_type": 1},
    {"operator_name": "阿米娅", "operator_type": 2},
    {"operator_name": "阿米娅近卫", "operator_type": 2},
    {"operator_name": "暴行", "operator_type": 2},
    {"operator_name": "断罪者", "operator_type": 2},
    {"operator_name": "嘉维尔", "operator_type": 3},
    {"operator_name": "讯使", "operator_type": 3},
    {"operator_name": "微风", "operator_type": 3},
    {"operator_name": "伊桑", "operator_type": 3},
    {"operator_name": "坚雷", "operator_type": 3},
    {"operator_name": "清流", "operator_type": 4},
    {"operator_name": "因陀罗", "operator_type": 4},
    {"operator_name": "火神", "operator_type": 4},
    {"operator_name": "艾丝黛尔", "operator_type": 4},
    {"operator_name": "格拉尼", "operator_type": 5},
    {"operator_name": "锡兰", "operator_type": 5},
    {"operator_name": "炎客", "operator_type": 5},
    {"operator_name": "拜松", "operator_type": 5},
    {"operator_name": "雪雉", "operator_type": 5},
    {"operator_name": "铸铁", "operator_type": 5},
    {"operator_name": "苦艾", "operator_type": 5},
    {"operator_name": "亚叶", "operator_type": 5},
    {"operator_name": "特米米", "operator_type": 5},
    {"operator_name": "薄绿", "operator_type": 5},
    {"operator_name": "鞭刃", "operator_type": 5},
    {"operator_name": "罗宾", "operator_type": 5},
    {"operator_name": "炎狱炎熔", "operator_type": 5},
    {"operator_name": "暴雨", "operator_type": 5},
    {"operator_name": "歌蕾蒂娅", "operator_type": 5},
    {"operator_name": "战车", "operator_type": 6},
    {"operator_name": "柏喙", "operator_type": 7},
    {"operator_name": "稀音", "operator_type": 7},
    {"operator_name": "图耶", "operator_type": 7},
    {"operator_name": "预备干员-近战", "operator_type": 8},
    {"operator_name": "预备干员-狙击", "operator_type": 8},
    {"operator_name": "预备干员-后勤", "operator_type": 8},
    {"operator_name": "预备干员-术师", "operator_type": 8},
    {"operator_name": "Sharp", "operator_type": 8},
    {"operator_name": "Stormeye", "operator_type": 8},
    {"operator_name": "Pith", "operator_type": 8},
    {"operator_name": "Touch", "operator_type": 8},
]
