"""角色关系和组织管理数据模型"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from app.database import Base
import uuid


class RelationshipType(Base):
    """关系类型定义表"""
    __tablename__ = "relationship_types"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), nullable=False, comment="Nome da relação")
    category = Column(String(20), nullable=False, comment="Categoria: family/social/hostile/professional")
    reverse_name = Column(String(50), comment="Nome da relação inversa")
    intimacy_range = Column(String(20), comment="Faixa de intimidade: high/medium/low")
    icon = Column(String(50), comment="Identificador do ícone")
    description = Column(Text, comment="Descrição da relação")
    created_at = Column(DateTime, server_default=func.now(), comment="Data de criação")
    
    def __repr__(self):
        return f"<RelationshipType(id={self.id}, name={self.name}, category={self.category})>"


class CharacterRelationship(Base):
    """角色关系表"""
    __tablename__ = "character_relationships"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="ID da relação")
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True, comment="ID do projeto")
    
    # 关系双方
    character_from_id = Column(String(36), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True, comment="ID do personagem A")
    character_to_id = Column(String(36), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True, comment="ID do personagem B")
    
    # 关系类型
    relationship_type_id = Column(Integer, ForeignKey("relationship_types.id"), index=True, comment="ID do tipo de relação")
    relationship_name = Column(String(100), comment="Nome personalizado da relação")
    
    # 关系属性
    intimacy_level = Column(Integer, default=50, comment="Intimidade: -100 a 100")
    status = Column(String(20), default="active", comment="Status: active/broken/past/complicated")
    description = Column(Text, comment="Descrição detalhada da relação")
    
    # 故事时间线
    started_at = Column(String(100), comment="Início da relação (tempo da história)")
    ended_at = Column(String(100), comment="Fim da relação (tempo da história)")
    
    # 来源标识
    source = Column(String(20), default="ai", comment="Origem: ai/manual/imported")
    
    created_at = Column(DateTime, server_default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Data de atualização")
    
    def __repr__(self):
        return f"<CharacterRelationship(id={self.id}, from={self.character_from_id}, to={self.character_to_id})>"


class Organization(Base):
    """组织详情表"""
    __tablename__ = "organizations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="ID da organização")
    character_id = Column(String(36), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, unique=True, comment="ID do personagem associado")
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True, comment="ID do projeto")
    
    # 组织层级
    parent_org_id = Column(String(36), ForeignKey("organizations.id", ondelete="SET NULL"), comment="ID da organização-mãe")
    level = Column(Integer, default=0, comment="Nível da organização")
    
    # 组织属性
    power_level = Column(Integer, default=50, comment="Nível de poder: 0-100")
    member_count = Column(Integer, default=0, comment="Quantidade de membros")
    location = Column(Text, comment="Localização")
    
    # 组织特色
    motto = Column(String(200), comment="Lema/propósito")
    color = Column(String(100), comment="Cor representativa")
    
    created_at = Column(DateTime, server_default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Data de atualização")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, character_id={self.character_id})>"


class OrganizationMember(Base):
    """组织成员关系表"""
    __tablename__ = "organization_members"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="ID da relação de membro")
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True, comment="ID da organização")
    character_id = Column(String(36), ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True, comment="ID do personagem")
    
    # 职位信息
    position = Column(String(100), nullable=False, comment="Nome do cargo")
    rank = Column(Integer, default=0, comment="Nível do cargo")
    
    # 成员状态
    status = Column(String(20), default="active", comment="Status: active/retired/expelled/deceased")
    joined_at = Column(String(100), comment="Entrada (tempo da história)")
    left_at = Column(String(100), comment="Saída (tempo da história)")
    
    # 成员属性
    loyalty = Column(Integer, default=50, comment="Lealdade: 0-100")
    contribution = Column(Integer, default=0, comment="Contribuição: 0-100")
    
    # 来源标识
    source = Column(String(20), default="ai", comment="Origem: ai/manual")
    
    notes = Column(Text, comment="Observações")
    created_at = Column(DateTime, server_default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Data de atualização")
    
    def __repr__(self):
        return f"<OrganizationMember(id={self.id}, org={self.organization_id}, char={self.character_id})>"