"""写作风格数据模型"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.sql import func
from app.database import Base


class WritingStyle(Base):
    """写作风格表"""
    __tablename__ = "writing_styles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=True, comment="ID do usuário proprietário (NULL = estilo predefinido global)")
    name = Column(String(100), nullable=False, comment="Nome do estilo")
    style_type = Column(String(50), nullable=False, comment="Tipo de estilo: preset/custom")
    preset_id = Column(String(50), comment="ID do estilo predefinido: natural/classical/modern etc.")
    description = Column(Text, comment="Descrição do estilo")
    prompt_content = Column(Text, nullable=False, comment="Conteúdo do prompt do estilo")
    order_index = Column(Integer, default=0, comment="Número de ordem")
    created_at = Column(DateTime, server_default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Data de atualização")
    
    def __repr__(self):
        return f"<WritingStyle(id={self.id}, name={self.name}, user_id={self.user_id})>"