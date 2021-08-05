from ..database_utils import DBSession
from ..class_result import Result
from ..models import PixivTag, Pixiv, PixivT2I
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


class DBPixivtag(object):
    def __init__(self, tagname: str):
        self.tagname = tagname

    async def id(self) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(PixivTag.id).where(PixivTag.tagname == self.tagname)
                    )
                    pixivtag_table_id = session_result.scalar_one()
                    result = Result.IntResult(error=False, info='Success', result=pixivtag_table_id)
                except NoResultFound:
                    result = Result.IntResult(error=True, info='NoResultFound', result=-1)
                except MultipleResultsFound:
                    result = Result.IntResult(error=True, info='MultipleResultsFound', result=-1)
                except Exception as e:
                    result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def exist(self) -> bool:
        result = await self.id()
        return result.success()

    async def add(self) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    try:
                        session_result = await session.execute(
                            select(PixivTag).where(PixivTag.tagname == self.tagname)
                        )
                        exist_pixivtag = session_result.scalar_one()
                        result = Result.IntResult(error=False, info='pixivtag exist', result=0)
                    except NoResultFound:
                        new_tag = PixivTag(tagname=self.tagname, created_at=datetime.now())
                        session.add(new_tag)
                        result = Result.IntResult(error=False, info='Success added', result=0)
                await session.commit()
            except MultipleResultsFound:
                await session.rollback()
                result = Result.IntResult(error=True, info='MultipleResultsFound', result=-1)
            except Exception as e:
                await session.rollback()
                result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def list_illust(self, nsfw_tag: int) -> Result.ListResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(Pixiv.pid).join(PixivT2I).join(PixivTag).
                        where(Pixiv.id == PixivT2I.illust_id).
                        where(PixivT2I.tag_id == PixivTag.id).
                        where(Pixiv.nsfw_tag == nsfw_tag).
                        where(PixivTag.tagname.ilike(f'%{self.tagname}%'))
                    )
                    tag_pid_list = [x for x in session_result.scalars().all()]
                    result = Result.ListResult(error=False, info='Success', result=tag_pid_list)
                except Exception as e:
                    result = Result.ListResult(error=True, info=repr(e), result=[])
        return result
