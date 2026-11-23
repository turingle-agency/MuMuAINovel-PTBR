"""职业生成服务"""
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json

from app.constants.languages import language_name
from app.models.project import Project
from app.models.career import Career
from app.services.ai_service import AIService
from app.logger import get_logger

logger = get_logger(__name__)


class CareerService:
    """职业相关业务逻辑服务"""
    
    @staticmethod
    async def get_career_generation_prompt(
        project: Project,
        main_career_count: int = 2,
        sub_career_count: int = 6
    ) -> str:
        """
        构建职业体系生成的提示词
        
        Args:
            project: 项目对象
            main_career_count: 主职业数量
            sub_career_count: 副职业数量
            
        Returns:
            完整的提示词
        """
        project_context = f"""
Informações do projeto:
- Título: {project.title}
- Gênero: {project.genre or 'Não definido'}
- Tema: {project.theme or 'Não definido'}
- Época: {project.world_time_period or 'Não definido'}
- Localização: {project.world_location or 'Não definido'}
- Atmosfera e tom: {project.world_atmosphere or 'Não definido'}
- Regras do mundo: {project.world_rules or 'Não definido'}
"""
        
        user_requirements = f"""
Requisitos de geração:
- Quantidade de carreiras principais: {main_career_count}
- Quantidade de carreiras secundárias: {sub_career_count}
- As carreiras principais devem seguir rigorosamente as regras do mundo e refletir o sistema central de habilidades
- As carreiras secundárias podem ser mais livres e flexíveis, incluindo tipos de produção, suporte e especiais
"""
        
        prompt = f"""{project_context}

{user_requirements}

Gere o sistema completo de carreiras para este livro. Retorne em formato JSON, com a seguinte estrutura:

{{
  "main_careers": [
    {{
      "name": "nome da carreira",
      "description": "descrição da carreira (100-200 palavras)",
      "category": "categoria da carreira (ex.: combate, magia, treinamento físico etc.)",
      "stages": [
        {{"level": 1, "name": "nome do estágio", "description": "descrição do estágio"}},
        {{"level": 2, "name": "nome do estágio", "description": "descrição do estágio"}},
        ... (10 estágios no total)
      ],
      "max_stage": 10,
      "requirements": "requisitos da carreira (ex.: talento ou aptidão específicos)",
      "special_abilities": "descrição das habilidades especiais",
      "worldview_rules": "vínculo com as regras do mundo (explique como a carreira se encaixa no mundo)",
      "attribute_bonuses": {{"strength": "+10%", "intelligence": "+5%"}}
    }}
  ],
  "sub_careers": [
    {{
      "name": "nome da carreira secundária",
      "description": "descrição da carreira",
      "category": "produção/suporte/especial",
      "stages": [
        {{"level": 1, "name": "nome do estágio", "description": "descrição do estágio"}},
        ... (5 a 8 estágios)
      ],
      "max_stage": 5,
      "requirements": "requisitos da carreira",
      "special_abilities": "habilidades especiais"
    }}
  ]
}}

Observações importantes:
1. Os estágios das carreiras principais devem ser detalhados, com um caminho de crescimento claro e nomes de estágio marcantes
2. Escolha carreiras adequadas ao gênero do livro:
   - Fantasia / cultivo: guerreiro, mago, sacerdote etc., com estágios como: aprendiz, adepto, mestre, grão-mestre...
   - Urbano com poderes: classificação dos poderosos, com estágios como: desperto, iniciante, intermediário, avançado...
   - Ficção científica / futuro: soldado geneticamente modificado, piloto de mecha etc., com estágios como: classe E, D, C, B...
   - Realismo / outros gêneros: carreiras reais do cenário (ofícios, cargos, especialidades), com estágios de senioridade
3. As carreiras secundárias devem ser úteis e interessantes, como: alquimista, ferreiro, artífice de formações, domador, curandeiro etc.
4. Todas as carreiras devem estar de acordo com o mundo geral do projeto
5. As descrições dos estágios devem ser concisas e destacar a característica central de cada um
6. **Retorne somente o objeto JSON puro, sem adicionar texto explicativo nem marcações markdown**

Escreva todo o conteúdo em {language_name(project.language)}.
"""
        
        return prompt
    
    @staticmethod
    async def parse_and_save_careers(
        career_data: Dict[str, Any],
        project_id: str,
        db: AsyncSession
    ) -> Dict[str, List[str]]:
        """
        解析AI返回的职业数据并保存到数据库
        
        Args:
            career_data: AI返回的职业数据（已解析为dict）
            project_id: 项目ID
            db: 数据库会话
            
        Returns:
            {"main_careers": [...], "sub_careers": [...]} 创建的职业名称列表
        """
        result = {
            "main_careers": [],
            "sub_careers": []
        }
        
        # 保存主职业
        for idx, career_info in enumerate(career_data.get("main_careers", [])):
            try:
                stages_json = json.dumps(career_info.get("stages", []), ensure_ascii=False)
                attribute_bonuses = career_info.get("attribute_bonuses")
                attribute_bonuses_json = json.dumps(attribute_bonuses, ensure_ascii=False) if attribute_bonuses else None
                
                career = Career(
                    project_id=project_id,
                    name=career_info.get("name", f"Carreira principal sem nome {idx+1}"),
                    type="main",
                    description=career_info.get("description"),
                    category=career_info.get("category"),
                    stages=stages_json,
                    max_stage=career_info.get("max_stage", 10),
                    requirements=career_info.get("requirements"),
                    special_abilities=career_info.get("special_abilities"),
                    worldview_rules=career_info.get("worldview_rules"),
                    attribute_bonuses=attribute_bonuses_json,
                    source="ai"
                )
                db.add(career)
                await db.flush()
                result["main_careers"].append(career.name)
                logger.info(f"  ✅ 创建主职业：{career.name}")
            except Exception as e:
                logger.error(f"  ❌ 创建主职业失败：{str(e)}")
                continue
        
        # 保存副职业
        for idx, career_info in enumerate(career_data.get("sub_careers", [])):
            try:
                stages_json = json.dumps(career_info.get("stages", []), ensure_ascii=False)
                attribute_bonuses = career_info.get("attribute_bonuses")
                attribute_bonuses_json = json.dumps(attribute_bonuses, ensure_ascii=False) if attribute_bonuses else None
                
                career = Career(
                    project_id=project_id,
                    name=career_info.get("name", f"Carreira secundária sem nome {idx+1}"),
                    type="sub",
                    description=career_info.get("description"),
                    category=career_info.get("category"),
                    stages=stages_json,
                    max_stage=career_info.get("max_stage", 5),
                    requirements=career_info.get("requirements"),
                    special_abilities=career_info.get("special_abilities"),
                    worldview_rules=career_info.get("worldview_rules"),
                    attribute_bonuses=attribute_bonuses_json,
                    source="ai"
                )
                db.add(career)
                await db.flush()
                result["sub_careers"].append(career.name)
                logger.info(f"  ✅ 创建副职业：{career.name}")
            except Exception as e:
                logger.error(f"  ❌ 创建副职业失败：{str(e)}")
                continue
        
        await db.commit()
        
        return result
    
    @staticmethod
    async def get_project_careers_summary(project_id: str, db: AsyncSession) -> Dict[str, Any]:
        """
        获取项目职业体系摘要
        
        Args:
            project_id: 项目ID
            db: 数据库会话
            
        Returns:
            职业体系摘要信息
        """
        result = await db.execute(
            select(Career).where(Career.project_id == project_id)
        )
        careers = result.scalars().all()
        
        main_careers = []
        sub_careers = []
        
        for career in careers:
            career_info = {
                "id": career.id,
                "name": career.name,
                "category": career.category,
                "max_stage": career.max_stage
            }
            
            if career.type == "main":
                main_careers.append(career_info)
            else:
                sub_careers.append(career_info)
        
        return {
            "main_careers": main_careers,
            "sub_careers": sub_careers,
            "total_count": len(careers)
        }


# 创建全局服务实例
career_service = CareerService()