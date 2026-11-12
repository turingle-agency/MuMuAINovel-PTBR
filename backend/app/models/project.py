"""项目数据模型"""
from sqlalchemy import Column, String, Text, DateTime, Integer, CheckConstraint, ForeignKey
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Project(Base):
    """项目表"""
    __tablename__ = "projects"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(100), nullable=False, index=True, comment="ID do usuário")
    title = Column(String(200), nullable=False, comment="Título do projeto")
    description = Column(Text, comment="Descrição do projeto")
    theme = Column(Text, comment="Tema")
    genre = Column(String(50), comment="Gênero do livro")
    target_words = Column(Integer, default=0, comment="Meta de palavras")
    current_words = Column(Integer, default=0, comment="Contagem atual de palavras")
    status = Column(String(20), default="planning", comment="Status de criação")
    wizard_status = Column(String(20), default="incomplete", comment="Status do assistente: incomplete/completed")
    wizard_step = Column(Integer, default=0, comment="Etapa atual do assistente: 0-4")
    outline_mode = Column(String(20), nullable=False, default="one-to-many", comment="Modo de capítulos do esboço: one-to-one (tradicional) ou one-to-many (detalhado)")
    
    # 世界构建字段
    world_time_period = Column(Text, comment="Contexto temporal")
    world_location = Column(Text, comment="Localização geográfica")
    world_atmosphere = Column(Text, comment="Atmosfera e tom")
    world_rules = Column(Text, comment="Regras do mundo")
    
    # 项目配置
    chapter_count = Column(Integer, comment="Quantidade de capítulos")
    narrative_perspective = Column(String(50), comment="Perspectiva narrativa: first_person/third_person/omniscient")
    character_count = Column(Integer, default=5, comment="Quantidade de personagens")

    # Fábrica de ebooks
    language = Column(String(10), nullable=False, default="pt-BR", server_default="pt-BR", comment="Idioma do projeto")
    project_type = Column(String(20), nullable=False, default="fiction", server_default="fiction", comment="fiction/lowticket")
    series_id = Column(String(36), ForeignKey("series.id", ondelete="SET NULL"), nullable=True, index=True, comment="Série")
    volume_number = Column(Integer, nullable=True, comment="Número do volume na série")

    # 封面字段
    cover_image_url = Column(String(1000), comment="URL de acesso à imagem de capa")
    cover_prompt = Column(Text, comment="Prompt usado na última geração de capa")
    cover_status = Column(String(20), default="none", nullable=False, comment="Status da capa: none/generating/ready/failed")
    cover_error = Column(Text, comment="Motivo da última falha na geração de capa")
    cover_updated_at = Column(DateTime, comment="Data da última geração de capa bem-sucedida")
    
    created_at = Column(DateTime, server_default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Data de atualização")
    
    __table_args__ = (
        CheckConstraint(
            "outline_mode IN ('one-to-one', 'one-to-many')",
            name='check_outline_mode'
        ),
        CheckConstraint(
            "cover_status IN ('none', 'generating', 'ready', 'failed')",
            name='check_cover_status'
        ),
        CheckConstraint(
            "project_type IN ('fiction', 'lowticket')",
            name='check_project_type'
        ),
    )
    
    def __repr__(self):
        return f"<Project(id={self.id}, title={self.title})>"
