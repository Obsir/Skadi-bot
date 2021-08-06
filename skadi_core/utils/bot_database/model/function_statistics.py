from ..database_utils import DBSession
from ..class_result import Result
from ..models import PluginStatistics
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


class DBPluginStatistics(object):

    @classmethod
    async def add_plugin_use_count(
            cls, plugin: str) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    try:
                        session_result = await session.execute(
                            select(PluginStatistics).
                            where(PluginStatistics.plugin == plugin)
                        )
                        plugin_statistics = session_result.scalar_one()
                        plugin_statistics.updated_at = datetime.now()
                        plugin_statistics.use_count += 1
                        result = Result.IntResult(error=False, info='Success upgraded', result=0)
                    except NoResultFound:
                        new_plugin_statistics = PluginStatistics(
                            plugin=plugin, created_at=datetime.now())
                        session.add(new_plugin_statistics)
                        result = Result.IntResult(error=False, info='Success added', result=0)
                await session.commit()
            except MultipleResultsFound:
                await session.rollback()
                result = Result.IntResult(error=True, info='MultipleResultsFound', result=-1)
            except Exception as e:
                await session.rollback()
                result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result


