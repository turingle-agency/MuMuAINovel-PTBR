"""职业相关的Pydantic模型"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class CareerStage(BaseModel):
    """职业阶段模型"""
    level: int = Field(..., description="Nível do estágio")
    name: str = Field(..., description="Nome do estágio")
    description: Optional[str] = Field(None, description="Descrição do estágio")


class CareerBase(BaseModel):
    """职业基础模型"""
    name: str = Field(..., description="Nome da carreira")
    type: str = Field(..., description="Tipo de carreira: main (principal)/sub (secundária)")
    description: Optional[str] = Field(None, description="Descrição da carreira")
    category: Optional[str] = Field(None, description="Categoria da carreira")
    stages: List[CareerStage] = Field(..., description="Lista de estágios da carreira")
    max_stage: int = Field(10, description="Número máximo de estágios")
    requirements: Optional[str] = Field(None, description="Requisitos/restrições da carreira")
    special_abilities: Optional[str] = Field(None, description="Descrição das habilidades especiais")
    worldview_rules: Optional[str] = Field(None, description="Vínculo com as regras do mundo")
    attribute_bonuses: Optional[Dict[str, str]] = Field(None, description="Bônus de atributos")


class CareerCreate(CareerBase):
    """创建职业的请求模型"""
    project_id: str = Field(..., description="ID do projeto")
    source: str = Field("manual", description="Origem: ai/manual")


class CareerUpdate(BaseModel):
    """更新职业的请求模型"""
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    stages: Optional[List[CareerStage]] = None
    max_stage: Optional[int] = None
    requirements: Optional[str] = None
    special_abilities: Optional[str] = None
    worldview_rules: Optional[str] = None
    attribute_bonuses: Optional[Dict[str, str]] = None


class CareerResponse(BaseModel):
    """职业响应模型"""
    id: str
    project_id: str
    name: str
    type: str
    description: Optional[str] = None
    category: Optional[str] = None
    stages: List[CareerStage]
    max_stage: int
    requirements: Optional[str] = None
    special_abilities: Optional[str] = None
    worldview_rules: Optional[str] = None
    attribute_bonuses: Optional[Dict[str, str]] = None
    source: str
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CareerListResponse(BaseModel):
    """职业列表响应模型"""
    total: int
    main_careers: List[CareerResponse] = Field(default_factory=list, description="Lista de carreiras principais")
    sub_careers: List[CareerResponse] = Field(default_factory=list, description="Lista de carreiras secundárias")


class CareerGenerateRequest(BaseModel):
    """AI生成职业体系的请求模型"""
    project_id: str = Field(..., description="ID do projeto")
    main_career_count: int = Field(5, description="Quantidade de carreiras principais", ge=1, le=20)
    sub_career_count: int = Field(8, description="Quantidade de carreiras secundárias", ge=0, le=30)
    user_requirements: str = Field("", description="Requisitos adicionais do usuário")
    enable_mcp: bool = Field(False, description="Habilitar reforço com ferramentas MCP")


# ===== 角色职业关联相关 =====

class CharacterCareerBase(BaseModel):
    """角色职业关联基础模型"""
    career_id: str = Field(..., description="ID da carreira")
    career_type: str = Field(..., description="main (principal)/sub (secundária)")
    current_stage: int = Field(1, description="Estágio atual", ge=1)
    stage_progress: int = Field(0, description="Progresso dentro do estágio (0-100)", ge=0, le=100)
    started_at: Optional[str] = Field(None, description="Início do treinamento")
    reached_current_stage_at: Optional[str] = Field(None, description="Momento em que alcançou o estágio atual")
    notes: Optional[str] = Field(None, description="Observações")


class CharacterCareerCreate(CharacterCareerBase):
    """创建角色职业关联的请求模型"""
    character_id: str = Field(..., description="ID do personagem")


class CharacterCareerUpdate(BaseModel):
    """更新角色职业关联的请求模型"""
    current_stage: Optional[int] = Field(None, ge=1)
    stage_progress: Optional[int] = Field(None, ge=0, le=100)
    reached_current_stage_at: Optional[str] = None
    notes: Optional[str] = None


class CharacterCareerDetail(BaseModel):
    """角色职业详情模型（包含职业信息）"""
    id: str
    character_id: str
    career_id: str
    career_name: str = Field(..., description="Nome da carreira")
    career_type: str
    current_stage: int
    stage_name: str = Field(..., description="Nome do estágio atual")
    stage_description: Optional[str] = Field(None, description="Descrição do estágio atual")
    stage_progress: int
    max_stage: int = Field(..., description="Estágio máximo da carreira")
    started_at: Optional[str] = None
    reached_current_stage_at: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CharacterCareerResponse(BaseModel):
    """角色职业响应模型"""
    main_career: Optional[CharacterCareerDetail] = Field(None, description="Carreira principal")
    sub_careers: List[CharacterCareerDetail] = Field(default_factory=list, description="Lista de carreiras secundárias")


class SetMainCareerRequest(BaseModel):
    """设置主职业请求模型"""
    career_id: str = Field(..., description="ID da carreira")
    current_stage: int = Field(1, description="Estágio atual", ge=1)
    started_at: Optional[str] = Field(None, description="Início do treinamento")


class AddSubCareerRequest(BaseModel):
    """添加副职业请求模型"""
    career_id: str = Field(..., description="ID da carreira")
    current_stage: int = Field(1, description="Estágio atual", ge=1)
    started_at: Optional[str] = Field(None, description="Início do treinamento")


class UpdateCareerStageRequest(BaseModel):
    """更新职业阶段请求模型"""
    current_stage: int = Field(..., description="Novo estágio", ge=1)
    stage_progress: int = Field(0, description="Progresso do estágio", ge=0, le=100)
    reached_current_stage_at: Optional[str] = Field(None, description="Momento de chegada")
    notes: Optional[str] = Field(None, description="Observações")