from ..database_utils import DBSession
from ..class_result import Result
from ..models import User, UserGroup, UserSub, AuthUser
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


class DBUser(object):
    def __init__(self, user_id: int):
        self.qq = user_id

    async def id(self) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(User.id).where(User.qq == self.qq)
                    )
                    user_table_id = session_result.scalar_one()
                    result = Result.IntResult(error=False, info='Success', result=user_table_id)
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

    async def nickname(self) -> Result.TextResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(User.nickname).where(User.qq == self.qq)
                    )
                    user_nickname = session_result.scalar_one()
                    result = Result.TextResult(error=False, info='Success', result=user_nickname)
                except NoResultFound:
                    result = Result.TextResult(error=True, info='NoResultFound', result='')
                except MultipleResultsFound:
                    result = Result.TextResult(error=True, info='MultipleResultsFound', result='')
                except Exception as e:
                    result = Result.TextResult(error=True, info=repr(e), result='')
        return result

    async def add(self, nickname: str, is_friend: int = 0, aliasname: str = None) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    try:
                        # 用户已存在则更新成员表昵称
                        session_result = await session.execute(
                            select(User).where(User.qq == self.qq)
                        )
                        exist_user = session_result.scalar_one()
                        if exist_user.nickname == nickname:
                            result = Result.IntResult(error=False, info='Nickname not change', result=0)
                        else:
                            exist_user.nickname = nickname
                            exist_user.is_friend = is_friend
                            exist_user.aliasname = aliasname
                            exist_user.updated_at = datetime.now()
                            result = Result.IntResult(error=False, info='Success upgraded', result=0)
                    except NoResultFound:
                        # 不存在则成员表中添加新成员
                        new_user = User(qq=self.qq, nickname=nickname, is_friend=is_friend,
                                        aliasname=aliasname, created_at=datetime.now())
                        session.add(new_user)
                        result = Result.IntResult(error=False, info='Success added', result=0)
                await session.commit()
            except MultipleResultsFound:
                await session.rollback()
                result = Result.IntResult(error=True, info='MultipleResultsFound', result=-1)
            except Exception as e:
                await session.rollback()
                result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def delete(self) -> Result.IntResult:
        id_result = await self.id()
        if id_result.error:
            return Result.IntResult(error=True, info='User not exist', result=-1)

        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    # 清空该用户权限节点
                    session_result = await session.execute(
                        select(AuthUser).where(AuthUser.user_id == id_result.result)
                    )
                    for exist_auth_node in session_result.scalars().all():
                        await session.delete(exist_auth_node)

                    # 清空订阅
                    session_result = await session.execute(
                        select(UserSub).where(UserSub.user_id == id_result.result)
                    )
                    for exist_user_sub in session_result.scalars().all():
                        await session.delete(exist_user_sub)

                    # 清空群成员表中该用户
                    session_result = await session.execute(
                        select(UserGroup).where(UserGroup.user_id == id_result.result)
                    )
                    for exist_user in session_result.scalars().all():
                        await session.delete(exist_user)

                    # 删除用户表中用户
                    session_result = await session.execute(
                        select(User).where(User.qq == self.qq)
                    )
                    exist_user = session_result.scalar_one()
                    await session.delete(exist_user)
                await session.commit()
                result = Result.IntResult(error=False, info='Success Delete', result=0)
            except NoResultFound:
                await session.rollback()
                result = Result.IntResult(error=True, info='NoResultFound', result=-1)
            except MultipleResultsFound:
                await session.rollback()
                result = Result.IntResult(error=True, info='MultipleResultsFound', result=-1)
            except Exception as e:
                await session.rollback()
                result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

