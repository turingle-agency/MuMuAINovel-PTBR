"""提示词模板相关的Pydantic模型"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class PromptTemplateBase(BaseModel):
    """提示词模板基础模型"""
    template_key: str = Field(..., description="Chave do template")
    template_name: str = Field(..., description="Nome de exibição do template")
    template_content: str = Field(..., description="Conteúdo do template")
    description: Optional[str] = Field(None, description="Descrição do template")
    category: Optional[str] = Field(None, description="Categoria do template")
    parameters: Optional[str] = Field(None, description="Definição de parâmetros do template (JSON)")
    is_active: bool = Field(True, description="Habilitado")


class PromptTemplateCreate(PromptTemplateBase):
    """创建提示词模板请求模型"""
    pass


class PromptTemplateUpdate(BaseModel):
    """更新提示词模板请求模型"""
    template_name: Optional[str] = Field(None, description="Nome de exibição do template")
    template_content: Optional[str] = Field(None, description="Conteúdo do template")
    description: Optional[str] = Field(None, description="Descrição do template")
    category: Optional[str] = Field(None, description="Categoria do template")
    parameters: Optional[str] = Field(None, description="Definição de parâmetros do template (JSON)")
    is_active: Optional[bool] = Field(None, description="Habilitado")


class PromptTemplateResponse(PromptTemplateBase):
    """提示词模板响应模型"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    is_system_default: bool
    created_at: datetime
    updated_at: datetime


class PromptTemplateListResponse(BaseModel):
    """提示词模板列表响应"""
    templates: List[PromptTemplateResponse]
    total: int
    categories: List[str]


class PromptTemplateCategoryResponse(BaseModel):
    """提示词模板分类响应"""
    category: str
    count: int
    templates: List[PromptTemplateResponse]


class PromptTemplateExportItem(BaseModel):
    """提示词模板导出项模型"""
    template_key: str = Field(..., description="Chave do template")
    template_name: str = Field(..., description="Nome de exibição do template")
    template_content: str = Field(..., description="Conteúdo do template")
    description: Optional[str] = Field(None, description="Descrição do template")
    category: Optional[str] = Field(None, description="Categoria do template")
    parameters: Optional[str] = Field(None, description="Definição de parâmetros do template (JSON)")
    is_active: bool = Field(True, description="Habilitado")
    is_customized: bool = Field(..., description="Personalizado pelo usuário (false=padrão do sistema, true=personalizado)")
    system_content_hash: Optional[str] = Field(None, description="Hash do conteúdo padrão do sistema, usado para comparação")


class PromptTemplateExport(BaseModel):
    """提示词模板导出模型"""
    templates: List[PromptTemplateExportItem]
    export_time: datetime
    version: str = "2.0"
    statistics: Optional[dict] = Field(None, description="Estatísticas de exportação")


class PromptTemplateImportResult(BaseModel):
    """提示词模板导入结果"""
    message: str
    statistics: dict = Field(..., description="Estatísticas de importação")
    converted_templates: List[dict] = Field(default_factory=list, description="Lista de templates convertidos em personalizados")


class PromptTemplatePreviewRequest(BaseModel):
    """提示词模板预览请求"""
    template_content: str = Field(..., description="Conteúdo do template")
    parameters: dict = Field(..., description="Dicionário de parâmetros")
