from ..database_utils import DBSession
from ..class_result import Result
from ..ark_models import *
from ..models import Base
from .user import DBUser
from .group import DBGroup
from datetime import datetime
import asyncio
from sqlalchemy.future import select
import aiofiles
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy import or_, and_, desc


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class DBArknights(metaclass=Singleton):

    async def __add(self, model, *args, **kwargs):
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    new_data = model(*args, **kwargs, created_at=datetime.now())
                    session.add(new_data)
                    result = Result.IntResult(error=False, info='Success added', result=new_data)
                await session.commit()
            except MultipleResultsFound:
                await session.rollback()
                result = Result.IntResult(error=True, info='MultipleResultsFound', result=-1)
            except Exception as e:
                await session.rollback()
                result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def add_operator_gacha_config(
            self, operator_name, operator_type) -> Result.IntResult:
        return await self.__add(OperatorGachaConfig, operator_name, operator_type)

    async def add_operator_pool(
            self, pool_name, pickup_6, pickup_5, pickup_4, pickup_s, limit_pool) -> Result.IntResult:
        return await self.__add(OperatorPool, pool_name, pickup_6, pickup_5, pickup_4, pickup_s, limit_pool)

    async def add_operator(
            self, operator_no: str, operator_name: str, operator_en_name: str, operator_avatar: str,
            operator_rarity: int, operator_class: int,
            available: int, in_limit: int) -> Result.IntResult:
        return await self.__add(Operator, operator_no, operator_name, operator_en_name, operator_avatar,
                                operator_rarity,
                                operator_class,
                                available, in_limit)

    async def add_operator_detail(
            self, operator_id, operator_desc, operator_usage, operator_quote, operator_token, max_level, max_hp,
            attack, defense, magic_resistance, cost, block_count, attack_time, respawn_time) -> Result.IntResult:
        return await self.__add(OperatorDetail, operator_id, operator_desc, operator_usage, operator_quote,
                                operator_token, max_level, max_hp,
                                attack, defense, magic_resistance, cost, block_count, attack_time, respawn_time)

    async def add_operator_evolve_cost(
            self, evolve_level, operator_id, use_material_id, use_number) -> Result.IntResult:
        return await self.__add(OperatorEvolveCosts, evolve_level, operator_id, use_material_id, use_number)

    async def add_operator_skill(
            self, operator_id, skill_index, skill_name, skill_icon, skill_no) -> Result.IntResult:
        return await self.__add(OperatorSkill, operator_id, skill_index, skill_name, skill_icon, skill_no)

    async def add_operator_skill_mastery_cost(
            self, skill_id, mastery_level, use_material_id, use_number) -> Result.IntResult:
        return await self.__add(OperatorSkillMasteryCosts, skill_id, mastery_level, use_material_id, use_number)

    async def add_operator_skill_description(
            self, skill_id, skill_level, skill_type, sp_type, sp_init, sp_cost, duration, description,
            max_charge) -> Result.IntResult:
        return await self.__add(OperatorSkillDescription, skill_id, skill_level, skill_type, sp_type, sp_init, sp_cost,
                                duration, description,
                                max_charge)

    async def add_operator_tags_relation(
            self, operator_name, operator_rarity, operator_tags) -> Result.IntResult:
        return await self.__add(OperatorTagsRelation, operator_name, operator_rarity, operator_tags)

    async def add_operator_skin(
            self, operator_id, skin_image, skin_type, skin_name, skin_drawer, skin_group, skin_content, skin_usage,
            skin_desc, skin_source) -> Result.IntResult:
        return await self.__add(OperatorSkins, operator_id, skin_image, skin_type, skin_name, skin_drawer, skin_group,
                                skin_content, skin_usage,
                                skin_desc, skin_source)

    async def add_operator_voice(
            self, operator_id, voice_title, voice_text, voice_no) -> Result.IntResult:
        return await self.__add(OperatorVoice, operator_id, voice_title, voice_text, voice_no)

    async def add_operator_story(
            self, operator_id, story_title, story_text) -> Result.IntResult:
        return await self.__add(OperatorStories, operator_id, story_title, story_text)

    async def add_operator_talent(self, operator_id, talents_name, talents_desc) -> Result.IntResult:
        return await self.__add(OperatorTalents, operator_id, talents_name, talents_desc)

    async def add_operator_potential(self, operator_id, potential_desc, potential_rank) -> Result.IntResult:
        return await self.__add(OperatorPotential, operator_id, potential_desc, potential_rank)

    async def add_operator_building_skill(self, operator_id, bs_unlocked, bs_name, bs_desc) -> Result.IntResult:
        return await self.__add(OperatorBuildingSkill, operator_id, bs_unlocked, bs_name, bs_desc)

    async def add_material(self, material_id, material_name, material_icon, material_desc) -> Result.IntResult:
        return await self.__add(Material, material_id, material_name, material_icon, material_desc)

    async def add_material_source(self, material_id, source_place, source_rate) -> Result.IntResult:
        return await self.__add(MaterialSource, material_id, source_place, source_rate)

    async def add_material_made(self, material_id, use_material_id, use_number, made_type) -> Result.IntResult:
        return await self.__add(MaterialMade, material_id, use_material_id, use_number, made_type)

    async def get_operator_id(self, operator_no='', operator_name='') -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(Operator.operator_id).where(
                            or_(Operator.operator_no == operator_no, Operator.operator_name == operator_name))
                    )
                    operator_id = session_result.scalar_one()
                    result = Result.IntResult(error=False, info='Success', result=operator_id)
                except NoResultFound:
                    result = Result.IntResult(error=True, info='NoResultFound', result=-1)
                except MultipleResultsFound:
                    result = Result.IntResult(error=True, info='MultipleResultsFound', result=-1)
                except Exception as e:
                    result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def get_operator_by_id(self, operator_id) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(Operator).where(Operator.operator_id == operator_id)
                    )
                    operator = session_result.scalar_one()
                    result = Result.AnyResult(error=False, info='Success', result=operator)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except MultipleResultsFound:
                    result = Result.AnyResult(error=True, info='MultipleResultsFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def get_skill_id(self, skill_no, operator_id) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(OperatorSkill.skill_id).
                            filter(OperatorSkill.skill_no == skill_no).
                            filter(OperatorSkill.operator_id == operator_id)
                    )
                    operator_skill_id = session_result.scalar_one()
                    result = Result.IntResult(error=False, info='Success', result=operator_skill_id)
                except NoResultFound:
                    result = Result.IntResult(error=True, info='NoResultFound', result=-1)
                except MultipleResultsFound:
                    result = Result.IntResult(error=True, info='MultipleResultsFound', result=-1)
                except Exception as e:
                    result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def get_all_operator(self, names: list = None) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    if names:
                        session_result = await session.execute(
                            select(Operator).filter(Operator.operator_name.in_(names))
                        )
                    else:
                        session_result = await session.execute(
                            select(Operator)
                        )
                    operators = session_result.scalars().all()
                    result = Result.AnyResult(error=False, info='Success', result=operators)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def get_gacha_operator(self, limit=0, extra=None) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(select(Operator).filter(Operator.available == 1).filter(
                        or_(Operator.in_limit.in_([limit, 0]), Operator.operator_name.in_(extra))))
                    operators = session_result.scalars().all()
                    result = Result.AnyResult(error=False, info='Success', result=operators)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def get_all_operator_tags(self) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(OperatorTagsRelation)
                    )
                    operator_tags = session_result.fetchall()
                    result = Result.AnyResult(error=False, info='Success', result=operator_tags)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def get_all_operator_skill(self) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(OperatorSkill)
                    )
                    operator_skills = session_result.scalars().all()
                    result = Result.AnyResult(error=False, info='Success', result=operator_skills)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def get_operator_skill_by_name(self, skill_name) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(OperatorSkill.skill_index, Operator.operator_name).outerjoin(
                            Operator, Operator.operator_id == OperatorSkill.operator_id).filter(
                            OperatorSkill.skill_name.like(f'%{skill_name}%'))
                    )
                    operator_results = session_result.scalars().all()
                    result = Result.AnyResult(error=False, info='Success', result=operator_results)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def get_all_stories_title(self) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(OperatorStories.story_title).group_by(OperatorStories.story_title))
                    operator_stories = session_result.scalars().all()
                    result = Result.AnyResult(error=False, info='Success', result=operator_stories)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def get_all_skins(self) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(select(OperatorSkins))
                    operator_skins = session_result.scalars().all()
                    result = Result.AnyResult(error=False, info='Success', result=operator_skins)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def find_operator_skin(self, skin_name) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(
                        select(OperatorSkins).filter(OperatorSkins.skin_name == skin_name)
                    )
                    operator_skin = session_result.scalar_one()
                    result = Result.AnyResult(error=False, info='Success', result=operator_skin)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except MultipleResultsFound:
                    result = Result.AnyResult(error=True, info='MultipleResultsFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def find_operator_all_detail(self, operator_id) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(select(Operator).filter(Operator.operator_id == operator_id))
                    base = session_result.scalar_one()
                    session_result = await session.execute(select(OperatorDetail).filter(
                        OperatorDetail.operator_id == operator_id))
                    detail = session_result.scalar_one()
                    session_result = await session.execute(select(OperatorTalents).filter(
                        OperatorTalents.operator_id == operator_id))
                    talents = session_result.scalars().all()
                    session_result = await session.execute(select(OperatorPotential).filter(
                        OperatorPotential.operator_id == operator_id))
                    potential = session_result.scalars().all()
                    session_result = await session.execute(
                        select(OperatorBuildingSkill).filter(
                            OperatorBuildingSkill.operator_id == operator_id)
                    )
                    building_skill = session_result.scalars().all()

                    result = Result.AnyResult(error=False, info='Success',
                                              result=[base, detail, talents, potential, building_skill])
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def find_operator_evolve_costs(self, name, level) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    sql = f'SELECT operator_id FROM {Operator.__tablename__} WHERE operator_name = "{name}"'
                    sql = f'SELECT m.material_name, m.material_icon, o.use_number FROM {OperatorEvolveCosts.__tablename__} o ' \
                          f'LEFT JOIN {Material.__tablename__} m ON m.material_id = o.use_material_id ' \
                          f'WHERE o.evolve_level = {level} AND o.operator_id in ({sql})'
                    # session_result = await session.execute(select(Material.material_name, Material.material_icon,
                    #                                               OperatorEvolveCosts.use_number).outerjoin(Material,
                    #                                                                                         Material.material_id == OperatorEvolveCosts.use_material_id).filter(
                    #     and_(OperatorEvolveCosts.evolve_level == level, OperatorEvolveCosts.operator_id.in_(
                    #         session.execute(select(Operator.operator_id).filter(Operator.operator_name == name))))))
                    session_result = await session.execute(sql)
                    operator_results = session_result.fetchall()
                    result = Result.AnyResult(error=False, info='Success', result=operator_results)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def find_operator_skill_mastery_costs(self, name, level, index=0) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    field = ', '.join([
                        's.skill_name',
                        's.skill_index',
                        's.skill_icon',
                        'm.material_name',
                        'm.material_icon',
                        'o.use_number',
                        'o.mastery_level'
                    ])
                    left_join = ' '.join([
                        f'LEFT JOIN {Material.__tablename__} m ON m.material_id = o.use_material_id',
                        f'LEFT JOIN {OperatorSkill.__tablename__} s ON s.skill_id = o.skill_id'
                    ])
                    sql = f'SELECT operator_id FROM {Operator.__tablename__} WHERE operator_name = "{name}"'
                    sql = f'SELECT skill_id FROM {OperatorSkill.__tablename__} WHERE operator_id IN ({sql})'
                    sql = f'SELECT {field} FROM {OperatorSkillMasteryCosts.__tablename__} o {left_join} ' \
                          f'WHERE o.mastery_level = {level} AND o.skill_id IN ({sql})'

                    if index > 0:
                        sql += ' AND s.skill_index = %d' % index
                    # session_result = await session.execute(select(OperatorSkill.skill_name, OperatorSkill.skill_index,
                    #                                      OperatorSkill.skill_icon,
                    #                                      Material.material_name, Material.material_icon,
                    #                                      OperatorSkillMasteryCosts.use_number,
                    #                                      OperatorSkillMasteryCosts.mastery_level).outerjoin(Material,
                    #                                                                                         Material.material_id == OperatorSkillMasteryCosts.use_material_id).outerjoin(
                    #     OperatorSkill, OperatorSkill.skill_id == OperatorSkillMasteryCosts.skill_id).filter(
                    #     OperatorSkillMasteryCosts.mastery_level == level).filter(OperatorSkillMasteryCosts.skill_id.in_(
                    #     session.execute(select(OperatorSkill.skill_id).filter(OperatorSkill.operator_id.in_(
                    #         session.execute(select(Operator.operator_id).filter(Operator.operator_name == name))))))))
                    # if index > 0:
                    #     session_result = await session_result.filter(OperatorSkill.skill_index == index)
                    session_result = await session.execute(sql)
                    operator_results = session_result.fetchall()
                    result = Result.AnyResult(error=False, info='Success', result=operator_results)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def find_operator_skill_description(self, name, level, index=0) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    # session_result = await session.execute(select(OperatorSkill.skill_name, OperatorSkill.skill_index,
                    #                                      OperatorSkill.skill_icon,
                    #                                      OperatorSkillDescription.skill_type,
                    #                                      OperatorSkillDescription.sp_type,
                    #                                      OperatorSkillDescription.sp_init,
                    #                                      OperatorSkillDescription.sp_cost,
                    #                                      OperatorSkillDescription.duration,
                    #                                      OperatorSkillDescription.description,
                    #                                      OperatorSkillDescription.max_charge).outerjoin(OperatorSkill,
                    #                                                                                     OperatorSkill.skill_id == OperatorSkillDescription.skill_id).filter(
                    #     OperatorSkillDescription.skill_level == level).filter(OperatorSkillDescription.skill_id.in_(
                    #     session.execute(select(OperatorSkill.skill_id).filter(OperatorSkill.operator_id.in_(
                    #         session.execute(select(Operator.operator_id).filter(Operator.operator_name == name))))))))
                    # if index > 0:
                    #     session_result = await session_result.filter(OperatorSkill.skill_index == index)
                    field = ', '.join([
                        's.skill_name',
                        's.skill_index',
                        's.skill_icon',
                        'd.skill_type',
                        'd.sp_type',
                        'd.sp_init',
                        'd.sp_cost',
                        'd.duration',
                        'd.description',
                        'd.max_charge'
                    ])
                    left_join = ' '.join([
                        f'LEFT JOIN {OperatorSkill.__tablename__} s ON s.skill_id = d.skill_id'
                    ])

                    sql = f'SELECT operator_id FROM {Operator.__tablename__} WHERE operator_name = "{name}"'
                    sql = f'SELECT skill_id FROM {OperatorSkill.__tablename__} WHERE operator_id IN ({sql})'
                    sql = f'SELECT {field} FROM {OperatorSkillDescription.__tablename__} d {left_join} ' \
                          f'WHERE d.skill_level = {level} AND d.skill_id IN ({sql})'

                    if index > 0:
                        sql += ' AND s.skill_index = %d' % index
                    session_result = await session.execute(sql)
                    operator_results = session_result.fetchall()
                    result = Result.AnyResult(error=False, info='Success', result=operator_results)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def find_operator_tags_by_tags(self, tags, min_rarity=1, max_rarity=6) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    # session_result = await session.execute(select(OperatorTagsRelation).filter(
                    #     or_(*[OperatorTagsRelation.operator_tags == tag for tag in tags])).filter(
                    #     OperatorTagsRelation.operator_rarity >= min_rarity).filter(
                    #     OperatorTagsRelation.operator_rarity <= max_rarity).order_by(
                    #     desc(OperatorTagsRelation.operator_rarity)))
                    where = []
                    for item in tags:
                        where.append('operator_tags = "%s"' % item)
                    where = ' OR '.join(where)
                    sql = f'SELECT * FROM {OperatorTagsRelation.__tablename__} WHERE ( {where} ) ' \
                          f'AND operator_rarity >= {min_rarity} ' \
                          f'AND operator_rarity <= {max_rarity} ' \
                          f'ORDER BY operator_rarity DESC'
                    session_result = await session.execute(sql)
                    operator_results = session_result.fetchall()
                    result = Result.AnyResult(error=False, info='Success', result=operator_results)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def find_operator_stories(self, name, title) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    # session_result = await session.execute(select(OperatorStories.story_text).outerjoin(OperatorStories,
                    #                                                                            OperatorStories.operator_id == Operator.operator_id).filter(
                    #     and_(Operator.operator_name == name, OperatorStories.story_title == title)))
                    sql = f'SELECT os.story_text FROM {Operator.__tablename__} o ' \
                          f'LEFT JOIN {OperatorStories.__tablename__} os on o.operator_id = os.operator_id ' \
                          f'WHERE o.operator_name = "{name}" and os.story_title = "{title}"'
                    session_result = await session.execute(sql)
                    operator_results = session_result.scalar_one()
                    result = Result.AnyResult(error=False, info='Success', result=operator_results)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except MultipleResultsFound:
                    result = Result.AnyResult(error=True, info='MultipleResultsFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def find_operator_voice(self, operator_name, title) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    _res = await session.execute(select(Operator.operator_id).filter(
                        Operator.operator_name == operator_name))
                    operator_id = _res.scalar_one()
                    session_result = await session.execute(select(OperatorVoice).filter(
                        and_(OperatorVoice.operator_id == operator_id, OperatorVoice.voice_title == title)))
                    operator_results = session_result.scalar_one()
                    result = Result.AnyResult(error=False, info='Success', result=operator_results)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except MultipleResultsFound:
                    result = Result.AnyResult(error=True, info='MultipleResultsFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def get_all_material(self) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(select(Material))
                    materials = session_result.scalars().all()
                    result = Result.AnyResult(error=False, info='Success', result=materials)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def get_material(self, name='') -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(select(Material).filter(or_(Material.material_name == name)))
                    material = session_result.scalar_one()
                    result = Result.AnyResult(error=False, info='Success', result=material)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except MultipleResultsFound:
                    result = Result.AnyResult(error=True, info='MultipleResultsFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def find_material_source(self, name, only_main=False) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    # session_result = await session.execute(select(Stage.stage_code, Stage.stage_name,
                    #                                      MaterialSource.source_rate).outerjoin(Stage,
                    #                                                                            Stage.stage_id == MaterialSource.source_place).outerjoin(
                    #     Material, Material.material_id == MaterialSource.material_id).filter(
                    #     Material.material_name == name).filter(MaterialSource.source_place.in_(session.execute(select(Stage.id)))))
                    # if only_main:
                    #     session_result = await session_result.filter(
                    #         or_(Stage.stage_id.like('main%'), Stage.stage_id.like('sub%'), Stage.stage_id.like('wk%')))
                    field = ', '.join([
                        'st.stage_code',
                        'st.stage_name',
                        'ms.source_rate'
                    ])
                    left_join = ' '.join([
                        f'LEFT JOIN {Stage.__tablename__} st ON st.stage_id = ms.source_place',
                        f'LEFT JOIN {Material.__tablename__} m ON m.material_id = ms.material_id'
                    ])

                    sql = f'SELECT stage_id FROM {Stage.__tablename__}'
                    sql = f'SELECT {field} FROM {MaterialSource.__tablename__} ms {left_join} ' \
                          f'WHERE m.material_name = "{name}" AND ms.source_place IN ({sql})'

                    if only_main:
                        sql += ' AND (st.stage_id LIKE "main%" OR st.stage_id LIKE "sub%" OR st.stage_id LIKE "wk%")'
                    session_result = await session.execute(sql)
                    results = session_result.fetchall()
                    result = Result.AnyResult(error=False, info='Success', result=results)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def find_material_made(self, name) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    # session_result = await session.execute(select(Material.material_name, Material.material_icon,
                    #                                      MaterialMade.use_number, MaterialMade.made_type).outerjoin(
                    #     Material, Material.material_id == MaterialMade.material_id).outerjoin(Material,
                    #                                                                           Material.material_id == MaterialMade.use_material_id).filter(
                    #     Material.material_name == name))
                    field = ', '.join([
                        'ml.material_name',
                        'ml.material_icon',
                        'mm.use_number',
                        'mm.made_type'
                    ])
                    left_join = ' '.join([
                        f'LEFT JOIN {Material.__tablename__} m ON m.material_id = mm.material_id',
                        f'LEFT JOIN {Material.__tablename__} ml ON ml.material_id = mm.use_material_id'
                    ])

                    sql = f'SELECT {field} FROM {MaterialMade.__tablename__} mm {left_join} WHERE m.material_name = "{name}"'
                    session_result = await session.execute(sql)
                    results = session_result.fetchall()
                    result = Result.AnyResult(error=False, info='Success', result=results)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def create_tags_file(self, path):
        tags_list = ['资深', '高资', '高级资深']

        all_operator_tags = await self.get_all_operator_tags()
        for item in all_operator_tags.result:
            if item['operator_tags'] not in tags_list:
                tags_list.append(item['operator_tags'])

        async with aiofiles.open(path, mode='w+', encoding='utf-8') as file:
            await file.write('\n'.join([item + ' 100 n' for item in tags_list]))

        return path

    async def update_stage(self, stage_list) -> Result.IntResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    await session.execute('truncate %s' % Stage.__tablename__)
                    for stage_info in stage_list:
                        new_stage = Stage(**stage_info)
                        session.add(new_stage)
                    result = Result.IntResult(error=False, info='Success', result=0)
                    await session.commit()
                except MultipleResultsFound:
                    await session.rollback()
                    result = Result.IntResult(error=True, info='MultipleResultsFound', result=-1)
                except Exception as e:
                    await session.rollback()
                    result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def delete_all_material_data(self) -> Result.IntResult:
        tables = [
            Material,
            MaterialMade,
            MaterialSource,
        ]
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    for table in tables:
                        await session.execute('truncate %s' % table.__tablename__)
                    result = Result.IntResult(error=False, info='Success', result=0)
                except NoResultFound:
                    result = Result.IntResult(error=True, info='NoResultFound', result=-1)
                except MultipleResultsFound:
                    result = Result.IntResult(error=True, info='MultipleResultsFound', result=-1)
                except Exception as e:
                    result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def delete_all_operator_data(self) -> Result.IntResult:
        tables = [
            Operator,
            OperatorBuildingSkill,
            OperatorDetail,
            OperatorEvolveCosts,
            OperatorPotential,
            OperatorSkill,
            OperatorSkillDescription,
            OperatorSkillMasteryCosts,
            OperatorSkins,
            OperatorStories,
            OperatorTagsRelation,
            OperatorTalents,
            OperatorVoice
        ]
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    for table in tables:
                        await session.execute('truncate %s' % table.__tablename__)
                    result = Result.IntResult(error=False, info='Success', result=0)
                except NoResultFound:
                    result = Result.IntResult(error=True, info='NoResultFound', result=-1)
                except MultipleResultsFound:
                    result = Result.IntResult(error=True, info='MultipleResultsFound', result=-1)
                except Exception as e:
                    result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def get_operator_gacha_config(self, group='limit') -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(select(OperatorGachaConfig.operator_name).filter(
                        OperatorGachaConfig.operator_type.in_(
                            [0, 1]) if group == 'limit' else OperatorGachaConfig.operator_type > 1))
                    operator_gacha_configs = session_result.scalars().all()
                    result = Result.AnyResult(error=False, info='Success', result=operator_gacha_configs)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def delete_gacha_config_and_pool(self) -> Result.IntResult:
        tables = [
            OperatorGachaConfig,
            OperatorPool,
        ]
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    for table in tables:
                        await session.execute('truncate %s' % table.__tablename__)
                    result = Result.IntResult(error=False, info='Success', result=0)
                except Exception as e:
                    await session.rollback()
                    result = Result.IntResult(error=True, info=repr(e), result=-1)
        return result

    async def get_gacha_pool(self, user_id=None):
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    where = (f'pool_id IN (SELECT gacha_pool FROM {UserGacha.__tablename__} WHERE user_id = %s)' % user_id) if user_id else None
                    if where:
                        sql = f'SELECT * FROM {OperatorPool.__tablename__} WHERE {where} '
                    else:
                        sql = f'SELECT * FROM {OperatorPool.__tablename__}'
                    session_result = await session.execute(sql)
                    if user_id:
                        result = session_result.fetchone()
                    else:
                        result = session_result.fetchall()
                    result = Result.AnyResult(error=False, info='Success', result=result)
                except NoResultFound:
                    result = Result.AnyResult(error=True, info='NoResultFound', result=None)
                except MultipleResultsFound:
                    result = Result.IntResult(error=True, info='MultipleResultsFound', result=-1)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result

    async def set_gacha_pool(self, user_id, pool_id):
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    session_result = await session.execute(
                        select(UserGacha).where(UserGacha.user_id == user_id)
                    )
                    user_gacha = session_result.scalar_one()
                    user_gacha.gacha_pool = pool_id
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

    async def set_break_even(self, user_id, break_even):
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            try:
                async with session.begin():
                    session_result = await session.execute(
                        select(UserGacha).where(UserGacha.user_id == user_id)
                    )
                    user_gacha = session_result.scalar_one()
                    user_gacha.gacha_break_even = break_even
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

    async def get_gacha_user(self, user_id) -> Result.AnyResult:
        async_session = DBSession().get_async_session()
        async with async_session() as session:
            async with session.begin():
                try:
                    session_result = await session.execute(select(UserGacha).filter(UserGacha.user_id == user_id))
                    user_gacha = session_result.scalar_one()
                    result = Result.AnyResult(error=False, info='Success', result=user_gacha)
                except NoResultFound:
                    result = await self.__add(UserGacha, user_id)
                except MultipleResultsFound:
                    result = Result.AnyResult(error=True, info='MultipleResultsFound', result=None)
                except Exception as e:
                    result = Result.AnyResult(error=True, info=repr(e), result=None)
        return result