import nonebot
from sqlalchemy import Sequence, ForeignKey
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, func, SmallInteger, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from .models import Base

global_config = nonebot.get_driver().config
GAME_PREFIX = 'arknights'
TABLE_PREFIX = "_".join([global_config.db_table_prefix, GAME_PREFIX])


# 干员表
class Operator(Base):
    __tablename__ = f'{TABLE_PREFIX}_operator'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    operator_id = Column(Integer, Sequence('operator_id_seq'), primary_key=True, nullable=False, index=True,
                         unique=True)
    operator_name = Column(String(64), nullable=True, comment='干员代号')
    operator_en_name = Column(String(64), nullable=True, comment='干员英文代号')
    operator_no = Column(String(64), nullable=True, comment='干员编号')
    operator_avatar = Column(String(64), nullable=True, comment='干员头像')
    operator_rarity = Column(SmallInteger, nullable=True, comment='干员稀有度')
    operator_class = Column(SmallInteger, nullable=True,
                            comment='干员类型: 先锋: 1,近卫: 2,重装: 3,狙击: 4,术师: 5,辅助: 6,医疗: 7,特种: 8')
    available = Column(SmallInteger, default=0, comment='干员可用与否')
    in_limit = Column(SmallInteger, default=0, comment='干员限定与否')

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    # operator_building_skills = relationship('OperatorBuildingSkill', back_populates='operator',
    #                                         cascade="all, delete", passive_deletes=True)
    # operator_details = relationship("OperatorDetail", cascade="all, delete", passive_deletes=True,
    #                                 back_populates="operator")
    # operator_evolve_costs = relationship("OperatorEvolveCosts", cascade="all, delete", passive_deletes=True,
    #                                      back_populates="operator")
    # operator_potentials = relationship("OperatorPotential", cascade="all, delete", passive_deletes=True,
    #                                    back_populates="operator")
    # operator_skills = relationship("OperatorSkill", cascade="all, delete", passive_deletes=True,
    #                                back_populates="operator")
    # operator_skins = relationship("OperatorSkins", cascade="all, delete", passive_deletes=True,
    #                               back_populates="operator")
    # operator_stories = relationship("OperatorStories", cascade="all, delete", passive_deletes=True,
    #                               back_populates="operator")

    def __init__(self, operator_no, operator_name, operator_en_name, operator_avatar, operator_rarity, operator_class,
                 available, in_limit, created_at=None, updated_at=None):
        self.operator_name = operator_name
        self.operator_no = operator_no
        self.operator_en_name = operator_en_name
        self.operator_avatar = operator_avatar
        self.operator_rarity = operator_rarity
        self.operator_class = operator_class
        self.available = available
        self.in_limit = in_limit
        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<Operator(operator_name='{self.operator_name}', operator_class='{self.operator_class}', operator_rarity='{self.operator_rarity}')>"


# 干员基建技表
class OperatorBuildingSkill(Base):
    __tablename__ = f'{TABLE_PREFIX}_operator_building_skill'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    bs_id = Column(Integer, Sequence('bs_id_seq'), primary_key=True, nullable=False, index=True,
                   unique=True)
    # operator_id = Column(Integer, ForeignKey(f'{TABLE_PREFIX}_operator.id'), nullable=False)
    operator_id = Column(Integer, nullable=True)
    bs_unlocked = Column(Integer, nullable=True)
    bs_name = Column(String(64), nullable=True, comment='基建技能名称')
    bs_desc = Column(String(255), nullable=True, comment='基建技能描述')

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    # operator = relationship("Operator", back_populates="operator_building_skills")

    def __init__(self, operator_id, bs_unlocked, bs_name, bs_desc, created_at=None, updated_at=None):
        self.operator_id = operator_id
        self.bs_unlocked = bs_unlocked
        self.bs_name = bs_name
        self.bs_desc = bs_desc
        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<OperatorBuildingSkill(operator_id='{self.operator_id}', bs_name='{self.bs_name}', bs_desc='{self.bs_desc}')>"


# 干员详情表
class OperatorDetail(Base):
    __tablename__ = f'{TABLE_PREFIX}_operator_detail'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    operator_detail_id = Column(Integer, Sequence('operator_detail_id_seq'), primary_key=True, nullable=False,
                                index=True,
                                unique=True)
    # operator_id = Column(Integer, ForeignKey(f'{TABLE_PREFIX}_operator.id'), nullable=False)
    operator_id = Column(Integer, nullable=True)
    operator_desc = Column(String(255), nullable=True)
    operator_usage = Column(String(255), nullable=True)
    operator_quote = Column(String(255), nullable=True)
    operator_token = Column(String(255), nullable=True)
    max_level = Column(String(64), nullable=True)
    max_hp = Column(String(64), nullable=True)
    attack = Column(String(64), nullable=True)
    defense = Column(String(64), nullable=True)
    magic_resistance = Column(String(64), nullable=True)
    cost = Column(String(64), nullable=True)
    block_count = Column(String(64), nullable=True)
    attack_time = Column(String(64), nullable=True)
    respawn_time = Column(String(64), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    # operator = relationship("Operator", back_populates="operator_details")

    def __init__(self, operator_id, operator_desc, operator_usage, operator_quote, operator_token, max_level, max_hp,
                 attack, defense, magic_resistance, cost, block_count, attack_time, respawn_time, created_at=None,
                 updated_at=None):
        self.operator_id = operator_id
        self.operator_desc = operator_desc
        self.operator_usage = operator_usage
        self.operator_quote = operator_quote
        self.operator_token = operator_token
        self.attack = attack
        self.defense = defense
        self.magic_resistance = magic_resistance
        self.cost = cost
        self.block_count = block_count
        self.attack_time = attack_time
        self.respawn_time = respawn_time
        self.max_level = max_level
        self.max_hp = max_hp

        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<OperatorDetail(operator_id='{self.operator_id}', operator_desc='{self.operator_desc}', " \
               f"operator_usage='{self.operator_usage}', operator_token='{self.operator_token}', " \
               f"operator_quote='{self.operator_quote}', attack='{self.attack}', defense='{self.defense}', " \
               f"magic_resistance='{self.magic_resistance}, cost='{self.cost}', block_count='{self.block_count}', " \
               f"attack_time='{self.attack_time}, respawn_time='{self.respawn_time}', max_level='{self.max_level}', " \
               f"max_hp='{self.max_hp}')>"


# 干员精英化所需材料表
class OperatorEvolveCosts(Base):
    __tablename__ = f'{TABLE_PREFIX}_operator_evolve_costs'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    cost_id = Column(Integer, Sequence('cost_id_seq'), primary_key=True, nullable=False, index=True,
                     unique=True)
    # operator_id = Column(Integer, ForeignKey(f'{TABLE_PREFIX}_operator.id'), nullable=False)
    operator_id = Column(Integer, nullable=True)
    evolve_level = Column(SmallInteger, nullable=True)

    use_material_id = Column(Integer, nullable=True)
    use_number = Column(SmallInteger, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    # operator = relationship("Operator", back_populates="operator_evolve_costs")

    def __init__(self, evolve_level, operator_id, use_material_id, use_number, created_at=None, updated_at=None):
        self.evolve_level = evolve_level
        self.operator_id = operator_id
        self.use_material_id = use_material_id
        self.use_number = use_number

        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<OperatorEvolveCosts(operator_id='{self.operator_id}', evolve_level='{self.evolve_level}', use_material_id='{self.use_material_id}', use_number='{self.use_number}')>"


# 干员潜能表
class OperatorPotential(Base):
    __tablename__ = f'{TABLE_PREFIX}_operator_potential'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    potential_id = Column(Integer, Sequence('potential_id_seq'), primary_key=True, nullable=False, index=True,
                          unique=True)
    # operator_id = Column(Integer, ForeignKey(f'{TABLE_PREFIX}_operator.id'), nullable=False)
    operator_id = Column(Integer, nullable=True)
    potential_desc = Column(String(255), nullable=True)
    potential_rank = Column(SmallInteger, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    # operator = relationship("Operator", back_populates="operator_potentials")

    def __init__(self, operator_id, potential_desc, potential_rank, created_at=None, updated_at=None):
        self.potential_desc = potential_desc
        self.operator_id = operator_id
        self.potential_rank = potential_rank

        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<OperatorPotential(operator_id='{self.operator_id}', potential_rank='{self.potential_rank}', potential_desc='{self.potential_desc}')>"


# 干员技能表
class OperatorSkill(Base):
    __tablename__ = f'{TABLE_PREFIX}_operator_skill'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    skill_id = Column(Integer, Sequence('skill_id_seq'), primary_key=True, nullable=False, index=True,
                      unique=True)
    # operator_id = Column(Integer, ForeignKey(f'{TABLE_PREFIX}_operator.id'), nullable=False)
    operator_id = Column(Integer, nullable=True)
    skill_index = Column(SmallInteger, nullable=True)

    skill_name = Column(String(255), nullable=True)
    skill_icon = Column(String(255), nullable=True)
    skill_no = Column(String(255), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    # operator = relationship("Operator", back_populates="operator_skills")
    # skill_description = relationship("OperatorSkillDescription", cascade="all, delete", passive_deletes=True,
    #                                  back_populates="skill")
    # skill_mastery_costs = relationship("OperatorSkillMasteryCosts", cascade="all, delete", passive_deletes=True,
    #                                    back_populates="skill")

    def __init__(self, operator_id, skill_index, skill_name, skill_icon, skill_no, created_at=None, updated_at=None):
        self.skill_index = skill_index
        self.operator_id = operator_id
        self.skill_name = skill_name
        self.skill_icon = skill_icon
        self.skill_no = skill_no

        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<OperatorSkill(operator_id='{self.operator_id}', skill_index='{self.skill_index}', skill_name='{self.skill_name}', " \
               f"skill_icon='{self.skill_icon}', skill_no='{self.skill_no}')>"


# 干员技能描述表
class OperatorSkillDescription(Base):
    __tablename__ = f'{TABLE_PREFIX}_operator_skill_description'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    desc_id = Column(Integer, Sequence('desc_id_seq'), primary_key=True, nullable=False, index=True,
                     unique=True)
    # skill_id = Column(Integer, ForeignKey(f'{TABLE_PREFIX}_operator_skill.id'), nullable=False)
    skill_id = Column(Integer, nullable=True)
    skill_level = Column(SmallInteger, nullable=True)
    skill_type = Column(SmallInteger, nullable=True)
    sp_type = Column(SmallInteger, nullable=True)
    sp_init = Column(Integer, nullable=True)
    sp_cost = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=True)
    max_charge = Column(SmallInteger, nullable=True)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    # skill = relationship("OperatorSkill", back_populates="skill_description")

    def __init__(self, skill_id, skill_level, skill_type, sp_type, sp_init, sp_cost, duration, description, max_charge,
                 created_at=None, updated_at=None):
        self.skill_id = skill_id
        self.skill_level = skill_level
        self.skill_type = skill_type
        self.sp_type = sp_type
        self.sp_init = sp_init
        self.sp_cost = sp_cost
        self.duration = duration
        self.description = description
        self.max_charge = max_charge

        self.created_at = created_at
        self.updated_at = updated_at


    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<OperatorSkillDescription(skill_id='{self.skill_id}', skill_level='{self.skill_level}', " \
               f"skill_type='{self.skill_type}', sp_type='{self.sp_type}', sp_init='{self.sp_init}', " \
               f"sp_cost='{self.sp_cost}', duration='{self.duration}', description='{self.description}', " \
               f"max_charge='{self.max_charge})>"


# 干员技能升级材料表
class OperatorSkillMasteryCosts(Base):
    __tablename__ = f'{TABLE_PREFIX}_operator_skill_mastery_costs'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    cost_id = Column(Integer, Sequence('cost_id_seq'), primary_key=True, nullable=False, index=True,
                     unique=True)
    # skill_id = Column(Integer, ForeignKey(f'{TABLE_PREFIX}_operator_skill.id'), nullable=False)
    skill_id = Column(Integer, nullable=True)
    mastery_level = Column(SmallInteger, nullable=True)
    use_material_id = Column(Integer, nullable=True)
    use_number = Column(Integer, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    # skill = relationship("OperatorSkill", back_populates="skill_mastery_costs")

    def __init__(self, skill_id, mastery_level, use_material_id, use_number, created_at=None, updated_at=None):
        self.skill_id = skill_id
        self.mastery_level = mastery_level
        self.use_material_id = use_material_id
        self.use_number = use_number

        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<OperatorSkillMasteryCosts(skill_id='{self.skill_id}', mastery_level='{self.mastery_level}', " \
               f"use_material_id='{self.use_material_id}', use_number='{self.use_number}')>"


# 干员皮肤表
class OperatorSkins(Base):
    __tablename__ = f'{TABLE_PREFIX}_operator_skins'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    skin_id = Column(Integer, Sequence('skin_id_seq'), primary_key=True, nullable=False, index=True,
                     unique=True)
    # operator_id = Column(Integer, ForeignKey(f'{TABLE_PREFIX}_operator.id'), nullable=False)
    operator_id = Column(Integer, nullable=True)
    skin_image = Column(String(64), nullable=True)
    skin_name = Column(String(64), nullable=True)
    skin_drawer = Column(String(64), nullable=True)
    skin_group = Column(String(64), nullable=True)
    skin_type = Column(SmallInteger, nullable=True)
    skin_usage = Column(String(255), nullable=True)
    skin_desc = Column(String(255), nullable=True)
    skin_source = Column(String(64), nullable=True)
    skin_content = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    # operator = relationship("Operator", back_populates="operator_skins")

    def __init__(self, operator_id, skin_image, skin_type, skin_name, skin_drawer, skin_group, skin_content, skin_usage,
                 skin_desc, skin_source, created_at=None, updated_at=None):
        self.operator_id = operator_id
        self.skin_image = skin_image
        self.skin_type = skin_type
        self.skin_name = skin_name
        self.skin_drawer = skin_drawer
        self.skin_group = skin_group
        self.skin_content = skin_content
        self.skin_usage = skin_usage
        self.skin_desc = skin_desc
        self.skin_source = skin_source

        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<OperatorSkins(operator_id='{self.operator_id}', skin_image='{self.skin_image}', " \
               f"skin_type='{self.skin_type}', skin_name='{self.skin_name}', skin_drawer='{self.skin_drawer}', " \
               f"skin_group='{self.skin_group}', skin_content='{self.skin_content}', skin_usage='{self.skin_usage}', " \
               f"skin_desc='{self.skin_desc}, skin_source='{self.skin_source}')>"


# 干员背景故事表
class OperatorStories(Base):
    __tablename__ = f'{TABLE_PREFIX}_operator_stories'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    story_id = Column(Integer, Sequence('story_id_seq'), primary_key=True, nullable=False, index=True,
                      unique=True)
    # operator_id = Column(Integer, ForeignKey(f'{TABLE_PREFIX}_operator.id'), nullable=False)
    operator_id = Column(Integer, nullable=True)
    story_title = Column(String(64), nullable=True)
    story_text = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    # operator = relationship("Operator", back_populates="operator_stories")

    def __init__(self, operator_id, story_title, story_text, created_at=None, updated_at=None):
        self.operator_id = operator_id
        self.story_title = story_title
        self.story_text = story_text

        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<OperatorStories(operator_id='{self.operator_id}', story_title='{self.story_title}', " \
               f"story_text='{self.story_text}')>"


# 干员标签表
class OperatorTagsRelation(Base):
    __tablename__ = f'{TABLE_PREFIX}_operator_tags_relation'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    rel_id = Column(Integer, Sequence('rel_id_seq'), primary_key=True, nullable=False, index=True,
                    unique=True)
    operator_rarity = Column(SmallInteger, nullable=True)
    operator_name = Column(String(255), nullable=True)
    operator_tags = Column(String(255), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    # operator = relationship("Operator", back_populates="operator_stories")

    def __init__(self, operator_name, operator_rarity, operator_tags, created_at=None, updated_at=None):
        self.operator_name = operator_name
        self.operator_rarity = operator_rarity
        self.operator_tags = operator_tags

        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<OperatorTagsRelation(operator_name='{self.operator_name}', operator_rarity='{self.operator_rarity}', " \
               f"operator_tags='{self.operator_tags}')>"


# 干员天赋表
class OperatorTalents(Base):
    __tablename__ = f'{TABLE_PREFIX}_operator_talents'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    talents_id = Column(Integer, Sequence('talents_id_seq'), primary_key=True, nullable=False, index=True,
                        unique=True)
    # operator_id = Column(Integer, ForeignKey(f'{TABLE_PREFIX}_operator.id'), nullable=False)
    operator_id = Column(Integer, nullable=True)
    talents_name = Column(String(64), nullable=True)
    talents_desc = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    # operator = relationship("Operator", back_populates="operator_stories")

    def __init__(self, operator_id, talents_name, talents_desc, created_at=None, updated_at=None):
        self.operator_id = operator_id
        self.talents_name = talents_name
        self.talents_desc = talents_desc

        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<OperatorTalents(operator_id='{self.operator_id}', talents_name='{self.talents_name}', " \
               f"talents_desc='{self.talents_desc}')>"


# 干员语音表
class OperatorVoice(Base):
    __tablename__ = f'{TABLE_PREFIX}_operator_voice'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    voice_id = Column(Integer, Sequence('voice_id_seq'), primary_key=True, nullable=False, index=True,
                      unique=True)
    # operator_id = Column(Integer, ForeignKey(f'{TABLE_PREFIX}_operator.id'), nullable=False)
    operator_id = Column(Integer, nullable=True)
    voice_title = Column(String(255), nullable=True)
    voice_no = Column(String(255), nullable=True)
    voice_text = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    # operator = relationship("Operator", back_populates="operator_stories")

    def __init__(self, operator_id, voice_title, voice_text, voice_no, created_at=None, updated_at=None):
        self.operator_id = operator_id
        self.voice_title = voice_title
        self.voice_text = voice_text
        self.voice_no = voice_no

        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<OperatorVoice(operator_id='{self.operator_id}', voice_title='{self.voice_title}', " \
               f"voice_text='{self.voice_text}, voice_no='{self.voice_no}')>"


# 材料表
class Material(Base):
    __tablename__ = f'{TABLE_PREFIX}_material'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    material_id = Column(Integer, primary_key=True, nullable=False, index=True, unique=True)
    material_name = Column(String(255), nullable=True)
    material_icon = Column(String(255), nullable=True)
    material_desc = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    def __init__(self, material_id, material_name, material_icon, material_desc, created_at=None, updated_at=None):
        self.material_id = material_id
        self.material_name = material_name
        self.material_icon = material_icon
        self.material_desc = material_desc

        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<Material(material_name='{self.material_name}', material_icon='{self.material_icon}', " \
               f"material_desc='{self.material_desc}')>"


# 材料制作表
class MaterialMade(Base):
    __tablename__ = f'{TABLE_PREFIX}_material_made'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    made_id = Column(Integer, Sequence('made_id_seq'), primary_key=True, nullable=False, index=True,
                     unique=True)
    material_id = Column(Integer, nullable=True)
    use_material_id = Column(Integer, nullable=True)
    use_number = Column(Integer, nullable=True)
    made_type = Column(String(64), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    def __init__(self, material_id, use_material_id, use_number, made_type, created_at=None, updated_at=None):
        self.material_id = material_id
        self.use_material_id = use_material_id
        self.use_number = use_number
        self.made_type = made_type

        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<MaterialMade(material_id='{self.material_id}', use_material_id='{self.use_material_id}', " \
               f"use_number='{self.use_number}, made_type='{self.made_type}')>"


# 材料掉落表
class MaterialSource(Base):
    __tablename__ = f'{TABLE_PREFIX}_material_source'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    source_id = Column(Integer, Sequence('source_id_seq'), primary_key=True, nullable=False, index=True,
                       unique=True)
    material_id = Column(Integer, nullable=True)
    source_place = Column(String(64), nullable=True)
    source_rate = Column(String(64), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    def __init__(self, material_id, source_place, source_rate, created_at=None, updated_at=None):
        self.material_id = material_id
        self.source_place = source_place
        self.source_rate = source_rate

        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<MaterialSource(material_id='{self.material_id}', source_place='{self.source_place}', " \
               f"source_rate='{self.source_rate}')>"


# 关卡表
class Stage(Base):
    __tablename__ = f'{TABLE_PREFIX}_stage'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    stage_id = Column(String(64), primary_key=True, nullable=False, index=True, unique=True)
    stage_code = Column(String(64), nullable=True)
    stage_name = Column(String(64), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    def __init__(self, stage_id, stage_code, stage_name, created_at=None, updated_at=None):
        self.stage_id = stage_id
        self.stage_code = stage_code
        self.stage_name = stage_name

        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<Stage(stage_id='{self.stage_id}', stage_code='{self.stage_code}', " \
               f"stage_name='{self.stage_name}')>"


class OperatorGachaConfig(Base):
    __tablename__ = f'{TABLE_PREFIX}_operator_gacha_config'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    id = Column(Integer, Sequence('id_seq'), primary_key=True, nullable=False, index=True,
                unique=True)
    operator_name = Column(String(255), nullable=True)
    operator_type = Column(SmallInteger, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    def __init__(self, operator_name, operator_type, created_at=None, updated_at=None):
        self.operator_name = operator_name
        self.operator_type = operator_type

        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<OperatorGachaConfig(id='{self.id}', operator_name='{self.operator_name}', " \
               f"operator_type='{self.operator_type}')>"


class UserGacha(Base):
    __tablename__ = f'{TABLE_PREFIX}_user_gacha'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    user_gacha_id = Column(Integer, Sequence('user_gacha_id_seq'), primary_key=True, nullable=False, index=True,
                     unique=True)
    user_id = Column(Integer, nullable=False)
    gacha_break_even = Column(Integer, default=0)
    gacha_pool = Column(Integer, default=1)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    def __init__(self, user_id, gacha_break_even=0, gacha_pool=1, created_at=None, updated_at=None):
        self.user_id = user_id
        self.gacha_break_even = gacha_break_even
        self.gacha_pool = gacha_pool

        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<UserGacha(user_id='{self.user_id}', gacha_break_even='{self.gacha_break_even}', " \
               f"gacha_pool='{self.gacha_pool}')>"


class OperatorPool(Base):
    __tablename__ = f'{TABLE_PREFIX}_operator_pool'
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8mb4'}

    # 表结构
    pool_id = Column(Integer, Sequence('pool_id_seq'), primary_key=True, nullable=False, index=True,
                     unique=True)
    pool_name = Column(String(255), nullable=True)
    pickup_6 = Column(String(255), nullable=True)
    pickup_5 = Column(String(255), nullable=True)
    pickup_4 = Column(String(255), nullable=True)
    pickup_s = Column(String(255), nullable=True)
    limit_pool = Column(SmallInteger, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    def __init__(self, pool_name, pickup_6, pickup_5, pickup_4, pickup_s, limit_pool, created_at=None, updated_at=None):
        self.pool_name = pool_name
        self.pickup_6 = pickup_6
        self.pickup_5 = pickup_5
        self.pickup_4 = pickup_4
        self.pickup_s = pickup_s
        self.limit_pool = limit_pool

        self.created_at = created_at
        self.updated_at = updated_at

    def __getitem__(self, item):
        return eval(f'self.{item}')

    def __repr__(self):
        return f"<OperatorPool(pool_name='{self.pool_name}', pickup_6='{self.pickup_6}', " \
               f"pickup_5='{self.pickup_5}, pickup_4='{self.pickup_4}, pickup_s='{self.pickup_s}, limit_pool='{self.limit_pool}')>"
