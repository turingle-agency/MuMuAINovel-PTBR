"""
用户数据模型 - 存储用户基本信息
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """用户模型 - 存储OAuth和本地用户信息"""
    __tablename__ = "users"
    
    user_id = Column(String(100), primary_key=True, index=True, comment="ID do usuário, formato: local_{id} etc.")
    username = Column(String(100), nullable=False, index=True, comment="Nome de usuário")
    display_name = Column(String(200), nullable=False, comment="Nome de exibição")
    avatar_url = Column(String(500), nullable=True, comment="URL do avatar")
    trust_level = Column(Integer, default=0, comment="Nível de confiança (apenas exibição)")
    is_admin = Column(Boolean, default=False, comment="É administrador")
    linuxdo_id = Column(String(100), nullable=False, unique=True, index=True, comment="ID único do usuário (nome da coluna é legado)")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Data de criação")
    last_login = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="Data do último login")
    
    def to_dict(self):
        """转换为字典"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "trust_level": self.trust_level,
            "is_admin": self.is_admin,
            "linuxdo_id": self.linuxdo_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }


class UserPassword(Base):
    """用户密码模型 - 存储用户密码信息"""
    __tablename__ = "user_passwords"
    
    user_id = Column(String(100), primary_key=True, index=True, comment="ID do usuário")
    username = Column(String(100), nullable=False, comment="Nome de usuário")
    password_hash = Column(String(255), nullable=False, comment="Hash da senha")
    has_custom_password = Column(Boolean, default=False, comment="Senha personalizada")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="Data de atualização")
