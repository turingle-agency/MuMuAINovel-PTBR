"""MCP插件配置数据模型"""
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, Index, JSON
from sqlalchemy.sql import func
from app.database import Base
import uuid


class MCPPlugin(Base):
    """MCP插件配置表"""
    __tablename__ = "mcp_plugins"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(50), nullable=False, index=True, comment="ID do usuário")
    
    # 插件基本信息
    plugin_name = Column(String(100), nullable=False, comment="Nome do plugin (identificador único)")
    display_name = Column(String(200), nullable=False, comment="Nome de exibição")
    description = Column(Text, comment="Descrição do plugin")
    plugin_type = Column(String(50), default="http", comment="Tipo de plugin: http/stdio")
    
    # 连接配置
    server_url = Column(String(500), comment="URL do servidor (tipo HTTP)")
    command = Column(String(500), comment="Comando de inicialização (tipo stdio)")
    args = Column(JSON, comment="Argumentos do comando (tipo stdio)")
    env = Column(JSON, comment="Variáveis de ambiente")
    headers = Column(JSON, comment="Cabeçalhos HTTP")
    
    # 插件配置
    config = Column(JSON, comment="Configuração específica do plugin (JSON)")
    tools = Column(JSON, comment="Lista de ferramentas fornecidas")
    
    # 状态管理
    enabled = Column(Boolean, default=True, comment="Habilitado")
    status = Column(String(50), default="inactive", comment="Status: active/inactive/error")
    last_error = Column(Text, comment="Última mensagem de erro")
    last_test_at = Column(DateTime, comment="Data do último teste")
    
    # 排序和分组
    category = Column(String(100), default="general", comment="Categoria")
    sort_order = Column(Integer, default=0, comment="Ordem de exibição")
    
    # 时间戳
    created_at = Column(DateTime, server_default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Data de atualização")
    
    __table_args__ = (
        Index('idx_user_plugin', 'user_id', 'plugin_name', unique=True),
        Index('idx_user_enabled', 'user_id', 'enabled'),
    )
    
    def __repr__(self):
        return f"<MCPPlugin(id={self.id}, name={self.plugin_name}, enabled={self.enabled})>"