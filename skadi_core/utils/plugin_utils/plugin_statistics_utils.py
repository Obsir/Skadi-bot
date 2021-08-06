import datetime
from ..bot_database import DBPluginStatistics, Result
from dataclasses import dataclass, field


async def add_plugin_use_count(plugin: str) -> Result.IntResult:
    res = await DBPluginStatistics.add_plugin_use_count(plugin=plugin)
    return res


__all__ = [
    'add_plugin_use_count',
]
