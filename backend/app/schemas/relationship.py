"""关系管理相关的Pydantic模型"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


# ============ 关系类型相关 ============

class RelationshipTypeResponse(BaseModel):
    """关系类型响应模型"""
    id: int
    name: str
    category: str
    reverse_name: Optional[str] = None
    intimacy_range: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============ 角色关系相关 ============

class CharacterRelationshipBase(BaseModel):
    """角色关系基础模型"""
    relationship_type_id: Optional[int] = Field(None, description="ID do tipo de relação")
    relationship_name: Optional[str] = Field(None, description="Nome personalizado da relação")
    intimacy_level: int = Field(50, ge=-100, le=100, description="Intimidade: -100 a 100")
    status: str = Field("active", description="Status: active/broken/past/complicated")
    description: Optional[str] = Field(None, description="Descrição da relação")
    started_at: Optional[str] = Field(None, description="Início da relação (tempo da história)")
    ended_at: Optional[str] = Field(None, description="Fim da relação")


class CharacterRelationshipCreate(CharacterRelationshipBase):
    """创建角色关系的请求模型"""
    project_id: str = Field(..., description="ID do projeto")
    character_from_id: str = Field(..., description="ID do personagem A")
    character_to_id: str = Field(..., description="ID do personagem B")


class CharacterRelationshipUpdate(BaseModel):
    """更新角色关系的请求模型"""
    relationship_type_id: Optional[int] = None
    relationship_name: Optional[str] = None
    intimacy_level: Optional[int] = Field(None, ge=-100, le=100)
    status: Optional[str] = None
    description: Optional[str] = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None


class CharacterRelationshipResponse(CharacterRelationshipBase):
    """角色关系响应模型"""
    id: str
    project_id: str
    character_from_id: str
    character_to_id: str
    source: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class RelationshipGraphNode(BaseModel):
    """关系图谱节点"""
    id: str
    name: str
    type: str  # character / organization
    role_type: Optional[str] = None
    avatar: Optional[str] = None


class RelationshipGraphLink(BaseModel):
    """关系图谱连线"""
    source: str
    target: str
    relationship: str
    intimacy: int
    status: str


class RelationshipGraphData(BaseModel):
    """关系图谱数据"""
    nodes: List[RelationshipGraphNode]
    links: List[RelationshipGraphLink]


# ============ 组织相关 ============

class OrganizationBase(BaseModel):
    """组织基础模型"""
    parent_org_id: Optional[str] = Field(None, description="ID da organização-mãe")
    level: int = Field(0, description="Nível da organização")
    power_level: int = Field(50, ge=0, le=100, description="Nível de poder")
    location: Optional[str] = Field(None, description="Localização")
    motto: Optional[str] = Field(None, description="Propósito da organização")
    color: Optional[str] = Field(None, description="Cor representativa")


class OrganizationCreate(OrganizationBase):
    """创建组织的请求模型"""
    character_id: str = Field(..., description="ID do personagem associado (registro da organização)")
    project_id: str = Field(..., description="ID do projeto")


class OrganizationUpdate(BaseModel):
    """更新组织的请求模型"""
    parent_org_id: Optional[str] = None
    level: Optional[int] = None
    power_level: Optional[int] = Field(None, ge=0, le=100)
    location: Optional[str] = None
    motto: Optional[str] = None
    color: Optional[str] = None


class OrganizationResponse(OrganizationBase):
    """组织响应模型"""
    id: str
    character_id: str
    project_id: str
    member_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class OrganizationDetailResponse(BaseModel):
    """组织详情响应（包含基本信息）"""
    id: str
    character_id: str
    name: str
    type: Optional[str] = None
    purpose: Optional[str] = None
    member_count: int
    power_level: int
    location: Optional[str] = None
    motto: Optional[str] = None
    color: Optional[str] = None


# ============ 组织成员相关 ============

class OrganizationMemberBase(BaseModel):
    """组织成员基础模型"""
    position: str = Field(..., description="Nome do cargo")
    rank: int = Field(0, description="Nível do cargo")
    status: str = Field("active", description="Status: active/retired/expelled/deceased")
    joined_at: Optional[str] = Field(None, description="Entrada (tempo da história)")
    left_at: Optional[str] = Field(None, description="Saída")
    loyalty: int = Field(50, ge=0, le=100, description="Lealdade")
    contribution: int = Field(0, ge=0, le=100, description="Contribuição")
    notes: Optional[str] = Field(None, description="Observações")


class OrganizationMemberCreate(OrganizationMemberBase):
    """创建组织成员的请求模型"""
    character_id: str = Field(..., description="ID do personagem")


class OrganizationMemberUpdate(BaseModel):
    """更新组织成员的请求模型"""
    position: Optional[str] = None
    rank: Optional[int] = None
    status: Optional[str] = None
    joined_at: Optional[str] = None
    left_at: Optional[str] = None
    loyalty: Optional[int] = Field(None, ge=0, le=100)
    contribution: Optional[int] = Field(None, ge=0, le=100)
    notes: Optional[str] = None


class OrganizationMemberResponse(OrganizationMemberBase):
    """组织成员响应模型"""
    id: str
    organization_id: str
    character_id: str
    source: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class OrganizationMemberDetailResponse(BaseModel):
    """组织成员详情响应（包含角色信息）"""
    id: str
    character_id: str
    character_name: str
    position: str
    rank: int
    loyalty: int
    contribution: int
    status: str
    joined_at: Optional[str] = None
    left_at: Optional[str] = None
    notes: Optional[str] = None