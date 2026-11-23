"""提示词模板数据模型"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base
import uuid


class PromptTemplate(Base):
    """提示词模板表"""
    __tablename__ = "prompt_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(50), nullable=False, index=True, comment="ID do usuário")
    template_key = Column(String(100), nullable=False, comment="Chave do template")
    template_name = Column(String(200), nullable=False, comment="Nome de exibição do template")
    template_content = Column(Text, nullable=False, comment="Conteúdo do template")
    description = Column(Text, comment="Descrição do template")
    category = Column(String(50), comment="Categoria do template")
    parameters = Column(Text, comment="Definição de parâmetros do template (JSON)")
    is_active = Column(Boolean, default=True, comment="Habilitado")
    is_system_default = Column(Boolean, default=False, comment="Template padrão do sistema")
    created_at = Column(DateTime, server_default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Data de atualização")
    
    __table_args__ = (
        Index('idx_user_template', 'user_id', 'template_key', unique=True),
    )
    
    def __repr__(self):
        return f"<PromptTemplate(id={self.id}, user_id={self.user_id}, template_key={self.template_key})>"