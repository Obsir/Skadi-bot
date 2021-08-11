#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import nonebot
from nonebot.adapters.cqhttp import Bot as CQHTTPBot
# from nonebot.adapters.ding import Bot as DINGBot
# from nonebot.adapters.mirai import Bot as MIRAIBot
# from nonebot.adapters.mirai import WebsocketBot
from nonebot.drivers.fastapi import Config

# Custom your logger
# 
from nonebot.log import logger, default_format
from skadi_core.configs import path_config
# win环境下proxy配置
import sys
import asyncio
import os
from datetime import datetime

if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# File path
bot_runtime_path = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'skadi_runtime'))
bot_res_path = os.path.abspath(os.path.join(bot_runtime_path, 'resources'))
if not os.path.exists(bot_res_path):
    os.makedirs(bot_res_path)

bot_log_path = os.path.abspath(os.path.join(bot_runtime_path, 'log'))
if not os.path.exists(bot_log_path):
    os.makedirs(bot_log_path)
# Custom logger
log_info_name = f"{datetime.today().strftime('%Y%m%d-%H_%M')}-INFO.log"
log_error_name = f"{datetime.today().strftime('%Y%m%d-%H_%M')}-ERROR.log"
log_info_path = os.path.join(bot_log_path, log_info_name)
log_error_path = os.path.join(bot_log_path, log_error_name)
logger.add(log_info_path, rotation="00:00", backtrace=True, diagnose=True, level="INFO", format=default_format, encoding='utf-8')
logger.add(log_error_path, rotation="00:00", backtrace=True, diagnose=True, level="ERROR", format=default_format, encoding='utf-8')


# You can pass some keyword args config to init function
nonebot.init()

config = nonebot.get_driver().config
config.root_path_ = bot_runtime_path
config.bot_res_path = bot_res_path

path_config.init_plugin_res_path(config)

app = nonebot.get_asgi()
driver = nonebot.get_driver()
# driver.register_adapter('mirai-ws', WebsocketBot, qq=1021493660) # qq参数需要填在mah中登录的qq
driver.register_adapter("cqhttp", CQHTTPBot)
# driver.register_adapter("ding", DINGBot)
# driver.register_adapter("mirai", MIRAIBot)

nonebot.load_builtin_plugins()
nonebot.load_plugins("skadi_core/plugins")
nonebot.load_from_toml("pyproject.toml")

# Modify some config / config depends on loaded configs
# 
# config = driver.config
# do something...


if __name__ == "__main__":
    nonebot.run(app="__mp_main__:app")
