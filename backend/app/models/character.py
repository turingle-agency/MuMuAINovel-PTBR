"""角色数据模型"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Character(Base):
    """角色表（包括角色和组织）"""
    __tablename__ = "characters"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    
    # 基本信息
    name = Column(String(100), nullable=False, comment="Nome do personagem/organização")
    age = Column(String(50), comment="Idade")
    gender = Column(String(50), comment="Gênero")
    is_organization = Column(Boolean, default=False, comment="É uma organização")
    
    # 角色类型：protagonist(主角)/supporting(配角)/antagonist(反派)
    role_type = Column(String(50), comment="Tipo de personagem")
    
    # 角色详细信息
    personality = Column(Text, comment="Personalidade / características da organização")
    background = Column(Text, comment="História de fundo")
    appearance = Column(Text, comment="Descrição da aparência")
    relationships = Column(Text, comment="Relações entre personagens (JSON)")
    
    # 组织特有字段
    organization_type = Column(String(100), comment="Tipo de organização")
    organization_purpose = Column(String(500), comment="Propósito da organização")
    organization_members = Column(Text, comment="Membros da organização (JSON)")
    
    # 角色/组织存活状态
    status = Column(String(20), default="active", comment="Status: active/deceased/missing/retired/destroyed")
    status_changed_chapter = Column(Integer, comment="Capítulo da mudança de status")
    
    # 心理状态追踪（由章节分析自动更新）
    current_state = Column(Text, comment="Estado psicológico atual do personagem (atualizado pela análise)")
    state_updated_chapter = Column(Integer, comment="Capítulo da última atualização do estado psicológico")
    
    # 职业相关字段（冗余字段，用于提升查询性能）
    main_career_id = Column(String(36), ForeignKey("careers.id", ondelete="SET NULL"), comment="ID da carreira principal")
    main_career_stage = Column(Integer, comment="Estágio atual da carreira principal")
    sub_careers = Column(Text, comment="Lista de carreiras secundárias (JSON): [{\"career_id\": \"xxx\", \"stage\": 3}, ...]")
    
    # 其他
    avatar_url = Column(String(500), comment="URL do avatar")
    traits = Column(Text, comment="Etiquetas de traços (JSON)")
    
    created_at = Column(DateTime, server_default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Data de atualização")
    
    def __repr__(self):
        entity_type = "organização" if self.is_organization else "personagem"
        return f"<Character(id={self.id}, name={self.name}, type={entity_type})>"