"""
统一封装数据库操作
"""

from .database_utils import DBTable
from .class_result import Result
from .model import \
    DBUser, DBFriend, DBGroup, DBSubscription, DBDynamic, \
    DBPixivillust, DBPixivtag, DBPixivision, \
    DBHistory, DBAuth, DBCoolDownEvent, DBStatus, DBPluginStatistics, \
    DBArknights


__all__ = [
    'DBTable',
    'DBUser',
    'DBFriend',
    'DBGroup',
    'DBSubscription',
    'DBDynamic',
    'DBPixivillust',
    'DBPixivtag',
    'DBPixivision',
    'DBHistory',
    'DBAuth',
    'DBCoolDownEvent',
    'Result',
    'DBStatus',
    'DBPluginStatistics',
]
