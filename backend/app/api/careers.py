
"""职业管理API"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
import json
from typing import AsyncGenerator

from app.database import get_db
from app.utils.sse_response import SSEResponse, create_sse_response, WizardProgressTracker, wrap_stream_with_heartbeat, HEARTBEAT
from app.models.career import Career, CharacterCareer
from app.models.character import Character
from app.models.project import Project
from app.schemas.career import (
    CareerCreate,
    CareerUpdate,
    CareerResponse,
    CareerListResponse,
    CareerGenerateRequest,
    CharacterCareerResponse,
    CharacterCareerDetail,
    SetMainCareerRequest,
    AddSubCareerRequest,
    UpdateCareerStageRequest,
    CareerStage
)
from app.constants.languages import language_name
from app.services.ai_service import AIService
from app.services.json_helper import loads_json
from app.logger import get_logger, safe_preview
from app.api.settings import get_user_ai_service
from app.api.common import verify_project_access

router = APIRouter(prefix="/careers", tags=["Gerenciamento de carreiras"])
logger = get_logger(__name__)


@router.get("", response_model=CareerListResponse, summary="Listar carreiras")
async def get_careers(
    project_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """获取指定项目的所有职业"""
    user_id = getattr(request.state, 'user_id', None)
    await verify_project_access(project_id, user_id, db)
    
    # 获取总数
    count_result = await db.execute(
        select(func.count(Career.id)).where(Career.project_id == project_id)
    )
    total = count_result.scalar_one()
    
    # 获取职业列表
    result = await db.execute(
        select(Career)
        .where(Career.project_id == project_id)
        .order_by(Career.type, Career.created_at.desc())
    )
    careers = result.scalars().all()
    
    # 分类返回
    main_careers = []
    sub_careers = []
    
    for career in careers:
        # 解析JSON字段
        stages = json.loads(career.stages) if career.stages else []
        attribute_bonuses = json.loads(career.attribute_bonuses) if career.attribute_bonuses else None
        
        career_dict = {
            "id": career.id,
            "project_id": career.project_id,
            "name": career.name,
            "type": career.type,
            "description": career.description,
            "category": career.category,
            "stages": stages,
            "max_stage": career.max_stage,
            "requirements": career.requirements,
            "special_abilities": career.special_abilities,
            "worldview_rules": career.worldview_rules,
            "attribute_bonuses": attribute_bonuses,
            "source": career.source,
            "created_at": career.created_at,
            "updated_at": career.updated_at
        }
        
        if career.type == "main":
            main_careers.append(career_dict)
        else:
            sub_careers.append(career_dict)
    
    return CareerListResponse(
        total=total,
        main_careers=main_careers,
        sub_careers=sub_careers
    )


@router.post("", response_model=CareerResponse, summary="Criar carreira")
async def create_career(
    career_data: CareerCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """手动创建职业"""
    user_id = getattr(request.state, 'user_id', None)
    await verify_project_access(career_data.project_id, user_id, db)
    
    try:
        # 转换stages为JSON字符串
        stages_json = json.dumps([stage.model_dump() for stage in career_data.stages], ensure_ascii=False)
        attribute_bonuses_json = json.dumps(career_data.attribute_bonuses, ensure_ascii=False) if career_data.attribute_bonuses else None
        
        # 创建职业
        career = Career(
            project_id=career_data.project_id,
            name=career_data.name,
            type=career_data.type,
            description=career_data.description,
            category=career_data.category,
            stages=stages_json,
            max_stage=career_data.max_stage,
            requirements=career_data.requirements,
            special_abilities=career_data.special_abilities,
            worldview_rules=career_data.worldview_rules,
            attribute_bonuses=attribute_bonuses_json,
            source=career_data.source
        )
        db.add(career)
        await db.commit()
        await db.refresh(career)
        
        logger.info(f"✅ 创建职业成功：{career.name} (ID: {career.id}, 类型: {career.type})")
        
        return CareerResponse(
            id=career.id,
            project_id=career.project_id,
            name=career.name,
            type=career.type,
            description=career.description,
            category=career.category,
            stages=career_data.stages,
            max_stage=career.max_stage,
            requirements=career.requirements,
            special_abilities=career.special_abilities,
            worldview_rules=career.worldview_rules,
            attribute_bonuses=career_data.attribute_bonuses,
            source=career.source,
            created_at=career.created_at,
            updated_at=career.updated_at
        )
        
    except Exception as e:
        logger.error(f"创建职业失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Falha ao criar a carreira: {str(e)}")


@router.post("/generate-system", summary="Gerar novas carreiras com IA (incremental, streaming)")
async def generate_career_system(
    request_data: CareerGenerateRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    user_ai_service: AIService = Depends(get_user_ai_service)
):
    """
    使用AI生成新职业（增量式，基于已有职业补充，支持SSE流式进度显示）
    
    通过Server-Sent Events返回实时进度信息
    """
    async def generate() -> AsyncGenerator[str, None]:
        tracker = WizardProgressTracker("sistema de carreiras")
        try:
            # 验证用户权限和项目是否存在
            user_id = getattr(http_request.state, 'user_id', None)
            project_id = request_data.project_id
            main_career_count = request_data.main_career_count
            sub_career_count = request_data.sub_career_count
            user_requirements = request_data.user_requirements
            project = await verify_project_access(project_id, user_id, db)
            
            yield await tracker.start()
            
            # 获取已有职业列表
            yield await tracker.loading("Analisando as carreiras existentes...", 0.3)
            
            existing_careers_result = await db.execute(
                select(Career).where(Career.project_id == project_id)
            )
            existing_careers = existing_careers_result.scalars().all()
            
            # 构建已有职业摘要
            existing_main_careers = []
            existing_sub_careers = []
            for career in existing_careers:
                career_summary = f"- {career.name} ({career.category or 'Sem categoria'}, {career.max_stage} estágios)"
                if career.description:
                    career_summary += f": {career.description[:50]}"
                
                if career.type == "main":
                    existing_main_careers.append(career_summary)
                else:
                    existing_sub_careers.append(career_summary)
            
            existing_careers_text = ""
            if existing_main_careers:
                existing_careers_text += f"\nCarreiras principais existentes ({len(existing_main_careers)}):\n" + "\n".join(existing_main_careers)
            if existing_sub_careers:
                existing_careers_text += f"\n\nCarreiras secundárias existentes ({len(existing_sub_careers)}):\n" + "\n".join(existing_sub_careers)
            
            if not existing_careers_text:
                existing_careers_text = "\nAinda não há nenhuma carreira; esta é a primeira criação do sistema de carreiras."
            
            # 构建项目上下文
            yield await tracker.loading("Analisando a construção do mundo do projeto...", 0.6)
            
            project_context = f"""
Informações do projeto:
- Título: {project.title}
- Gênero: {project.genre or 'Não definido'}
- Tema: {project.theme or 'Não definido'}
- Período do mundo: {project.world_time_period or 'Não definido'}
- Localização: {project.world_location or 'Não definido'}
- Atmosfera e tom: {project.world_atmosphere or 'Não definido'}
- Regras do mundo: {project.world_rules or 'Não definido'}
"""
            
            sanitized_user_requirements = user_requirements.strip()
            extra_requirement_text = ""
            if sanitized_user_requirements:
                extra_requirement_text = f"""
Requisitos adicionais do usuário:
{sanitized_user_requirements}

Requisitos de execução:
- Priorize a direção de carreira, o estilo de habilidades, as restrições e os itens a evitar indicados pelo usuário
- Se o pedido do usuário for muito parecido com uma carreira existente, preserve o núcleo do pedido, mas gere uma nova carreira com posicionamento claramente diferente
- Se o pedido do usuário conflitar com a construção do mundo do projeto, reescreva e adapte de forma razoável, sem contrariar a construção do mundo
"""

            generation_requirements = f"""
Situação das carreiras existentes: {existing_careers_text}

Requisitos de geração (incremental):
- Carreiras principais a adicionar desta vez: {main_career_count}
- Carreiras secundárias a adicionar desta vez: {sub_career_count}
- ⚠️ Importante: gere novas carreiras **sem repetir** as existentes, formando um sistema complementar
- As novas carreiras devem preencher as lacunas do sistema atual e enriquecer a diversidade de carreiras
- As carreiras principais devem respeitar rigorosamente as regras do mundo e refletir o sistema central de habilidades
- As carreiras secundárias podem ser mais livres e flexíveis, incluindo tipos de produção, apoio e especiais

{extra_requirement_text}"""
            
            yield await tracker.preparing("Montando o prompt da IA...")
            
            # 构建提示词
            prompt = f"""{project_context}

{generation_requirements}

Gere novas carreiras complementares (incremental) para este projeto de romance. Escreva todo o conteúdo em {language_name(project.language)}. Requisitos:
1. **Analise com atenção as carreiras existentes**, evitando gerar carreiras repetidas ou parecidas
2. **Preencha as lacunas do sistema de carreiras**, tornando-o mais completo e diversificado
3. Se houver poucas carreiras, pode gerar carreiras básicas centrais
4. Se houver muitas carreiras, pode gerar carreiras mais características e especializadas

Retorne no formato JSON, com a seguinte estrutura:

{{
  "main_careers": [
    {{
      "name": "Nome da carreira",
      "description": "Descrição da carreira",
      "category": "Categoria da carreira (ex.: combate, magia etc.)",
      "stages": [
        {{"level": 1, "name": "Nome do estágio", "description": "Descrição do estágio"}},
        {{"level": 2, "name": "Nome do estágio", "description": "Descrição do estágio"}},
        ...
      ],
      "max_stage": 10,
      "requirements": "Requisitos da carreira",
      "special_abilities": "Habilidades especiais",
      "worldview_rules": "Regras do mundo relacionadas",
      "attribute_bonuses": {{"strength": "+10%", "intelligence": "+5%"}}
    }}
  ],
  "sub_careers": [
    {{
      "name": "Nome da carreira secundária",
      "description": "Descrição da carreira",
      "category": "produção/apoio/especial",
      "stages": [...],
      "max_stage": 5,
      "requirements": "Requisitos da carreira",
      "special_abilities": "Habilidades especiais"
    }}
  ]
}}

Observações:
1. **Evite repetição**: o nome e o posicionamento das carreiras geradas não podem repetir os das existentes
2. **Complementaridade**: as novas carreiras devem complementar as existentes e enriquecer o sistema de carreiras
3. As carreiras principais precisam de estágios detalhados, com um caminho de crescimento claro
4. Os nomes dos estágios devem combinar com as características do mundo
5. As carreiras secundárias podem ser mais simples, mas devem ter singularidade
6. Todas as carreiras devem respeitar a construção de mundo geral do projeto
7. Se houver requisitos adicionais do usuário, atenda-os com prioridade; se conflitarem com a construção do mundo, prevalece a construção do mundo, com reescrita razoável
8. Retorne apenas JSON puro, sem adicionar nenhum texto explicativo
"""
            
            yield await tracker.generating(0, max(3000, len(prompt) * 8), "Chamando a IA para gerar novas carreiras...")
            logger.info(f"🎯 开始为项目 {project_id} 生成新职业（增量式，已有{len(existing_careers)}个职业）")
            
            try:
                # 使用流式生成替代非流式
                ai_response = ""
                chunk_count = 0
                estimated_total = max(3000, len(prompt) * 8)
                
                async for chunk in wrap_stream_with_heartbeat(
                    user_ai_service.generate_text_stream(prompt=prompt),
                    heartbeat_interval=15.0
                ):
                    # 心跳哨兵：发送心跳保活，不混入AI响应
                    if chunk is HEARTBEAT:
                        yield await tracker.heartbeat()
                        continue

                    chunk_count += 1
                    ai_response += chunk
                    
                    # 发送内容块
                    yield await SSEResponse.send_chunk(chunk)
                    
                    # 平滑更新进度（避免过于频繁）
                    if chunk_count % 10 == 0:
                        yield await tracker.generating(len(ai_response), estimated_total)
                    
                    # 心跳
                    if chunk_count % 20 == 0:
                        yield await tracker.heartbeat()
                
            except Exception as ai_error:
                logger.error(f"❌ AI服务调用异常：{str(ai_error)}")
                yield await tracker.error(f"Falha na chamada do serviço de IA: {str(ai_error)}")
                return
            
            if not ai_response or not ai_response.strip():
                yield await tracker.error("O serviço de IA retornou uma resposta vazia")
                return
            
            yield await tracker.parsing("Analisando a resposta da IA...", 0.5)
            
            # 清洗并解析JSON
            try:
                cleaned_response = user_ai_service._clean_json_response(ai_response)
                career_data = loads_json(cleaned_response)
                logger.info(f"✅ 职业体系JSON解析成功")
            except json.JSONDecodeError as e:
                logger.error(f"❌ 职业体系JSON解析失败: {e}")
                logger.debug(f"   原始响应预览: {safe_preview(ai_response, 200)}")
                yield await tracker.error(f"O conteúdo retornado pela IA não pôde ser interpretado como JSON: {str(e)}")
                return
            
            yield await tracker.saving("Salvando as carreiras principais no banco de dados...", 0.3)
            
            # 保存主职业
            main_careers_created = []
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
                    main_careers_created.append(career.name)
                    logger.info(f"  ✅ 创建主职业：{career.name}")
                except Exception as e:
                    logger.error(f"  ❌ 创建主职业失败：{str(e)}")
                    continue
            
            yield await tracker.saving("Salvando as carreiras secundárias no banco de dados...", 0.6)
            
            # 保存副职业
            sub_careers_created = []
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
                    sub_careers_created.append(career.name)
                    logger.info(f"  ✅ 创建副职业：{career.name}")
                except Exception as e:
                    logger.error(f"  ❌ 创建副职业失败：{str(e)}")
                    continue
            
            await db.commit()
            
            total_main = len(existing_main_careers) + len(main_careers_created)
            total_sub = len(existing_sub_careers) + len(sub_careers_created)
            
            logger.info(f"🎉 新职业生成完成：新增主职业{len(main_careers_created)}个，新增副职业{len(sub_careers_created)}个")
            logger.info(f"   职业体系总数：主职业{total_main}个，副职业{total_sub}个")
            
            yield await tracker.complete(f"Novas carreiras geradas! ({total_main} principais, {total_sub} secundárias)")
            
            # 发送结果数据
            yield await tracker.result({
                "main_careers_count": len(main_careers_created),
                "sub_careers_count": len(sub_careers_created),
                "main_careers": main_careers_created,
                "sub_careers": sub_careers_created
            })
            
            yield await tracker.done()
            
        except HTTPException as he:
            logger.error(f"HTTP异常: {he.detail}")
            yield await tracker.error(he.detail, he.status_code)
        except Exception as e:
            logger.error(f"生成职业体系失败: {str(e)}")
            yield await tracker.error(f"Falha ao gerar novas carreiras: {str(e)}")
    
    return create_sse_response(generate())


@router.put("/{career_id}", response_model=CareerResponse, summary="Atualizar carreira")
async def update_career(
    career_id: str,
    career_update: CareerUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """更新职业信息"""
    result = await db.execute(
        select(Career).where(Career.id == career_id)
    )
    career = result.scalar_one_or_none()
    
    if not career:
        raise HTTPException(status_code=404, detail="Carreira não encontrada")
    
    # 验证用户权限
    user_id = getattr(request.state, 'user_id', None)
    await verify_project_access(career.project_id, user_id, db)
    
    # 更新字段
    update_data = career_update.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "stages" and value is not None:
            # 转换为JSON字符串
            # model_dump() 已经将嵌套模型转换为字典，所以 value 中的元素已经是 dict
            stages_list = [
                stage if isinstance(stage, dict) else stage.model_dump()
                for stage in value
            ]
            setattr(career, field, json.dumps(stages_list, ensure_ascii=False))
        elif field == "attribute_bonuses" and value is not None:
            # 转换为JSON字符串
            setattr(career, field, json.dumps(value, ensure_ascii=False))
        else:
            setattr(career, field, value)
    
    await db.commit()
    await db.refresh(career)
    
    logger.info(f"✅ 更新职业成功：{career.name} (ID: {career_id})")
    
    # 解析JSON返回
    stages = json.loads(career.stages) if career.stages else []
    attribute_bonuses = json.loads(career.attribute_bonuses) if career.attribute_bonuses else None
    
    return CareerResponse(
        id=career.id,
        project_id=career.project_id,
        name=career.name,
        type=career.type,
        description=career.description,
        category=career.category,
        stages=stages,
        max_stage=career.max_stage,
        requirements=career.requirements,
        special_abilities=career.special_abilities,
        worldview_rules=career.worldview_rules,
        attribute_bonuses=attribute_bonuses,
        source=career.source,
        created_at=career.created_at,
        updated_at=career.updated_at
    )


@router.delete("/{career_id}", summary="Excluir carreira")
async def delete_career(
    career_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """删除职业"""
    result = await db.execute(
        select(Career).where(Career.id == career_id)
    )
    career = result.scalar_one_or_none()
    
    if not career:
        raise HTTPException(status_code=404, detail="Carreira não encontrada")
    
    # 验证用户权限
    user_id = getattr(request.state, 'user_id', None)
    await verify_project_access(career.project_id, user_id, db)
    
    # 检查是否有角色使用该职业
    char_career_result = await db.execute(
        select(func.count(CharacterCareer.id)).where(CharacterCareer.career_id == career_id)
    )
    usage_count = char_career_result.scalar_one()
    
    if usage_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Esta carreira é usada por {usage_count} personagens e não pode ser excluída. Remova primeiro o vínculo de carreira dos personagens."
        )
    
    await db.delete(career)
    await db.commit()
    
    logger.info(f"✅ 删除职业成功：{career.name} (ID: {career_id})")
    
    return {"message": "Carreira excluída com sucesso"}


@router.get("/{career_id}", response_model=CareerResponse, summary="Obter detalhes da carreira")
async def get_career(
    career_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """根据ID获取职业详情"""
    result = await db.execute(
        select(Career).where(Career.id == career_id)
    )
    career = result.scalar_one_or_none()
    
    if not career:
        raise HTTPException(status_code=404, detail="Carreira não encontrada")
    
    # 验证用户权限
    user_id = getattr(request.state, 'user_id', None)
    await verify_project_access(career.project_id, user_id, db)
    
    # 解析JSON字段
    stages = json.loads(career.stages) if career.stages else []
    attribute_bonuses = json.loads(career.attribute_bonuses) if career.attribute_bonuses else None
    
    return CareerResponse(
        id=career.id,
        project_id=career.project_id,
        name=career.name,
        type=career.type,
        description=career.description,
        category=career.category,
        stages=stages,
        max_stage=career.max_stage,
        requirements=career.requirements,
        special_abilities=career.special_abilities,
        worldview_rules=career.worldview_rules,
        attribute_bonuses=attribute_bonuses,
        source=career.source,
        created_at=career.created_at,
        updated_at=career.updated_at
    )


# ===== 角色职业关联API =====

@router.get("/character/{character_id}/careers", response_model=CharacterCareerResponse, summary="Obter as carreiras do personagem")
async def get_character_careers(
    character_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """获取角色的所有职业信息（主职业和副职业）"""
    # 验证角色存在
    char_result = await db.execute(
        select(Character).where(Character.id == character_id)
    )
    character = char_result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(status_code=404, detail="Personagem não encontrado")
    
    # 验证用户权限
    user_id = getattr(request.state, 'user_id', None)
    await verify_project_access(character.project_id, user_id, db)
    
    # 获取角色的所有职业关联
    result = await db.execute(
        select(CharacterCareer, Career)
        .join(Career, CharacterCareer.career_id == Career.id)
        .where(CharacterCareer.character_id == character_id)
        .order_by(CharacterCareer.career_type.desc())  # main排在前
    )
    career_relations = result.all()
    
    main_career = None
    sub_careers = []
    
    for char_career, career in career_relations:
        # 解析职业的阶段信息
        stages = json.loads(career.stages) if career.stages else []
        
        # 找到当前阶段信息
        stage_name = "Estágio desconhecido"
        stage_description = None
        for stage in stages:
            if stage.get("level") == char_career.current_stage:
                stage_name = stage.get("name", f"Estágio {char_career.current_stage}")
                stage_description = stage.get("description")
                break
        
        career_detail = CharacterCareerDetail(
            id=char_career.id,
            character_id=char_career.character_id,
            career_id=char_career.career_id,
            career_name=career.name,
            career_type=char_career.career_type,
            current_stage=char_career.current_stage,
            stage_name=stage_name,
            stage_description=stage_description,
            stage_progress=char_career.stage_progress,
            max_stage=career.max_stage,
            started_at=char_career.started_at,
            reached_current_stage_at=char_career.reached_current_stage_at,
            notes=char_career.notes,
            created_at=char_career.created_at,
            updated_at=char_career.updated_at
        )
        
        if char_career.career_type == "main":
            main_career = career_detail
        else:
            sub_careers.append(career_detail)
    
    return CharacterCareerResponse(
        main_career=main_career,
        sub_careers=sub_careers
    )


@router.post("/character/{character_id}/careers/main", summary="Definir a carreira principal do personagem")
async def set_main_career(
    character_id: str,
    career_request: SetMainCareerRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """设置或更换角色的主职业"""
    # 验证角色存在
    char_result = await db.execute(
        select(Character).where(Character.id == character_id)
    )
    character = char_result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(status_code=404, detail="Personagem não encontrado")
    
    # 验证用户权限
    user_id = getattr(request.state, 'user_id', None)
    await verify_project_access(character.project_id, user_id, db)
    
    # 验证职业存在且为主职业类型
    career_result = await db.execute(
        select(Career).where(
            Career.id == career_request.career_id,
            Career.project_id == character.project_id
        )
    )
    career = career_result.scalar_one_or_none()
    
    if not career:
        raise HTTPException(status_code=404, detail="Carreira não encontrada")
    
    if career.type != "main":
        raise HTTPException(status_code=400, detail="Esta carreira não é do tipo principal e não pode ser definida como carreira principal")
    
    # 验证阶段有效性
    if career_request.current_stage > career.max_stage:
        raise HTTPException(
            status_code=400,
            detail=f"Estágio fora do intervalo, o estágio máximo desta carreira é {career.max_stage}"
        )
    
    # 检查是否已有主职业
    existing_main = await db.execute(
        select(CharacterCareer).where(
            CharacterCareer.character_id == character_id,
            CharacterCareer.career_type == "main"
        )
    )
    current_main = existing_main.scalar_one_or_none()
    
    if current_main:
        # 删除旧的主职业
        await db.delete(current_main)
        logger.info(f"  移除旧主职业关联: {current_main.career_id}")
    
    # 创建新的主职业关联
    char_career = CharacterCareer(
        character_id=character_id,
        career_id=career_request.career_id,
        career_type="main",
        current_stage=career_request.current_stage,
        stage_progress=0,
        started_at=career_request.started_at,
        reached_current_stage_at=career_request.started_at
    )
    db.add(char_career)
    await db.commit()
    
    logger.info(f"✅ 设置主职业成功：角色{character.name} -> {career.name}（第{career_request.current_stage}阶段）")
    
    return {"message": "Carreira principal definida com sucesso", "career_name": career.name}


@router.post("/character/{character_id}/careers/sub", summary="Adicionar carreira secundária ao personagem")
async def add_sub_career(
    character_id: str,
    career_request: AddSubCareerRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """为角色添加副职业"""
    # 验证角色存在
    char_result = await db.execute(
        select(Character).where(Character.id == character_id)
    )
    character = char_result.scalar_one_or_none()
    
    if not character:
        raise HTTPException(status_code=404, detail="Personagem não encontrado")
    
    # 验证用户权限
    user_id = getattr(request.state, 'user_id', None)
    await verify_project_access(character.project_id, user_id, db)
    
    # 验证职业存在且为副职业类型
    career_result = await db.execute(
        select(Career).where(
            Career.id == career_request.career_id,
            Career.project_id == character.project_id
        )
    )
    career = career_result.scalar_one_or_none()
    
    if not career:
        raise HTTPException(status_code=404, detail="Carreira não encontrada")
    
    if career.type != "sub":
        raise HTTPException(status_code=400, detail="Esta carreira não é do tipo secundário e não pode ser adicionada como carreira secundária")
    
    # 验证阶段有效性
    if career_request.current_stage > career.max_stage:
        raise HTTPException(
            status_code=400,
            detail=f"Estágio fora do intervalo, o estágio máximo desta carreira é {career.max_stage}"
        )
    
    # 检查是否已存在
    existing_check = await db.execute(
        select(CharacterCareer).where(
            CharacterCareer.character_id == character_id,
            CharacterCareer.career_id == career_request.career_id
        )
    )
    if existing_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Este personagem já possui esta carreira secundária")
    
    # 检查副职业数量限制（可选，这里设置为最多5个）
    sub_count_result = await db.execute(
        select(func.count(CharacterCareer.id)).where(
            CharacterCareer.character_id == character_id,
            CharacterCareer.career_type == "sub"
        )
    )
    sub_count = sub_count_result.scalar_one()
    
    if sub_count >= 5:
        raise HTTPException(status_code=400, detail="O limite de carreiras secundárias foi atingido (no máximo 5)")
    
    # 创建副职业关联
    char_career = CharacterCareer(
        character_id=character_id,
        career_id=career_request.career_id,
        career_type="sub",
        current_stage=career_request.current_stage,
        stage_progress=0,
        started_at=career_request.started_at,
        reached_current_stage_at=career_request.started_at
    )
    db.add(char_career)
    await db.commit()
    
    logger.info(f"✅ 添加副职业成功：角色{character.name} -> {career.name}（第{career_request.current_stage}阶段）")
    
    return {"message": "Carreira secundária adicionada com sucesso", "career_name": career.name}


@router.put("/character/{character_id}/careers/{career_id}/stage", summary="Atualizar o estágio da carreira")
async def update_career_stage(
    character_id: str,
    career_id: str,
    stage_request: UpdateCareerStageRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """更新角色在某个职业的阶段"""
    # 验证角色职业关联存在
    result = await db.execute(
        select(CharacterCareer, Career, Character)
        .join(Career, CharacterCareer.career_id == Career.id)
        .join(Character, CharacterCareer.character_id == Character.id)
        .where(
            CharacterCareer.character_id == character_id,
            CharacterCareer.career_id == career_id
        )
    )
    relation_data = result.one_or_none()
    
    if not relation_data:
        raise HTTPException(status_code=404, detail="Vínculo entre personagem e carreira não encontrado")
    
    char_career, career, character = relation_data
    
    # 验证用户权限
    user_id = getattr(request.state, 'user_id', None)
    await verify_project_access(character.project_id, user_id, db)
    
    # 验证新阶段有效性
    if stage_request.current_stage > career.max_stage:
        raise HTTPException(
            status_code=400,
            detail=f"Estágio fora do intervalo, o estágio máximo desta carreira é {career.max_stage}"
        )
    
    # 验证阶段递增规则（不能倒退，除非降级）
    if stage_request.current_stage < char_career.current_stage:
        logger.warning(f"⚠️ 角色{character.name}的职业{career.name}阶段降低：{char_career.current_stage} -> {stage_request.current_stage}")
    
    # 更新阶段信息
    char_career.current_stage = stage_request.current_stage
    char_career.stage_progress = stage_request.stage_progress
    if stage_request.reached_current_stage_at:
        char_career.reached_current_stage_at = stage_request.reached_current_stage_at
    if stage_request.notes is not None:
        char_career.notes = stage_request.notes
    
    await db.commit()
    
    logger.info(f"✅ 更新职业阶段成功：{character.name}的{career.name} -> 第{stage_request.current_stage}阶段")
    
    return {
        "message": "Estágio da carreira atualizado com sucesso",
        "career_name": career.name,
        "new_stage": stage_request.current_stage
    }


@router.delete("/character/{character_id}/careers/{career_id}", summary="Remover carreira secundária do personagem")
async def remove_sub_career(
    character_id: str,
    career_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """删除角色的副职业"""
    # 验证角色职业关联存在
    result = await db.execute(
        select(CharacterCareer, Character)
        .join(Character, CharacterCareer.character_id == Character.id)
        .where(
            CharacterCareer.character_id == character_id,
            CharacterCareer.career_id == career_id
        )
    )
    relation_data = result.one_or_none()
    
    if not relation_data:
        raise HTTPException(status_code=404, detail="Vínculo entre personagem e carreira não encontrado")
    
    char_career, character = relation_data
    
    # 验证用户权限
    user_id = getattr(request.state, 'user_id', None)
    await verify_project_access(character.project_id, user_id, db)
    
    # 不允许删除主职业
    if char_career.career_type == "main":
        raise HTTPException(status_code=400, detail="Não é possível remover a carreira principal, apenas trocá-la")
    
    await db.delete(char_career)
    await db.commit()
    
    logger.info(f"✅ 删除副职业成功：角色{character.name}移除职业{career_id}")
    
    return {"message": "Carreira secundária removida com sucesso"}
