from ..database_utils import DBSession
from ..class_result import Result
from ..models import \
    User, Group, UserGroup, Subscription, GroupSub, AuthGroup
from .user import DBUser
from .subscription import DBSubscription
from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound


class DBGroup(object):
    def __init__(self, group_id: int):
        self.group_id = group_id

    async def id(self) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(Group.id).where(Group.group_id == self.group_id)
                    )
                    group_table_id = session_result.scalar_one()
                    result = Result.IntResult(error=False, info='Success', result=group_table_id)
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

    async def name(self) -> Result.TextResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(Group.name).where(Group.group_id == self.group_id)
                    )
                    group_name = session_result.scalar_one()
                    result = Result.TextResult(error=False, info='Success', result=group_name)
                except NoResultFound:
                    result = Result.TextResult(error=True, info='NoResultFound', result='')
                except MultipleResultsFound:
                    result = Result.TextResult(error=True, info='MultipleResultsFound', result='')
                except Exception as e:
                    result = Result.TextResult(error=True, info=repr(e), result='')
        return result

    async def add(self, name: str) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    try:
                        session_result = await session.execute(
                            select(Group).where(Group.group_id == self.group_id)
                        )
                        exist_group = session_result.scalar_one()
                        exist_group.name = name
                        exist_group.updated_at = datetime.now()
                        result = Result.IntResult(error=False, info='Success upgraded', result=0)
                    except NoResultFound:
                        new_group = Group(group_id=self.group_id, name=name, notice_permissions=0,
                                          command_permissions=0, permission_level=0, created_at=datetime.now())
                        session.add(new_group)
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
            return Result.IntResult(error=True, info='Group not exist', result=-1)

        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    # 清空权限节点
                    session_result = await session.execute(
                        select(AuthGroup).where(AuthGroup.group_id == id_result.result)
                    )
                    for exist_auth_node in session_result.scalars().all():
                        await session.delete(exist_auth_node)

                    # 清空群成员列表
                    session_result = await session.execute(
                        select(UserGroup).where(UserGroup.group_id == id_result.result)
                    )
                    for exist_user in session_result.scalars().all():
                        await session.delete(exist_user)

                    # 清空订阅
                    session_result = await session.execute(
                        select(GroupSub).where(GroupSub.group_id == id_result.result)
                    )
                    for exist_group_sub in session_result.scalars().all():
                        await session.delete(exist_group_sub)

                    # 删除群组表中该群组
                    session_result = await session.execute(
                        select(Group).where(Group.group_id == self.group_id)
                    )
                    exist_group = session_result.scalar_one()
                    await session.delete(exist_group)
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

    async def member_list(self) -> Result.ListResult:
        id_result = await self.id()
        if id_result.error:
            return Result.ListResult(error=True, info='Group not exist', result=[])

        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(User.qq, UserGroup.user_group_nickname).
                        join(UserGroup).
                        where(UserGroup.group_id == id_result.result)
                    )
                    res = [(x[0], x[1]) for x in session_result.all()]
                    result = Result.ListResult(error=False, info='Success', result=res)
                except Exception as e:
                    result = Result.ListResult(error=True, info=repr(e), result=[])
        return result

    async def member_add(self, user: DBUser, user_group_nickname: str) -> Result.IntResult:
        group_id_result = await self.id()
        if group_id_result.error:
            return Result.IntResult(error=True, info='Group not exist', result=-1)

        user_id_result = await user.id()
        if user_id_result.error:
            return Result.IntResult(error=True, info='User not exist', result=-1)

        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    # 查询成员-群组表中用户-群关系
                    try:
                        # 用户-群关系已存在, 更新用户群昵称
                        session_result = await session.execute(
                            select(UserGroup).
                            where(UserGroup.user_id == user_id_result.result).
                            where(UserGroup.group_id == group_id_result.result)
                        )
                        exist_user = session_result.scalar_one()
                        exist_user.user_group_nickname = user_group_nickname
                        exist_user.updated_at = datetime.now()
                        result = Result.IntResult(error=False, info='Success upgraded', result=0)
                    except NoResultFound:
                        # 不存在关系则添加新成员
                        new_user = UserGroup(user_id=user_id_result.result, group_id=group_id_result.result,
                                             user_group_nickname=user_group_nickname, created_at=datetime.now())
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

    async def member_del(self, user: DBUser) -> Result.IntResult:
        group_id_result = await self.id()
        if group_id_result.error:
            return Result.IntResult(error=True, info='Group not exist', result=-1)

        user_id_result = await user.id()
        if user_id_result.error:
            return Result.IntResult(error=True, info='User not exist', result=-1)

        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    session_result = await session.execute(
                        select(UserGroup).
                        where(UserGroup.user_id == user_id_result.result).
                        where(UserGroup.group_id == group_id_result.result)
                    )
                    exist_user = session_result.scalar_one()
                    await session.delete(exist_user)
                await session.commit()
                result = Result.IntResult(error=False, info='Success', result=0)
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

    async def member_clear(self) -> Result.IntResult:
        group_id_result = await self.id()
        if group_id_result.error:
            return Result.IntResult(error=True, info='Group not exist', result=-1)

        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    session_result = await session.execute(
                        select(UserGroup).where(UserGroup.group_id == group_id_result.result)
                    )
                    for exist_user in session_result.scalars().all():
                        await session.delete(exist_user)
                await session.commit()
                result = Result.IntResult(error=False, info='Success', result=0)
            except Exception as e:
                await session.rollback()
                result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def permission_reset(self) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    session_result = await session.execute(
                        select(Group).where(Group.group_id == self.group_id)
                    )
                    exist_group = session_result.scalar_one()
                    exist_group.notice_permissions = 0
                    exist_group.command_permissions = 0
                    exist_group.permission_level = 0
                    exist_group.updated_at = datetime.now()
                    result = Result.IntResult(error=False, info='Success upgraded', result=0)
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

    async def permission_set(self, notice: int = 0, command: int = 0, level: int = 0) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    session_result = await session.execute(
                        select(Group).where(Group.group_id == self.group_id)
                    )
                    exist_group = session_result.scalar_one()
                    exist_group.notice_permissions = notice
                    exist_group.command_permissions = command
                    exist_group.permission_level = level
                    exist_group.updated_at = datetime.now()
                    result = Result.IntResult(error=False, info='Success upgraded', result=0)
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

    async def permission_info(self) -> Result.IntTupleResult:
        """
        :return: Result: Tuple[Notice_permission, Command_permission, Permission_level]
        """
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(Group.notice_permissions, Group.command_permissions, Group.permission_level).
                        where(Group.group_id == self.group_id)
                    )
                    notice, command, level = session_result.one()
                    result = Result.IntTupleResult(error=False, info='Success', result=(notice, command, level))
                except NoResultFound:
                    result = Result.IntTupleResult(error=True, info='NoResultFound', result=(-1, -1, -1))
                except MultipleResultsFound:
                    result = Result.IntTupleResult(error=True, info='MultipleResultsFound', result=(-1, -1, -1))
                except Exception as e:
                    result = Result.IntTupleResult(error=True, info=repr(e), result=(-1, -1, -1))
        return result

    async def permission_notice(self) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(Group.notice_permissions).where(Group.group_id == self.group_id)
                    )
                    res = session_result.scalar_one()
                    result = Result.IntResult(error=False, info='Success', result=res)
                except Exception as e:
                    result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def permission_command(self) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(Group.command_permissions).where(Group.group_id == self.group_id)
                    )
                    res = session_result.scalar_one()
                    result = Result.IntResult(error=False, info='Success', result=res)
                except Exception as e:
                    result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def permission_level(self) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(Group.permission_level).where(Group.group_id == self.group_id)
                    )
                    res = session_result.scalar_one()
                    result = Result.IntResult(error=False, info='Success', result=res)
                except Exception as e:
                    result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def subscription_list(self) -> Result.ListResult:
        """
        :return: Result: List[Tuple[sub_type, sub_id, up_name]]
        """
        group_id_result = await self.id()
        if group_id_result.error:
            return Result.ListResult(error=True, info='Group not exist', result=[])

        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(Subscription.sub_type, Subscription.sub_id, Subscription.up_name).
                        join(GroupSub).
                        where(Subscription.id == GroupSub.sub_id).
                        where(GroupSub.group_id == group_id_result.result)
                    )
                    res = [(x[0], x[1], x[2]) for x in session_result.all()]
                    result = Result.ListResult(error=False, info='Success', result=res)
                except Exception as e:
                    result = Result.ListResult(error=True, info=repr(e), result=[])
        return result

    async def subscription_list_by_type(self, sub_type: int) -> Result.ListResult:
        """
        :param sub_type: 订阅类型
        :return: Result: List[Tuple[sub_id, up_name]]
        """
        group_id_result = await self.id()
        if group_id_result.error:
            return Result.ListResult(error=True, info='Group not exist', result=[])

        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(Subscription.sub_id, Subscription.up_name).
                        join(GroupSub).
                        where(Subscription.sub_type == sub_type).
                        where(Subscription.id == GroupSub.sub_id).
                        where(GroupSub.group_id == group_id_result.result)
                    )
                    res = [(x[0], x[1]) for x in session_result.all()]
                    result = Result.ListResult(error=False, info='Success', result=res)
                except Exception as e:
                    result = Result.ListResult(error=True, info=repr(e), result=[])
        return result

    async def subscription_add(self, sub: DBSubscription, group_sub_info: str = None) -> Result.IntResult:
        group_id_result = await self.id()
        if group_id_result.error:
            return Result.IntResult(error=True, info='Group not exist', result=-1)

        sub_id_result = await sub.id()
        if sub_id_result.error:
            return Result.IntResult(error=True, info='Subscription not exist', result=-1)

        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    try:
                        session_result = await session.execute(
                            select(GroupSub).
                            where(GroupSub.group_id == group_id_result.result).
                            where(GroupSub.sub_id == sub_id_result.result)
                        )
                        # 订阅关系已存在, 更新信息
                        exist_subscription = session_result.scalar_one()
                        exist_subscription.group_sub_info = group_sub_info
                        exist_subscription.updated_at = datetime.now()
                        result = Result.IntResult(error=False, info='Success upgraded', result=0)
                    except NoResultFound:
                        subscription = GroupSub(sub_id=sub_id_result.result, group_id=group_id_result.result,
                                                group_sub_info=group_sub_info, created_at=datetime.now())
                        session.add(subscription)
                        result = Result.IntResult(error=False, info='Success added', result=0)
                await session.commit()
            except MultipleResultsFound:
                await session.rollback()
                result = Result.IntResult(error=True, info='MultipleResultsFound', result=-1)
            except Exception as e:
                await session.rollback()
                result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def subscription_del(self, sub: DBSubscription) -> Result.IntResult:
        group_id_result = await self.id()
        if group_id_result.error:
            return Result.IntResult(error=True, info='Group not exist', result=-1)

        sub_id_result = await sub.id()
        if sub_id_result.error:
            return Result.IntResult(error=True, info='Subscription not exist', result=-1)

        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    session_result = await session.execute(
                        select(GroupSub).
                        where(GroupSub.group_id == group_id_result.result).
                        where(GroupSub.sub_id == sub_id_result.result)
                    )
                    exist_subscription = session_result.scalar_one()
                    await session.delete(exist_subscription)
                await session.commit()
                result = Result.IntResult(error=False, info='Success', result=0)
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

    async def subscription_clear(self) -> Result.IntResult:
        group_id_result = await self.id()
        if group_id_result.error:
            return Result.IntResult(error=True, info='Group not exist', result=-1)

        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    session_result = await session.execute(
                        select(GroupSub).where(GroupSub.group_id == group_id_result.result)
                    )
                    for exist_group_sub in session_result.scalars().all():
                        await session.delete(exist_group_sub)
                await session.commit()
                result = Result.IntResult(error=False, info='Success', result=0)
            except Exception as e:
                await session.rollback()
                result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def subscription_clear_by_type(self, sub_type: int) -> Result.IntResult:
        group_id_result = await self.id()
        if group_id_result.error:
            return Result.IntResult(error=True, info='Group not exist', result=-1)

        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    session_result = await session.execute(
                        select(GroupSub).join(Subscription).
                        where(GroupSub.sub_id == Subscription.id).
                        where(Subscription.sub_type == sub_type).
                        where(GroupSub.group_id == group_id_result.result)
                    )
                    for exist_group_sub in session_result.scalars().all():
                        await session.delete(exist_group_sub)
                await session.commit()
                result = Result.IntResult(error=False, info='Success', result=0)
            except Exception as e:
                await session.rollback()
                result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

