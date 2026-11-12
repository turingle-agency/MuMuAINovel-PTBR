"""设置数据模型"""
from sqlalchemy import Column, String, Text, Float, Integer, DateTime, Boolean, Index
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Settings(Base):
    """设置表"""
    __tablename__ = "settings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(50), nullable=False, unique=True, index=True, comment="ID do usuário")
    api_provider = Column(String(50), default="openai", comment="Provedor da API")
    api_key = Column(String(500), comment="Chave da API")
    api_base_url = Column(String(500), comment="URL personalizada da API")
    llm_model = Column(String(100), nullable=True, comment="Nome do modelo (vazio = padrão do provedor)")
    temperature = Column(Float, default=0.7, comment="Parâmetro de temperatura")
    max_tokens = Column(Integer, default=2000, comment="Máximo de tokens")
    system_prompt = Column(Text, comment="Prompt de nível de sistema, usado em toda chamada de IA")
    disable_thinking = Column(Boolean, default=False, server_default="0", nullable=False, comment="Desativar o raciocínio do modelo (ao ativar, modelos de raciocínio pulam a etapa de raciocínio e geram o texto direto)")

    # API de reserva usada quando o Codex falha (cota, login, timeout)
    fallback_api_provider = Column(String(50), nullable=True, comment="Provider da API de reserva")
    fallback_api_key = Column(String(500), nullable=True, comment="Chave da API de reserva")
    fallback_api_base_url = Column(String(500), nullable=True, comment="URL da API de reserva")
    fallback_llm_model = Column(String(100), nullable=True, comment="Modelo da API de reserva")

    # 封面图片生成配置
    cover_api_provider = Column(String(50), comment="Provedor da API de imagem de capa")
    cover_api_key = Column(String(500), comment="Chave da API de imagem de capa")
    cover_api_base_url = Column(String(500), comment="URL personalizada da API de imagem de capa")
    cover_image_model = Column(String(100), comment="Nome do modelo de imagem de capa")
    cover_enabled = Column(Boolean, default=False, server_default="0", nullable=False, comment="Geração de capa habilitada")

    # 系统级 SMTP 配置（仅管理员维护）
    smtp_provider = Column(String(50), default="custom", server_default="qq", nullable=False, comment="Provedor SMTP")
    smtp_host = Column(String(255), comment="Host SMTP")
    smtp_port = Column(Integer, default=465, server_default="465", nullable=False, comment="Porta SMTP")
    smtp_username = Column(String(255), comment="Usuário SMTP")
    smtp_password = Column(String(500), comment="Senha SMTP ou código de autorização")
    smtp_use_tls = Column(Boolean, default=False, server_default="0", nullable=False, comment="TLS habilitado")
    smtp_use_ssl = Column(Boolean, default=True, server_default="1", nullable=False, comment="SSL habilitado")
    smtp_from_email = Column(String(255), comment="E-mail do remetente")
    smtp_from_name = Column(String(255), default="MuMuAINovel", server_default="MuMuAINovel", nullable=False, comment="Nome do remetente")
    email_auth_enabled = Column(Boolean, default=True, server_default="1", nullable=False, comment="Autenticação por e-mail habilitada")
    email_register_enabled = Column(Boolean, default=True, server_default="1", nullable=False, comment="Cadastro por e-mail habilitado")
    verification_code_ttl_minutes = Column(Integer, default=10, server_default="10", nullable=False, comment="Validade do código de verificação (minutos)")
    verification_resend_interval_seconds = Column(Integer, default=60, server_default="60", nullable=False, comment="Intervalo para reenvio do código (segundos)")

    preferences = Column(Text, comment="Outras preferências (JSON)")
    created_at = Column(DateTime, server_default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Data de atualização")
    
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
    )
    
    def __repr__(self):
        return f"<Settings(id={self.id}, user_id={self.user_id}, api_provider={self.api_provider})>"
