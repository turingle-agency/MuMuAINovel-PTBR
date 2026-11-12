"""设置相关的Pydantic模型"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime


class SettingsBase(BaseModel):
    """设置基础模型"""
    model_config = ConfigDict(protected_namespaces=())
    
    api_provider: Optional[str] = Field(default="openai", description="Provedor da API")
    api_key: Optional[str] = Field(default=None, description="Chave da API")
    api_base_url: Optional[str] = Field(default=None, description="URL personalizada da API")
    llm_model: Optional[str] = Field(default=None, description="Nome do modelo")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="Parâmetro de temperatura")
    max_tokens: Optional[int] = Field(default=2000, ge=1, description="Máximo de tokens")
    system_prompt: Optional[str] = Field(default=None, description="Prompt de nível de sistema, usado em toda chamada de IA")
    disable_thinking: Optional[bool] = Field(default=False, description="Desativar o raciocínio do modelo: modelos de raciocínio pulam a etapa de raciocínio e geram o texto direto, reduzindo tokens e tempo de espera")
    fallback_api_provider: Optional[str] = Field(default=None, description="Provider da API de reserva (usada se o Codex falhar)")
    fallback_api_key: Optional[str] = Field(default=None, description="Chave da API de reserva")
    fallback_api_base_url: Optional[str] = Field(default=None, description="URL da API de reserva")
    fallback_llm_model: Optional[str] = Field(default=None, description="Modelo da API de reserva")
    cover_api_provider: Optional[str] = Field(default=None, description="Provedor da API de imagem de capa")
    cover_api_key: Optional[str] = Field(default=None, description="Chave da API de imagem de capa")
    cover_api_base_url: Optional[str] = Field(default=None, description="URL personalizada da API de imagem de capa")
    cover_image_model: Optional[str] = Field(default=None, description="Nome do modelo de imagem de capa")
    cover_enabled: Optional[bool] = Field(default=False, description="Geração de capa habilitada")
    preferences: Optional[str] = Field(default=None, description="Outras preferências (JSON)")


class SettingsCreate(SettingsBase):
    """创建设置请求模型"""
    pass


class SettingsUpdate(SettingsBase):
    """更新设置请求模型"""
    pass


class SettingsResponse(SettingsBase):
    """设置响应模型"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class SystemSMTPSettingsBase(BaseModel):
    """系统 SMTP 设置基础模型"""
    model_config = ConfigDict(protected_namespaces=())

    smtp_provider: str = Field(default="custom", description="Provedor SMTP")
    smtp_host: Optional[str] = Field(default=None, description="Host SMTP")
    smtp_port: int = Field(default=465, ge=1, le=65535, description="Porta SMTP")
    smtp_username: Optional[str] = Field(default=None, description="Usuário SMTP")
    smtp_password: Optional[str] = Field(default=None, description="Senha SMTP ou código de autorização")
    smtp_use_tls: bool = Field(default=False, description="TLS habilitado")
    smtp_use_ssl: bool = Field(default=True, description="SSL habilitado")
    smtp_from_email: Optional[str] = Field(default=None, description="E-mail do remetente")
    smtp_from_name: str = Field(default="MuMuAINovel", description="Nome do remetente")
    email_auth_enabled: bool = Field(default=True, description="Autenticação por e-mail habilitada")
    email_register_enabled: bool = Field(default=True, description="Cadastro por e-mail habilitado")
    verification_code_ttl_minutes: int = Field(default=10, ge=1, le=120, description="Validade do código de verificação (minutos)")
    verification_resend_interval_seconds: int = Field(default=60, ge=10, le=3600, description="Intervalo para reenvio do código (segundos)")


class SystemSMTPSettingsUpdate(SystemSMTPSettingsBase):
    """系统 SMTP 设置更新模型"""
    pass


class SystemSMTPSettingsResponse(SystemSMTPSettingsBase):
    """系统 SMTP 设置响应模型"""
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class SMTPTestRequest(BaseModel):
    """SMTP 测试请求模型"""
    model_config = ConfigDict(protected_namespaces=())

    to_email: str = Field(..., min_length=3, max_length=255, description="E-mail de destino do teste")


# ========== API配置预设相关模型 ==========

class APIKeyPresetConfig(BaseModel):
    """预设配置内容"""
    model_config = ConfigDict(protected_namespaces=())
    
    api_provider: str = Field(..., description="Provedor da API")
    api_key: Optional[str] = Field(default="", description="Chave da API (vazia para o provider codex)")
    api_base_url: Optional[str] = Field(None, description="URL personalizada da API")
    llm_model: Optional[str] = Field(default="", description="Nome do modelo (vazio = padrão do provider)")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Parâmetro de temperatura")
    max_tokens: int = Field(default=2000, ge=1, description="Máximo de tokens")
    system_prompt: Optional[str] = Field(default=None, description="Prompt de nível de sistema")


class APIKeyPreset(BaseModel):
    """API配置预设"""
    model_config = ConfigDict(protected_namespaces=())
    
    id: str = Field(..., description="ID do preset")
    name: str = Field(..., min_length=1, max_length=50, description="Nome do preset")
    description: Optional[str] = Field(None, max_length=200, description="Descrição do preset")
    is_active: bool = Field(default=False, description="Ativo")
    created_at: datetime = Field(..., description="Data de criação")
    config: APIKeyPresetConfig = Field(..., description="Conteúdo da configuração")


class PresetCreateRequest(BaseModel):
    """创建预设请求"""
    model_config = ConfigDict(protected_namespaces=())
    
    name: str = Field(..., min_length=1, max_length=50, description="Nome do preset")
    description: Optional[str] = Field(None, max_length=200, description="Descrição do preset")
    config: APIKeyPresetConfig = Field(..., description="Conteúdo da configuração")


class PresetUpdateRequest(BaseModel):
    """更新预设请求"""
    model_config = ConfigDict(protected_namespaces=())
    
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="Nome do preset")
    description: Optional[str] = Field(None, max_length=200, description="Descrição do preset")
    config: Optional[APIKeyPresetConfig] = Field(None, description="Conteúdo da configuração")


class PresetResponse(APIKeyPreset):
    """预设响应"""
    pass


class PresetListResponse(BaseModel):
    """预设列表响应"""
    model_config = ConfigDict(protected_namespaces=())
    
    presets: List[PresetResponse] = Field(..., description="Lista de presets")
    total: int = Field(..., description="Total")
    active_preset_id: Optional[str] = Field(None, description="ID do preset ativo")
    chapter_analysis_preset_id: Optional[str] = Field(None, description="ID do preset usado na análise de capítulos; se vazio, usa a configuração padrão de API")


class ChapterAnalysisPresetSelectionRequest(BaseModel):
    """章节内容分析预设选择请求"""
    model_config = ConfigDict(protected_namespaces=())

    preset_id: Optional[str] = Field(None, description="ID do preset usado na análise de capítulos; se vazio, usa a configuração padrão de API")