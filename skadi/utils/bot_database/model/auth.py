from ..database_utils import DBSession
from ..class_result import Result
from ..models import AuthUser, AuthGroup, User, Group
from .user import DBUser
from .group import DBGroup
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


class DBAuth(object):
    def __init__(self, auth_id: int, auth_type: str, auth_node: str):
        """
        :param auth_id: 请求授权id, 用户qq号或群组群号
        :param auth_type:
            user: 用户授权
            group: 群组授权
        :param auth_node: 授权节点
        """
        self.auth_id = auth_id
        self.auth_type = auth_type
        self.auth_node = auth_node

    async def id(self) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    if self.auth_type == 'user':
                        session_result = await session.execute(
                            select(AuthUser.id).join(User).
                            where(AuthUser.user_id == User.id).
                            where(User.qq == self.auth_id).
                            where(AuthUser.auth_node == self.auth_node)
                        )
                        auth_table_id = session_result.scalar_one()
                        result = Result.IntResult(error=False, info='Success', result=auth_table_id)
                    elif self.auth_type == 'group':
                        session_result = await session.execute(
                            select(AuthGroup.id).join(Group).
                            where(AuthGroup.group_id == Group.id).
                            where(Group.group_id == self.auth_id).
                            where(AuthGroup.auth_node == self.auth_node)
                        )
                        auth_table_id = session_result.scalar_one()
                        result = Result.IntResult(error=False, info='Success', result=auth_table_id)
                    else:
                        result = Result.IntResult(error=True, info='Auth type error', result=-1)
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

    async def set(self, allow_tag: int, deny_tag: int, auth_info: str = None) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    try:
                        if self.auth_type == 'user':
                            session_result = await session.execute(
                                select(AuthUser).join(User).
                                where(AuthUser.user_id == User.id).
                                where(User.qq == self.auth_id).
                                where(AuthUser.auth_node == self.auth_node)
                            )
                            auth = session_result.scalar_one()
                            auth.allow_tag = allow_tag
                            auth.deny_tag = deny_tag
                            auth.auth_info = auth_info
                            auth.updated_at = datetime.now()
                            result = Result.IntResult(error=False, info='Success upgraded', result=0)
                        elif self.auth_type == 'group':
                            session_result = await session.execute(
                                select(AuthGroup).join(Group).
                                where(AuthGroup.group_id == Group.id).
                                where(Group.group_id == self.auth_id).
                                where(AuthGroup.auth_node == self.auth_node)
                            )
                            auth = session_result.scalar_one()
                            auth.allow_tag = allow_tag
                            auth.deny_tag = deny_tag
                            auth.auth_info = auth_info
                            auth.updated_at = datetime.now()
                            result = Result.IntResult(error=False, info='Success upgraded', result=0)
                        else:
                            result = Result.IntResult(error=True, info='Auth type error', result=-1)
                    except NoResultFound:
                        if self.auth_type == 'user':
                            user = DBUser(user_id=self.auth_id)
                            user_id_result = await user.id()
                            if user_id_result.error:
                                result = Result.IntResult(error=True, info='User not exist', result=-1)
                            else:
                                auth = AuthUser(user_id=user_id_result.result, auth_node=self.auth_node,
                                                allow_tag=allow_tag,
                                                deny_tag=deny_tag, auth_info=auth_info, created_at=datetime.now())
                                session.add(auth)
                                result = Result.IntResult(error=False, info='Success set', result=0)
                        elif self.auth_type == 'group':
                            group = DBGroup(group_id=self.auth_id)
                            group_id_result = await group.id()
                            if group_id_result.error:
                                result = Result.IntResult(error=True, info='Group not exist', result=-1)
                            else:
                                auth = AuthGroup(group_id=group_id_result.result, auth_node=self.auth_node,
                                                 allow_tag=allow_tag,
                                                 deny_tag=deny_tag, auth_info=auth_info, created_at=datetime.now())
                                session.add(auth)
                                result = Result.IntResult(error=False, info='Success set', result=0)
                        else:
                            result = Result.IntResult(error=True, info='Auth type error', result=-1)
                await session.commit()
            except MultipleResultsFound:
                await session.rollback()
                result = Result.IntResult(error=True, info='MultipleResultsFound', result=-1)
            except Exception as e:
                await session.rollback()
                result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def allow_tag(self) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    if self.auth_type == 'user':
                        session_result = await session.execute(
                            select(AuthUser.allow_tag).join(User).
                            where(AuthUser.user_id == User.id).
                            where(User.qq == self.auth_id).
                            where(AuthUser.auth_node == self.auth_node)
                        )
                        allow_tag = session_result.scalar_one()
                        result = Result.IntResult(error=False, info='Success', result=allow_tag)
                    elif self.auth_type == 'group':
                        session_result = await session.execute(
                            select(AuthGroup.allow_tag).join(Group).
                            where(AuthGroup.group_id == Group.id).
                            where(Group.group_id == self.auth_id).
                            where(AuthGroup.auth_node == self.auth_node)
                        )
                        allow_tag = session_result.scalar_one()
                        result = Result.IntResult(error=False, info='Success', result=allow_tag)
                    else:
                        result = Result.IntResult(error=True, info='Auth type error', result=-1)
                except NoResultFound:
                    result = Result.IntResult(error=True, info='NoResultFound', result=-2)
                except MultipleResultsFound:
                    result = Result.IntResult(error=True, info='MultipleResultsFound', result=-1)
                except Exception as e:
                    result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def deny_tag(self) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    if self.auth_type == 'user':
                        session_result = await session.execute(
                            select(AuthUser.deny_tag).join(User).
                            where(AuthUser.user_id == User.id).
                            where(User.qq == self.auth_id).
                            where(AuthUser.auth_node == self.auth_node)
                        )
                        deny_tag = session_result.scalar_one()
                        result = Result.IntResult(error=False, info='Success', result=deny_tag)
                    elif self.auth_type == 'group':
                        session_result = await session.execute(
                            select(AuthGroup.deny_tag).join(Group).
                            where(AuthGroup.group_id == Group.id).
                            where(Group.group_id == self.auth_id).
                            where(AuthGroup.auth_node == self.auth_node)
                        )
                        deny_tag = session_result.scalar_one()
                        result = Result.IntResult(error=False, info='Success', result=deny_tag)
                    else:
                        result = Result.IntResult(error=True, info='Auth type error', result=-1)
                except NoResultFound:
                    result = Result.IntResult(error=True, info='NoResultFound', result=-2)
                except MultipleResultsFound:
                    result = Result.IntResult(error=True, info='MultipleResultsFound', result=-1)
                except Exception as e:
                    result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def tags_info(self) -> Result.IntTupleResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    if self.auth_type == 'user':
                        session_result = await session.execute(
                            select(AuthUser.allow_tag, AuthUser.deny_tag).join(User).
                            where(AuthUser.user_id == User.id).
                            where(User.qq == self.auth_id).
                            where(AuthUser.auth_node == self.auth_node)
                        )
                        res = session_result.one()
                        result = Result.IntTupleResult(error=False, info='Success', result=(res[0], res[1]))
                    elif self.auth_type == 'group':
                        session_result = await session.execute(
                            select(AuthGroup.allow_tag, AuthGroup.deny_tag).join(Group).
                            where(AuthGroup.group_id == Group.id).
                            where(Group.group_id == self.auth_id).
                            where(AuthGroup.auth_node == self.auth_node)
                        )
                        res = session_result.one()
                        result = Result.IntTupleResult(error=False, info='Success', result=(res[0], res[1]))
                    else:
                        result = Result.IntTupleResult(error=True, info='Auth type error', result=(-1, -1))
                except NoResultFound:
                    result = Result.IntTupleResult(error=True, info='NoResultFound', result=(-2, -2))
                except MultipleResultsFound:
                    result = Result.IntTupleResult(error=True, info='MultipleResultsFound', result=(-1, -1))
                except Exception as e:
                    result = Result.IntTupleResult(error=True, info=repr(e), result=(-1, -1))
        return result

    async def delete(self) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    if self.auth_type == 'user':
                        session_result = await session.execute(
                            select(AuthUser).join(User).
                            where(AuthUser.user_id == User.id).
                            where(User.qq == self.auth_id).
                            where(AuthUser.auth_node == self.auth_node)
                        )
                        auth = session_result.scalar_one()
                        await session.delete(auth)
                        result = Result.IntResult(error=False, info='Success', result=0)
                    elif self.auth_type == 'group':
                        session_result = await session.execute(
                            select(AuthGroup).join(Group).
                            where(AuthGroup.group_id == Group.id).
                            where(Group.group_id == self.auth_id).
                            where(AuthGroup.auth_node == self.auth_node)
                        )
                        auth = session_result.scalar_one()
                        await session.delete(auth)
                        result = Result.IntResult(error=False, info='Success', result=0)
                    else:
                        result = Result.IntResult(error=True, info='Auth type error', result=-1)
                await session.commit()
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

    @classmethod
    async def list(cls, auth_type: str, auth_id: int) -> Result.ListResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    if auth_type == 'user':
                        session_result = await session.execute(
                            select(AuthUser.auth_node, AuthUser.allow_tag, AuthUser.deny_tag).join(User).
                            where(AuthUser.user_id == User.id).
                            where(User.qq == auth_id)
                        )
                        auth_node_list = [(x[0], x[1], x[2]) for x in session_result.all()]
                        result = Result.ListResult(error=False, info='Success', result=auth_node_list)
                    elif auth_type == 'group':
                        session_result = await session.execute(
                            select(AuthGroup.auth_node, AuthGroup.allow_tag, AuthGroup.deny_tag).join(Group).
                            where(AuthGroup.group_id == Group.id).
                            where(Group.group_id == auth_id)
                        )
                        auth_node_list = [(x[0], x[1], x[2]) for x in session_result.all()]
                        result = Result.ListResult(error=False, info='Success', result=auth_node_list)
                    else:
                        result = Result.ListResult(error=True, info='Auth type error', result=[])
                except NoResultFound:
                    result = Result.ListResult(error=True, info='NoResultFound', result=[])
                except MultipleResultsFound:
                    result = Result.ListResult(error=True, info='MultipleResultsFound', result=[])
                except Exception as e:
                    result = Result.ListResult(error=True, info=repr(e), result=[])
        return result
