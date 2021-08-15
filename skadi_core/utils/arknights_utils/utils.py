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

global_config = get_driver().config
ARK_GAMEDATA_PATH = global_config.ark_gamedata_path
RESOURCE_PATH = os.path.join(ARK_GAMEDATA_PATH, 'data')
fonts_dir = os.path.join(ARK_GAMEDATA_PATH, 'fonts')
if not os.path.exists(fonts_dir):
    os.makedirs(fonts_dir)
font_file = os.path.join(fonts_dir, 'font.ttf')
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


def insert_empty(text, max_num, half=False):
    return '%s%s' % (text, ('　' if half else ' ') * (max_num - len(str(text))))


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


def create_image(text: str, images=None):
    text = '\n'.join(split_text(text))
    height = len(text.split('\n')) + 1
    image = Image.new('RGB', (550, height * 18), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_file, 14)
    draw.text((10, 5), text, font=font, fill='#000000')

    if images:
        for item in images:
            if os.path.exists(item['path']) is False:
                continue
            img = Image.open(item['path']).convert('RGBA')
            img = img.resize(size=item['size'])
            image.paste(img, box=item['pos'], mask=img)

    return pic2b64(image)


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
