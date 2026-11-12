"""角色相关的Pydantic模型"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class CharacterBase(BaseModel):
    """角色基础模型"""
    name: str = Field(..., description="Nome do personagem/organização")
    age: Optional[str] = Field(None, description="Idade")
    gender: Optional[str] = Field(None, description="Gênero")
    is_organization: bool = Field(False, description="É uma organização")
    role_type: Optional[str] = Field(None, description="Tipo de personagem: protagonist/supporting/antagonist")
    personality: Optional[str] = Field(None, description="Personalidade / características da organização")
    background: Optional[str] = Field(None, description="História de fundo")
    appearance: Optional[str] = Field(None, description="Características físicas")
    relationships: Optional[str] = Field(None, description="Relacionamentos (JSON)")
    organization_type: Optional[str] = Field(None, description="Tipo de organização")
    organization_purpose: Optional[str] = Field(None, description="Propósito da organização")
    organization_members: Optional[str] = Field(None, description="Membros da organização (JSON)")
    traits: Optional[str] = Field(None, description="Etiquetas de traços (JSON)")


class CharacterCreate(BaseModel):
    """手动创建角色的请求模型"""
    project_id: str = Field(..., description="ID do projeto")
    name: str = Field(..., description="Nome do personagem/organização")
    age: Optional[str] = Field(None, description="Idade")
    gender: Optional[str] = Field(None, description="Gênero")
    is_organization: bool = Field(False, description="É uma organização")
    role_type: Optional[str] = Field("supporting", description="Tipo de personagem: protagonist/supporting/antagonist")
    personality: Optional[str] = Field(None, description="Personalidade / características da organização")
    background: Optional[str] = Field(None, description="História de fundo")
    appearance: Optional[str] = Field(None, description="Características físicas")
    organization_type: Optional[str] = Field(None, description="Tipo de organização")
    organization_purpose: Optional[str] = Field(None, description="Propósito da organização")
    organization_members: Optional[str] = Field(None, description="Membros da organização (JSON)")
    traits: Optional[str] = Field(None, description="Etiquetas de traços (JSON)")
    avatar_url: Optional[str] = Field(None, description="URL do avatar")
    
    # 组织额外字段
    power_level: Optional[int] = Field(None, description="Nível de poder da organização (0-100)")
    location: Optional[str] = Field(None, description="Localização da organização")
    motto: Optional[str] = Field(None, description="Lema da organização")
    color: Optional[str] = Field(None, description="Cor da organização")
    
    # 职业字段
    main_career_id: Optional[str] = Field(None, description="ID da carreira principal")
    main_career_stage: Optional[int] = Field(None, description="Estágio da carreira principal")
    sub_careers: Optional[str] = Field(None, description="Lista de carreiras secundárias (string JSON)")


class CharacterUpdate(BaseModel):
    """更新角色的请求模型"""
    name: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    is_organization: Optional[bool] = None
    role_type: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    appearance: Optional[str] = None
    organization_type: Optional[str] = None
    organization_purpose: Optional[str] = None
    organization_members: Optional[str] = None
    traits: Optional[str] = None
    
    # 组织额外字段（会同步到Organization表）
    power_level: Optional[int] = Field(None, description="Nível de poder da organização (0-100)")
    location: Optional[str] = Field(None, description="Localização da organização")
    motto: Optional[str] = Field(None, description="Lema da organização")
    color: Optional[str] = Field(None, description="Cor da organização")
    
    # 职业字段（会同步到CharacterCareer表）
    main_career_id: Optional[str] = Field(None, description="ID da carreira principal")
    main_career_stage: Optional[int] = Field(None, description="Estágio da carreira principal")
    sub_careers: Optional[str] = Field(None, description="Lista de carreiras secundárias (string JSON)")


class CharacterResponse(CharacterBase):
    """角色响应模型"""
    id: str
    project_id: str
    avatar_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # 组织额外字段（从Organization表关联）
    power_level: Optional[int] = Field(None, description="Nível de poder da organização (0-100)")
    location: Optional[str] = Field(None, description="Localização da organização")
    motto: Optional[str] = Field(None, description="Lema da organização")
    color: Optional[str] = Field(None, description="Cor da organização")
    
    # 职业信息字段
    main_career_id: Optional[str] = Field(None, description="ID da carreira principal")
    main_career_stage: Optional[int] = Field(None, description="Estágio da carreira principal")
    sub_careers: Optional[List[Dict[str, Any]]] = Field(None, description="Lista de carreiras secundárias")
    
    # 角色/组织存活状态
    status: Optional[str] = Field("active", description="Status: active/deceased/missing/retired/destroyed")
    status_changed_chapter: Optional[int] = Field(None, description="Capítulo da mudança de status")
    
    # 心理状态追踪字段
    current_state: Optional[str] = Field(None, description="Estado psicológico atual do personagem")
    state_updated_chapter: Optional[int] = Field(None, description="Capítulo da última atualização do estado psicológico")
    
    model_config = ConfigDict(from_attributes=True)


class CharacterGenerateRequest(BaseModel):
    """AI生成角色的请求模型"""
    project_id: str = Field(..., description="ID do projeto")
    name: Optional[str] = Field(None, description="Nome do personagem")
    role_type: Optional[str] = Field(None, description="Tipo de personagem")
    background: Optional[str] = Field(None, description="Histórico do personagem")
    requirements: Optional[str] = Field(None, description="Requisitos especiais")
    enable_mcp: bool = Field(True, description="Habilitar reforço com ferramentas MCP (busca de referências de arquétipos)")


class CharacterListResponse(BaseModel):
    """角色列表响应模型"""
    total: int
    items: List[CharacterResponse]