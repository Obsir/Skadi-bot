from nonebot import require, logger
from nonebot.adapters import Bot
import nonebot
from nonebot.adapters.cqhttp.message import MessageSegment
import os
from pathlib import Path

try:
    import ujson as json
except ModuleNotFoundError:
    import json
IMAGE_PATH = Path(os.path.join(nonebot.get_driver().config.genshin_data_path, 'images'))
IMAGE_PATH.mkdir(parents=True, exist_ok=True)
IMAGE_PATH = str(IMAGE_PATH.absolute()) + '/'

TXT_PATH = Path(os.path.join(nonebot.get_driver().config.genshin_data_path, 'text'))
TXT_PATH.mkdir(parents=True, exist_ok=True)
TXT_PATH = str(TXT_PATH.absolute()) + '/'

TTF_PATH = Path(os.path.join(nonebot.get_driver().config.genshin_data_path, 'ttf'))
TTF_PATH.mkdir(parents=True, exist_ok=True)
TTF_PATH = str(TTF_PATH.absolute()) + '/'
scheduler = require("nonebot_plugin_apscheduler").scheduler


def get_message_text(data: str) -> str:
    """
    说明：
        获取消息中 纯文本 的信息
    参数：
        :param data: event.json()
    """
    data = json.loads(data)
    result = ""
    for msg in data["message"]:
        if msg["type"] == "text":
            result += msg["data"]["text"].strip() + " "
    return result.strip()


def get_bot() -> Bot:
    """
    说明：
        获取 bot 对象
    """
    return list(nonebot.get_bots().values())[0]


def image(
        img_name: str = None, path: str = None, abspath: str = None, b64: str = None
) -> MessageSegment or str:
    """
    说明：
        生成一个 MessageSegment.image 消息
        生成顺序：绝对路径(abspath) > base64(b64) > img_name
    参数：
        :param img_name: 图片文件名称，默认在 resource/img 目录下
        :param path: 图片所在路径，默认在 resource/img 目录下
        :param abspath: 图片绝对路径
        :param b64: 图片base64
    """
    if abspath:
        return (
            MessageSegment.image("file:///" + abspath)
            if os.path.exists(abspath)
            else ""
        )
    elif b64:
        return MessageSegment.image(b64 if "base64://" in b64 else "base64://" + b64)
    else:
        if "http" in img_name:
            return MessageSegment.image(img_name)
        if len(img_name.split(".")) == 1:
            img_name += ".jpg"
        file = (
            Path(IMAGE_PATH) / path / img_name if path else Path(IMAGE_PATH) / img_name
        )
        if file.exists():
            return MessageSegment.image(f"file:///{file.absolute()}")
        else:
            logger.warning(f"图片 {file.absolute()}缺失...")
            return ""
