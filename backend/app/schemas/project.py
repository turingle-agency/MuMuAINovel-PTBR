"""项目相关的Pydantic模型"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.constants.languages import SUPPORTED_LANGUAGES
from typing import Optional, Literal
from datetime import datetime


def _checar_idioma(v):
    if v is not None and v not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Idioma não suportado: {v}")
    return v


class ProjectBase(BaseModel):
    """项目基础模型"""
    title: str = Field(..., description="Título do projeto")
    description: Optional[str] = Field(None, description="Descrição do projeto")
    theme: Optional[str] = Field(None, description="Tema")
    genre: Optional[str] = Field(None, description="Gênero do livro")
    target_words: Optional[int] = Field(None, description="Meta de palavras")
    outline_mode: Literal["one-to-one", "one-to-many"] = Field(
        default="one-to-many",
        description="Modo de capítulos do esboço: one-to-one (tradicional, 1 esboço→1 capítulo) ou one-to-many (detalhado, 1 esboço→N capítulos)"
    )
    language: str = Field(default="pt-BR", description="Idioma do projeto")
    project_type: Literal["fiction", "lowticket"] = Field(default="fiction", description="Tipo de projeto")
    series_id: Optional[str] = Field(None, description="ID da série")
    volume_number: Optional[int] = Field(None, description="Número do volume na série")

    @field_validator("language")
    @classmethod
    def _validar_idioma(cls, v: str) -> str:
        return _checar_idioma(v)


class ProjectCreate(ProjectBase):
    """创建项目的请求模型"""
    pass


class ProjectUpdate(BaseModel):
    """更新项目的请求模型"""
    title: Optional[str] = None
    description: Optional[str] = None
    theme: Optional[str] = None
    genre: Optional[str] = None
    target_words: Optional[int] = None
    status: Optional[str] = None
    # wizard_status 和 wizard_step 只能通过向导API修改，普通更新不允许
    world_time_period: Optional[str] = None
    world_location: Optional[str] = None
    world_atmosphere: Optional[str] = None
    world_rules: Optional[str] = None
    chapter_count: Optional[int] = None
    narrative_perspective: Optional[str] = None
    character_count: Optional[int] = None
    language: Optional[str] = None
    project_type: Optional[Literal["fiction", "lowticket"]] = None
    series_id: Optional[str] = None
    volume_number: Optional[int] = None

    @field_validator("language")
    @classmethod
    def _validar_idioma(cls, v):
        return _checar_idioma(v)
    # current_words 由章节内容自动计算，不允许手动修改


class ProjectResponse(ProjectBase):
    """项目响应模型"""
    id: str  # UUID字符串
    status: str
    current_words: int
    wizard_status: Optional[str] = None
    wizard_step: Optional[int] = None
    world_time_period: Optional[str] = None
    world_location: Optional[str] = None
    world_atmosphere: Optional[str] = None
    world_rules: Optional[str] = None
    chapter_count: Optional[int] = None
    narrative_perspective: Optional[str] = None
    character_count: Optional[int] = None
    cover_image_url: Optional[str] = None
    cover_prompt: Optional[str] = None
    cover_status: Optional[str] = None
    cover_error: Optional[str] = None
    cover_updated_at: Optional[datetime] = None
    outline_mode: str  # 显式声明以确保响应中包含
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    """项目列表响应模型"""
    total: int
    items: list[ProjectResponse]


class ProjectWizardRequest(BaseModel):
    """项目创建向导请求模型"""
    title: str = Field(..., description="Título do livro")
    theme: str = Field(..., description="Tema")
    genre: Optional[str] = Field(None, description="Gênero")
    chapter_count: int = Field(..., ge=1, description="Quantidade de capítulos")
    narrative_perspective: str = Field(..., description="Perspectiva narrativa")
    character_count: int = Field(5, ge=5, description="Quantidade de personagens (mínimo 5)")
    target_words: Optional[int] = Field(None, description="Meta de palavras")
    outline_mode: Literal["one-to-one", "one-to-many"] = Field(
        default="one-to-many",
        description="Modo de capítulos do esboço"
    )


class WorldBuildingResponse(BaseModel):
    """世界构建响应模型"""
    time_period: str = Field(..., description="Contexto temporal")
    location: str = Field(..., description="Localização geográfica")
    atmosphere: str = Field(..., description="Atmosfera e tom")
    rules: str = Field(..., description="Regras do mundo")