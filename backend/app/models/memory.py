"""长期记忆数据模型 - 支持向量检索和剧情分析"""
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Float, JSON, Boolean
from sqlalchemy.sql import func
from app.database import Base
import uuid


class StoryMemory(Base):
    """故事记忆表 - 存储结构化的故事片段和元数据"""
    __tablename__ = "story_memories"
    
    id = Column(String(100), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    chapter_id = Column(String(36), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # 记忆类型
    memory_type = Column(String(50), nullable=False, index=True, comment="""
    Tipo de memória:
    - plot_point: ponto da trama
    - character_event: evento de personagem
    - world_detail: detalhe do mundo
    - hook: gancho (suspense/conflito)
    - foreshadow: foreshadowing
    - dialogue: diálogo importante
    - scene: descrição de cena
    """)
    
    # 记忆内容
    title = Column(String(200), comment="Título/resumo breve da memória")
    content = Column(Text, nullable=False, comment="Resumo do conteúdo da memória (100-500 palavras)")
    full_context = Column(Text, comment="Contexto completo (opcional, para registro detalhado)")
    
    # 关联信息
    related_characters = Column(JSON, comment="IDs dos personagens envolvidos: ['char_id_1', 'char_id_2']")
    related_locations = Column(JSON, comment="Locais envolvidos: ['Local 1', 'Local 2']")
    tags = Column(JSON, comment="Lista de etiquetas: ['suspense', 'reviravolta', 'foreshadowing', 'clímax']")
    
    # 重要性评分 (用于过滤和排序)
    importance_score = Column(Float, default=0.5, comment="Pontuação de importância 0.0-1.0")
    
    # 时间线定位
    story_timeline = Column(Integer, nullable=False, index=True, comment="Posição na linha do tempo da história (número do capítulo)")
    chapter_position = Column(Integer, default=0, comment="Posição dentro do capítulo (caractere)")
    text_length = Column(Integer, default=0, comment="Tamanho do texto (caracteres)")
    
    # 伏笔相关字段
    is_foreshadow = Column(Integer, default=0, comment="Status do foreshadowing: 0=memória comum, 1=plantado, 2=resolvido")
    foreshadow_resolved_at = Column(String(100), ForeignKey("chapters.id", ondelete="SET NULL"), comment="ID do capítulo de resolução do foreshadowing")
    foreshadow_strength = Column(Float, comment="Intensidade do foreshadowing 0.0-1.0")
    
    # 向量数据库关联
    vector_id = Column(String(100), unique=True, comment="ID único no banco vetorial")
    embedding_model = Column(String(100), default="paraphrase-multilingual-MiniLM-L12-v2", comment="Modelo de embedding utilizado")
    
    created_at = Column(DateTime, server_default=func.now(), comment="Data de criação")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="Data de atualização")
    
    def __repr__(self):
        return f"<StoryMemory(id={self.id[:8]}, type={self.memory_type}, title={self.title})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "chapter_id": self.chapter_id,
            "memory_type": self.memory_type,
            "title": self.title,
            "content": self.content,
            "related_characters": self.related_characters,
            "related_locations": self.related_locations,
            "tags": self.tags,
            "importance_score": self.importance_score,
            "story_timeline": self.story_timeline,
            "is_foreshadow": self.is_foreshadow,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class PlotAnalysis(Base):
    """剧情分析表 - 存储AI分析的章节结构和剧情元素"""
    __tablename__ = "plot_analysis"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    chapter_id = Column(String(36), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # 剧情结构分析
    plot_stage = Column(String(50), comment="Estágio da trama: abertura/desenvolvimento/clímax/desfecho/transição")
    conflict_level = Column(Integer, comment="Intensidade do conflito 1-10")
    conflict_types = Column(JSON, comment="Tipos de conflito: ['pessoa vs. pessoa', 'pessoa vs. si mesma', 'pessoa vs. ambiente']")
    
    # 情感分析
    emotional_tone = Column(String(100), comment="Emoção dominante: tensão/aconchego/tristeza/euforia/calma")
    emotional_intensity = Column(Float, comment="Intensidade emocional 0.0-1.0")
    emotional_curve = Column(JSON, comment="Curva emocional: {start: 0.3, middle: 0.7, end: 0.5}")
    
    # 钩子分析 (Hook Analysis)
    hooks = Column(JSON, comment="""Lista de ganchos - elementos que prendem o leitor: [
        {
            "type": "suspense|emoção|conflito|cognição",
            "content": "conteúdo específico",
            "strength": 8,
            "position": "início|meio|fim"
        }
    ]""")
    hooks_count = Column(Integer, default=0, comment="Quantidade de ganchos")
    hooks_avg_strength = Column(Float, comment="Intensidade média dos ganchos")
    
    # 伏笔分析 (Foreshadowing Analysis)
    foreshadows = Column(JSON, comment="""Lista de foreshadowings: [
        {
            "content": "conteúdo do foreshadowing",
            "type": "planted|resolved",
            "strength": 7,
            "subtlety": 8,
            "reference_chapter": 3
        }
    ]""")
    foreshadows_planted = Column(Integer, default=0, comment="Foreshadowings plantados neste capítulo")
    foreshadows_resolved = Column(Integer, default=0, comment="Foreshadowings resolvidos neste capítulo")
    
    # 关键情节点 (Plot Points)
    plot_points = Column(JSON, comment="""Lista de pontos da trama: [
        {
            "content": "descrição do ponto da trama",
            "importance": 0.9,
            "type": "revelation|conflict|resolution|transition",
            "impact": "descrição do impacto na história"
        }
    ]""")
    plot_points_count = Column(Integer, default=0, comment="Quantidade de pontos da trama")
    
    # 角色状态追踪 (Character State Tracking)
    character_states = Column(JSON, comment="""Mudanças de estado dos personagens: [
        {
            "character_id": "xxx",
            "character_name": "João",
            "state_before": "indeciso",
            "state_after": "convicto",
            "psychological_change": "descrição interior",
            "key_event": "evento gatilho",
            "relationship_changes": {"Pedro": "mudança na relação"}
        }
    ]""")
    
    # 场景和氛围
    scenes = Column(JSON, comment="Lista de cenas: [{location: 'local', atmosphere: 'atmosfera', duration: 'duração'}]")
    pacing = Column(String(50), comment="Ritmo: slow|moderate|fast|varied")
    
    # 质量评分
    overall_quality_score = Column(Float, comment="Pontuação geral de qualidade 0.0-10.0")
    pacing_score = Column(Float, comment="Pontuação de ritmo 0.0-10.0")
    engagement_score = Column(Float, comment="Pontuação de atratividade 0.0-10.0")
    coherence_score = Column(Float, comment="Pontuação de coerência 0.0-10.0")
    
    # 文本分析报告
    analysis_report = Column(Text, comment="Relatório de análise completo em texto")
    suggestions = Column(JSON, comment="Lista de sugestões de melhoria: ['sugestão 1', 'sugestão 2']")
    
    # 统计信息
    word_count = Column(Integer, comment="Palavras do capítulo")
    dialogue_ratio = Column(Float, comment="Proporção de diálogo 0.0-1.0")
    description_ratio = Column(Float, comment="Proporção de descrição 0.0-1.0")
    
    created_at = Column(DateTime, server_default=func.now(), comment="Data da análise")
    
    def __repr__(self):
        return f"<PlotAnalysis(chapter_id={self.chapter_id[:8]}, stage={self.plot_stage}, quality={self.overall_quality_score})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "chapter_id": self.chapter_id,
            "plot_stage": self.plot_stage,
            "conflict_level": self.conflict_level,
            "conflict_types": self.conflict_types or [],
            "emotional_tone": self.emotional_tone,
            "emotional_intensity": self.emotional_intensity or 0.0,
            "hooks": self.hooks or [],
            "hooks_count": self.hooks_count or 0,
            "foreshadows": self.foreshadows or [],
            "foreshadows_planted": self.foreshadows_planted or 0,
            "foreshadows_resolved": self.foreshadows_resolved or 0,
            "plot_points": self.plot_points or [],
            "plot_points_count": self.plot_points_count or 0,
            "character_states": self.character_states or [],
            "scenes": self.scenes or [],
            "pacing": self.pacing,
            "overall_quality_score": self.overall_quality_score or 0.0,
            "pacing_score": self.pacing_score or 0.0,
            "engagement_score": self.engagement_score or 0.0,
            "coherence_score": self.coherence_score or 0.0,
            "analysis_report": self.analysis_report,
            "suggestions": self.suggestions or [],
            "dialogue_ratio": self.dialogue_ratio or 0.0,
            "description_ratio": self.description_ratio or 0.0,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }