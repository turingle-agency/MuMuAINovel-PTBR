"""初始化关系类型数据"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.relationship import RelationshipType
from app.logger import get_logger

logger = get_logger(__name__)


# Tipos de relação semeados (PT-BR). Estes nomes são o vocabulário que os prompts
# pedem à IA em `relationship_type`; os parsers casam por nome exato
# (sem diferenciar maiúsculas/minúsculas), então mantenha prompts e lista em sincronia.
RELATIONSHIP_TYPES = [
    # Família
    {"name": "pai", "category": "family", "reverse_name": "filho(a)", "intimacy_range": "high", "icon": "👨", "description": "Relação de pai com filho ou filha"},
    {"name": "mãe", "category": "family", "reverse_name": "filho(a)", "intimacy_range": "high", "icon": "👩", "description": "Relação de mãe com filho ou filha"},
    {"name": "irmão", "category": "family", "reverse_name": "irmão", "intimacy_range": "high", "icon": "👬", "description": "Relação entre irmãos"},
    {"name": "irmã", "category": "family", "reverse_name": "irmã", "intimacy_range": "high", "icon": "👭", "description": "Relação entre irmãs"},
    {"name": "filho(a)", "category": "family", "reverse_name": "pai/mãe", "intimacy_range": "high", "icon": "👶", "description": "Relação de filho ou filha com os pais"},
    {"name": "cônjuge", "category": "family", "reverse_name": "cônjuge", "intimacy_range": "high", "icon": "💑", "description": "Relação de casamento"},
    {"name": "par romântico", "category": "family", "reverse_name": "par romântico", "intimacy_range": "high", "icon": "💕", "description": "Relação amorosa"},

    # Social
    {"name": "mestre", "category": "social", "reverse_name": "discípulo", "intimacy_range": "high", "icon": "🎓", "description": "Relação de mestre e discípulo (ponto de vista do mestre)"},
    {"name": "discípulo", "category": "social", "reverse_name": "mestre", "intimacy_range": "high", "icon": "📚", "description": "Relação de mestre e discípulo (ponto de vista do discípulo)"},
    {"name": "amigo", "category": "social", "reverse_name": "amigo", "intimacy_range": "medium", "icon": "🤝", "description": "Relação de amizade"},
    {"name": "colega de classe", "category": "social", "reverse_name": "colega de classe", "intimacy_range": "medium", "icon": "🎒", "description": "Relação entre colegas de escola ou turma"},
    {"name": "vizinho", "category": "social", "reverse_name": "vizinho", "intimacy_range": "low", "icon": "🏘️", "description": "Relação entre vizinhos"},
    {"name": "confidente", "category": "social", "reverse_name": "confidente", "intimacy_range": "high", "icon": "💙", "description": "Amigo próximo, de total confiança"},

    # Profissional
    {"name": "chefe", "category": "professional", "reverse_name": "subordinado", "intimacy_range": "low", "icon": "👔", "description": "Relação hierárquica (ponto de vista do chefe)"},
    {"name": "subordinado", "category": "professional", "reverse_name": "chefe", "intimacy_range": "low", "icon": "💼", "description": "Relação hierárquica (ponto de vista do subordinado)"},
    {"name": "colega de trabalho", "category": "professional", "reverse_name": "colega de trabalho", "intimacy_range": "medium", "icon": "🤵", "description": "Relação entre colegas de trabalho"},
    {"name": "parceiro de negócios", "category": "professional", "reverse_name": "parceiro de negócios", "intimacy_range": "medium", "icon": "🤜🤛", "description": "Relação de cooperação"},

    # Hostil
    {"name": "inimigo", "category": "hostile", "reverse_name": "inimigo", "intimacy_range": "low", "icon": "⚔️", "description": "Relação de inimizade"},
    {"name": "inimigo mortal", "category": "hostile", "reverse_name": "inimigo mortal", "intimacy_range": "low", "icon": "💢", "description": "Relação de ódio profundo"},
    {"name": "rival", "category": "hostile", "reverse_name": "rival", "intimacy_range": "low", "icon": "🎯", "description": "Relação de competição"},
    {"name": "nêmesis", "category": "hostile", "reverse_name": "nêmesis", "intimacy_range": "low", "icon": "⚡", "description": "Inimigo predestinado"},
]


async def init_relationship_types():
    """初始化预置的关系类型数据"""
    
    # Import tardio: app.database carrega todos os modelos e não é necessário para ler RELATIONSHIP_TYPES.
    from app.database import AsyncSessionLocal

    relationship_types = RELATIONSHIP_TYPES

    async with AsyncSessionLocal() as session:
        try:
            # 检查是否已经有数据
            result = await session.execute(select(RelationshipType))
            existing = result.scalars().first()
            
            if existing:
                logger.info("关系类型数据已存在，跳过初始化")
                return
            
            # 插入预置数据
            logger.info("开始插入关系类型数据...")
            for rt_data in relationship_types:
                relationship_type = RelationshipType(**rt_data)
                session.add(relationship_type)
            
            await session.commit()
            logger.info(f"成功插入 {len(relationship_types)} 条关系类型数据")
            
        except Exception as e:
            logger.error(f"初始化关系类型数据失败: {str(e)}", exc_info=True)
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(init_relationship_types())