"""伏笔管理数据模型 - 独立管理小说伏笔的埋入和回收"""
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Float, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid


class Foreshadow(Base):
    """
    伏笔管理表 - 独立管理小说伏笔
    
    支持以下功能：
    1. 从章节分析结果自动同步伏笔
    2. 用户手动添加自定义伏笔
    3. 关联埋入章节和计划回收章节
    4. 长线伏笔管理
    5. 章节生成时的伏笔提醒
    """
    __tablename__ = "foreshadows"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # === 伏笔内容 ===
    title = Column(String(200), nullable=False, comment="Título do foreshadowing")
    content = Column(Text, nullable=False, comment="Conteúdo/descrição detalhada do foreshadowing")
    hint_text = Column(Text, comment="Texto de sugestão ao plantar (trecho original ou resumo)")
    resolution_text = Column(Text, comment="Texto de revelação ao resolver (trecho original ou resumo)")
    
    # === 来源信息 ===
    source_type = Column(String(20), default='manual', comment="Tipo de origem: analysis=extraído da análise, manual=adicionado manualmente")
    source_memory_id = Column(String(100), comment="ID da memória de origem (se sincronizado da análise)")
    source_analysis_id = Column(String(36), comment="ID da tarefa de análise de origem")
    
    # === 章节关联 ===
    # 埋入章节
    plant_chapter_id = Column(String(36), ForeignKey("chapters.id", ondelete="SET NULL"), comment="ID do capítulo de plantio")
    plant_chapter_number = Column(Integer, comment="Número do capítulo de plantio (armazenado de forma redundante para consultas)")
    
    # 计划回收章节
    target_resolve_chapter_id = Column(String(36), ForeignKey("chapters.id", ondelete="SET NULL"), comment="ID do capítulo de resolução planejada")
    target_resolve_chapter_number = Column(Integer, comment="Número do capítulo de resolução planejada")
    
    # 实际回收章节
    actual_resolve_chapter_id = Column(String(36), ForeignKey("chapters.id", ondelete="SET NULL"), comment="ID do capítulo de resolução real")
    actual_resolve_chapter_number = Column(Integer, comment="Número do capítulo de resolução real")
    
    # === 状态管理 ===
    status = Column(String(20), default='pending', index=True, comment="""
    Status do foreshadowing:
    - pending: a plantar (planejado, ainda não escrito em capítulo)
    - planted: plantado (já inserido em um capítulo)
    - resolved: resolvido (já pago em um capítulo)
    - partially_resolved: parcialmente resolvido (os de longo prazo podem ser resolvidos em várias etapas)
    - abandoned: abandonado (decidiu-se não usar mais)
    """)
    
    is_long_term = Column(Boolean, default=False, comment="Foreshadowing de longo prazo (importante, abrange vários capítulos)")
    
    # === 重要性和优先级 ===
    importance = Column(Float, default=0.5, comment="Pontuação de importância 0.0-1.0")
    strength = Column(Integer, default=5, comment="Intensidade 1-10 (impacto sobre o leitor)")
    subtlety = Column(Integer, default=5, comment="Sutileza 1-10 (quanto maior, mais oculto)")
    urgency = Column(Integer, default=0, comment="Urgência: 0=sem urgência, 1=requer atenção, 2=resolução urgente")
    
    # === 关联信息 ===
    related_characters = Column(JSON, comment="Lista de nomes de personagens relacionados: ['Personagem 1', 'Personagem 2']")
    related_foreshadow_ids = Column(JSON, comment="IDs de outros foreshadowings relacionados (cadeia)")
    tags = Column(JSON, comment="Lista de etiquetas: ['origem', 'suspense', 'reviravolta']")
    category = Column(String(50), comment="Categoria: identity (origem), mystery (mistério), item (objeto), relationship (relação), event (evento)")
    
    # === 备注和说明 ===
    notes = Column(Text, comment="Notas de criação (visíveis apenas ao autor)")
    resolution_notes = Column(Text, comment="Descrição da forma de resolução")
    
    # === AI辅助设置 ===
    auto_remind = Column(Boolean, default=True, comment="Lembrar automaticamente durante a geração de capítulos")
    remind_before_chapters = Column(Integer, default=5, comment="Quantos capítulos antes começar a lembrar da resolução")
    include_in_context = Column(Boolean, default=True, comment="Incluído no contexto de geração")
    
    # === 时间戳 ===
    created_at = Column(DateTime, server_default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Data de atualização")
    planted_at = Column(DateTime, comment="Data de plantio")
    resolved_at = Column(DateTime, comment="Data de resolução")
    
    def __repr__(self):
        return f"<Foreshadow(id={self.id[:8]}, title={self.title}, status={self.status})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "content": self.content,
            "hint_text": self.hint_text,
            "resolution_text": self.resolution_text,
            "source_type": self.source_type,
            "source_memory_id": self.source_memory_id,
            "plant_chapter_id": self.plant_chapter_id,
            "plant_chapter_number": self.plant_chapter_number,
            "target_resolve_chapter_id": self.target_resolve_chapter_id,
            "target_resolve_chapter_number": self.target_resolve_chapter_number,
            "actual_resolve_chapter_id": self.actual_resolve_chapter_id,
            "actual_resolve_chapter_number": self.actual_resolve_chapter_number,
            "status": self.status,
            "is_long_term": self.is_long_term,
            "importance": self.importance,
            "strength": self.strength,
            "subtlety": self.subtlety,
            "urgency": self.urgency,
            "related_characters": self.related_characters or [],
            "related_foreshadow_ids": self.related_foreshadow_ids or [],
            "tags": self.tags or [],
            "category": self.category,
            "notes": self.notes,
            "resolution_notes": self.resolution_notes,
            "auto_remind": self.auto_remind,
            "remind_before_chapters": self.remind_before_chapters,
            "include_in_context": self.include_in_context,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "planted_at": self.planted_at.isoformat() if self.planted_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
    
    def to_context_string(self) -> str:
        """
        转换为上下文字符串(用于章节生成提示)
        """
        parts = []
        
        # 基本信息
        parts.append(f"Foreshadowing «{self.title}»")
        
        # 埋入信息
        if self.plant_chapter_number:
            parts.append(f"(plantado no capítulo {self.plant_chapter_number})")
        
        # 内容摘要
        content_preview = self.content[:100] if len(self.content) > 100 else self.content
        parts.append(f": {content_preview}")
        
        # 计划回收
        if self.target_resolve_chapter_number:
            parts.append(f" [resolução planejada no capítulo {self.target_resolve_chapter_number}]")
        
        # 关联角色
        if self.related_characters:
            parts.append(f" Envolve: {', '.join(self.related_characters[:3])}")
        
        return "".join(parts)
    
    def get_urgency_level(self, current_chapter: int) -> int:
        """
        计算当前紧急度
        
        Args:
            current_chapter: 当前章节号
        
        Returns:
            0=不紧急, 1=需关注, 2=急需回收, 3=已超期
        """
        if self.status != 'planted' or not self.target_resolve_chapter_number:
            return 0
        
        chapters_remaining = self.target_resolve_chapter_number - current_chapter
        
        if chapters_remaining < 0:
            return 3  # 已超期
        elif chapters_remaining <= 2:
            return 2  # 急需回收
        elif chapters_remaining <= self.remind_before_chapters:
            return 1  # 需关注
        else:
            return 0  # 不紧急