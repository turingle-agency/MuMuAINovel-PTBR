"""职业数据模型"""
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Index
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Career(Base):
    """职业表"""
    __tablename__ = "careers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    # 基本信息
    name = Column(String(100), nullable=False, comment="Nome da carreira")
    type = Column(String(20), nullable=False, comment="Tipo de carreira: main (principal)/sub (secundária)")
    description = Column(Text, comment="Descrição da carreira")
    category = Column(String(50), comment="Categoria da carreira (ex.: combate, produção, suporte)")
    
    # 阶段设定
    stages = Column(Text, nullable=False, comment="Lista de estágios da carreira (JSON): [{level:1, name:'', description:''}, ...]")
    max_stage = Column(Integer, nullable=False, default=10, comment="Número máximo de estágios")
    
    # 职业特性
    requirements = Column(Text, comment="Requisitos/restrições da carreira")
    special_abilities = Column(Text, comment="Descrição das habilidades especiais")
    worldview_rules = Column(Text, comment="Vínculo com as regras do mundo")
    
    # 职业属性加成（可选，JSON格式）
    attribute_bonuses = Column(Text, comment="Bônus de atributos (JSON): {strength: '+10%', intelligence: '+5%'}")
    
    # 元数据
    source = Column(String(20), default='ai', comment="Origem: ai/manual")
    created_at = Column(DateTime, server_default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Data de atualização")
    
    __table_args__ = (
        Index('idx_project_id', 'project_id'),
        Index('idx_type', 'type'),
    )
    
    def __repr__(self):
        return f"<Career(id={self.id}, name={self.name}, type={self.type})>"


class CharacterCareer(Base):
    """角色职业关联表"""
    __tablename__ = "character_careers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    character_id = Column(String(36), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False)
    career_id = Column(String(36), ForeignKey("careers.id", ondelete="CASCADE"), nullable=False)
    career_type = Column(String(20), nullable=False, comment="main (principal)/sub (secundária)")
    
    # 阶段进度
    current_stage = Column(Integer, nullable=False, default=1, comment="Estágio atual (valor correspondente na carreira)")
    stage_progress = Column(Integer, default=0, comment="Progresso dentro do estágio (0-100)")
    
    # 时间记录
    started_at = Column(String(100), comment="Início do treinamento (linha do tempo da história)")
    reached_current_stage_at = Column(String(100), comment="Momento em que alcançou o estágio atual")
    
    # 备注
    notes = Column(Text, comment="Observações (ex.: aprendizados, eventos especiais)")
    
    created_at = Column(DateTime, server_default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Data de atualização")
    
    __table_args__ = (
        Index('idx_character_id', 'character_id'),
        Index('idx_career_type', 'career_type'),
        Index('idx_character_career', 'character_id', 'career_id', unique=True),
    )
    
    def __repr__(self):
        return f"<CharacterCareer(character_id={self.character_id}, career_id={self.career_id}, type={self.career_type})>"