"""灵感模式API - 通过对话引导创建项目"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import json

from app.database import get_db
from app.services.ai_service import AIService
from app.services.json_helper import loads_json
from app.api.settings import get_user_ai_service
from app.services.prompt_service import PromptService
from app.logger import get_logger

router = APIRouter(prefix="/inspiration", tags=["Modo inspiração"])
logger = get_logger(__name__)


# 不同阶段的temperature设置（递减以保持一致性）
TEMPERATURE_SETTINGS = {
    "title": 0.8,        # 书名阶段可以更有创意
    "description": 0.65, # 简介需要贴合书名和原始想法
    "theme": 0.55,       # 主题需要更加贴合
    "genre": 0.45        # 类型应该很明确
}


def validate_options_response(result: Dict[str, Any], step: str, max_retries: int = 3) -> tuple[bool, str]:
    """
    校验AI返回的选项格式是否正确
    
    Returns:
        (is_valid, error_message)
    """
    # 检查必需字段
    if "options" not in result:
        return False, "Campo options ausente"
    
    options = result.get("options", [])
    
    # 检查options是否为数组
    if not isinstance(options, list):
        return False, "options deve ser uma lista"
    
    # 检查数组长度
    if len(options) < 3:
        return False, f"Poucas opções: são necessárias pelo menos 3, mas há apenas {len(options)}"
    
    if len(options) > 10:
        return False, f"Opções demais: o máximo é 10, mas há {len(options)}"
    
    # 检查每个选项是否为字符串且不为空
    for i, option in enumerate(options):
        if not isinstance(option, str):
            return False, f"A opção {i+1} não é do tipo texto"
        if not option.strip():
            return False, f"A opção {i+1} está vazia"
        if len(option) > 500:
            return False, f"A opção {i+1} é longa demais (mais de 500 caracteres)"
    
    # 根据不同步骤进行特定校验
    if step == "genre":
        # 类型标签应该比较短
        for i, option in enumerate(options):
            if len(option) > 30:
                return False, f"O rótulo de gênero \"{option}\" é longo demais, deve ter entre 2 e 30 caracteres"
    
    return True, ""


@router.post("/generate-options")
async def generate_options(
    data: Dict[str, Any],
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    ai_service: AIService = Depends(get_user_ai_service)
) -> Dict[str, Any]:
    """
    根据当前收集的信息生成下一步的选项建议（带自动重试）
    
    Request:
        {
            "step": "title",  // title/description/theme/genre
            "context": {
                "title": "...",
                "description": "...",
                "theme": "..."
            }
        }
    
    Response:
        {
            "prompt": "引导语",
            "options": ["选项1", "选项2", ...]
        }
    """
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            step = data.get("step", "title")
            context = data.get("context", {})
            
            logger.info(f"灵感模式：生成{step}阶段的选项（第{attempt + 1}次尝试）")
            
            # 获取用户ID
            user_id = getattr(http_request.state, 'user_id', None)
            
            # 获取对应的提示词模板（根据step确定模板key）
            # 新结构：每个步骤有独立的 SYSTEM 和 USER 模板
            template_key_map = {
                "title": ("INSPIRATION_TITLE_SYSTEM", "INSPIRATION_TITLE_USER"),
                "description": ("INSPIRATION_DESCRIPTION_SYSTEM", "INSPIRATION_DESCRIPTION_USER"),
                "theme": ("INSPIRATION_THEME_SYSTEM", "INSPIRATION_THEME_USER"),
                "genre": ("INSPIRATION_GENRE_SYSTEM", "INSPIRATION_GENRE_USER")
            }
            template_keys = template_key_map.get(step)
            
            if not template_keys:
                return {
                    "error": f"Etapa não suportada: {step}",
                    "prompt": "",
                    "options": []
                }
            
            system_key, user_key = template_keys
            
            # 获取自定义提示词模板（分别获取 system 和 user）
            system_template = await PromptService.get_template(system_key, user_id, db)
            user_template = await PromptService.get_template(user_key, user_id, db)
            
            # 准备格式化参数
            format_params = {
                "initial_idea": context.get("initial_idea", context.get("description", "")),
                "title": context.get("title", ""),
                "description": context.get("description", ""),
                "theme": context.get("theme", "")
            }
            
            # 格式化提示词
            system_prompt = PromptService.format_prompt(system_template, **format_params)
            user_prompt = PromptService.format_prompt(user_template, **format_params)
            
            # 如果是重试，在提示词中强调格式要求
            if attempt > 0:
                system_prompt += f"\n\n⚠️ Esta é a tentativa de geração nº {attempt + 1}. Responda estritamente no formato JSON e garanta que a lista options contenha 6 opções válidas!"
            
            # 调用AI生成选项
            # 关键改进：使用递减的temperature以保持后续阶段与前文的一致性
            temperature = TEMPERATURE_SETTINGS.get(step, 0.7)
            logger.info(f"调用AI生成{step}选项... (temperature={temperature})")
            
            # 流式生成并累积文本
            accumulated_text = ""
            async for chunk in ai_service.generate_text_stream(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=temperature
            ):
                accumulated_text += chunk
            
            response = {"content": accumulated_text}
            content = accumulated_text
            logger.info(f"AI返回内容长度: {len(content)}")
            
            # 解析JSON（使用统一的JSON清洗方法）
            try:
                # 使用统一的JSON清洗方法
                cleaned_content = ai_service._clean_json_response(content)
                
                result = loads_json(cleaned_content)
                
                # 校验返回格式
                is_valid, error_msg = validate_options_response(result, step)
                
                if not is_valid:
                    logger.warning(f"⚠️ 第{attempt + 1}次生成格式校验失败: {error_msg}")
                    if attempt < max_retries - 1:
                        logger.info("准备重试...")
                        continue  # 重试
                    else:
                        # 最后一次尝试也失败了
                        return {
                            "prompt": f"Informe o conteúdo para \"{step}\":",
                            "options": ["Pedir à IA para gerar de novo", "Vou digitar eu mesmo"],
                            "error": f"Formato de geração da IA inválido ({error_msg}), foram feitas {max_retries} tentativas automáticas; tente novamente ou digite você mesmo"
                        }
                
                logger.info(f"✅ 第{attempt + 1}次成功生成{len(result.get('options', []))}个有效选项")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"第{attempt + 1}次JSON解析失败: {e}")
                
                if attempt < max_retries - 1:
                    logger.info("JSON解析失败，准备重试...")
                    continue  # 重试
                else:
                    # 最后一次尝试也失败了
                    return {
                        "prompt": f"Informe o conteúdo para \"{step}\":",
                        "options": ["Pedir à IA para gerar de novo", "Vou digitar eu mesmo"],
                        "error": f"Formato de resposta da IA inválido, foram feitas {max_retries} tentativas automáticas; tente novamente ou digite você mesmo"
                    }
        
        except Exception as e:
            logger.error(f"第{attempt + 1}次生成失败: {e}", exc_info=True)
            if attempt < max_retries - 1:
                logger.info("发生异常，准备重试...")
                continue
            else:
                return {
                    "error": str(e),
                    "prompt": "Falha na geração, tente novamente",
                    "options": ["Gerar de novo", "Vou digitar eu mesmo"]
                }
    
    # 理论上不会到这里
    return {
        "error": "Falha na geração",
        "prompt": "Tente novamente",
        "options": []
    }


@router.post("/refine-options")
async def refine_options(
    data: Dict[str, Any],
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    ai_service: AIService = Depends(get_user_ai_service)
) -> Dict[str, Any]:
    """
    基于用户反馈重新生成选项（支持多轮对话）
    
    Request:
        {
            "step": "title",  // 当前步骤
            "context": {
                "initial_idea": "...",
                "title": "...",
                "description": "...",
                "theme": "..."
            },
            "feedback": "我想要更悲剧一些的主题",  // 用户反馈
            "previous_options": ["选项1", "选项2", ...]  // 之前的选项（可选）
        }
    
    Response:
        {
            "prompt": "引导语",
            "options": ["新选项1", "新选项2", ...]
        }
    """
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            step = data.get("step", "title")
            context = data.get("context", {})
            feedback = data.get("feedback", "")
            previous_options = data.get("previous_options", [])
            
            logger.info(f"灵感模式：根据反馈重新生成{step}阶段的选项（第{attempt + 1}次尝试）")
            logger.info(f"用户反馈: {feedback}")
            
            # 获取用户ID
            user_id = getattr(http_request.state, 'user_id', None)
            
            # 获取对应的提示词模板
            template_key_map = {
                "title": ("INSPIRATION_TITLE_SYSTEM", "INSPIRATION_TITLE_USER"),
                "description": ("INSPIRATION_DESCRIPTION_SYSTEM", "INSPIRATION_DESCRIPTION_USER"),
                "theme": ("INSPIRATION_THEME_SYSTEM", "INSPIRATION_THEME_USER"),
                "genre": ("INSPIRATION_GENRE_SYSTEM", "INSPIRATION_GENRE_USER")
            }
            template_keys = template_key_map.get(step)
            
            if not template_keys:
                return {
                    "error": f"Etapa não suportada: {step}",
                    "prompt": "",
                    "options": []
                }
            
            system_key, user_key = template_keys
            
            # 获取自定义提示词模板
            system_template = await PromptService.get_template(system_key, user_id, db)
            user_template = await PromptService.get_template(user_key, user_id, db)
            
            # 准备格式化参数
            format_params = {
                "initial_idea": context.get("initial_idea", context.get("description", "")),
                "title": context.get("title", ""),
                "description": context.get("description", ""),
                "theme": context.get("theme", "")
            }
            
            # 格式化提示词
            system_prompt = PromptService.format_prompt(system_template, **format_params)
            user_prompt = PromptService.format_prompt(user_template, **format_params)
            
            # 添加反馈信息到提示词
            feedback_instruction = f"""

⚠️ O usuário não ficou satisfeito com as opções anteriores e deu o seguinte feedback:
"{feedback}"

Opções geradas anteriormente:
{chr(10).join([f"- {opt}" for opt in previous_options]) if previous_options else "(nenhuma)"}

Ajuste a estratégia de geração conforme o feedback e ofereça novas opções que atendam melhor às expectativas do usuário.
Atenção:
1. Entenda com cuidado a intenção do feedback
2. As novas opções devem refletir claramente o ajuste pedido pelo usuário
3. Mantenha a coerência com o contexto existente
4. Garanta que sejam retornadas 6 opções válidas
"""
            
            system_prompt += feedback_instruction
            
            # 如果是重试，强调格式要求
            if attempt > 0:
                system_prompt += f"\n\n⚠️ Esta é a tentativa de geração nº {attempt + 1}. Responda estritamente no formato JSON!"
            
            # 调用AI生成选项
            temperature = TEMPERATURE_SETTINGS.get(step, 0.7)
            # 反馈生成时使用稍高的temperature以获得更多样化的结果
            temperature = min(temperature + 0.1, 0.9)
            logger.info(f"调用AI根据反馈生成{step}选项... (temperature={temperature})")
            
            # 流式生成并累积文本
            accumulated_text = ""
            async for chunk in ai_service.generate_text_stream(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=temperature
            ):
                accumulated_text += chunk
            
            content = accumulated_text
            logger.info(f"AI返回内容长度: {len(content)}")
            
            # 解析JSON
            try:
                cleaned_content = ai_service._clean_json_response(content)
                result = loads_json(cleaned_content)
                
                # 校验返回格式
                is_valid, error_msg = validate_options_response(result, step)
                
                if not is_valid:
                    logger.warning(f"⚠️ 第{attempt + 1}次生成格式校验失败: {error_msg}")
                    if attempt < max_retries - 1:
                        logger.info("准备重试...")
                        continue
                    else:
                        return {
                            "prompt": f"Informe o conteúdo para \"{step}\":",
                            "options": ["Pedir à IA para gerar de novo", "Vou digitar eu mesmo"],
                            "error": f"Formato de geração da IA inválido ({error_msg}), foram feitas {max_retries} tentativas automáticas"
                        }
                
                logger.info(f"✅ 第{attempt + 1}次根据反馈成功生成{len(result.get('options', []))}个有效选项")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"第{attempt + 1}次JSON解析失败: {e}")
                
                if attempt < max_retries - 1:
                    logger.info("JSON解析失败，准备重试...")
                    continue
                else:
                    return {
                        "prompt": f"Informe o conteúdo para \"{step}\":",
                        "options": ["Pedir à IA para gerar de novo", "Vou digitar eu mesmo"],
                        "error": f"Formato de resposta da IA inválido, foram feitas {max_retries} tentativas automáticas"
                    }
        
        except Exception as e:
            logger.error(f"第{attempt + 1}次根据反馈生成失败: {e}", exc_info=True)
            if attempt < max_retries - 1:
                logger.info("发生异常，准备重试...")
                continue
            else:
                return {
                    "error": str(e),
                    "prompt": "Falha na geração, tente novamente",
                    "options": ["Gerar de novo", "Vou digitar eu mesmo"]
                }
    
    return {
        "error": "Falha na geração",
        "prompt": "Tente novamente",
        "options": []
    }


@router.post("/quick-generate")
async def quick_generate(
    data: Dict[str, Any],
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    ai_service: AIService = Depends(get_user_ai_service)
) -> Dict[str, Any]:
    """
    智能补全：根据用户已提供的部分信息，AI自动补全缺失字段
    
    Request:
        {
            "title": "书名（可选）",
            "description": "简介（可选）",
            "theme": "主题（可选）",
            "genre": ["类型1", "类型2"]（可选）
        }
    
    Response:
        {
            "title": "补全的书名",
            "description": "补全的简介",
            "theme": "补全的主题",
            "genre": ["补全的类型"]
        }
    """
    try:
        logger.info("灵感模式：智能补全")
        
        # 获取用户ID
        user_id = getattr(http_request.state, 'user_id', None)
        
        # 构建补全提示词
        existing_info = []
        if data.get("title"):
            existing_info.append(f"- Título: {data['title']}")
        if data.get("description"):
            existing_info.append(f"- Sinopse: {data['description']}")
        if data.get("theme"):
            existing_info.append(f"- Tema: {data['theme']}")
        if data.get("genre"):
            existing_info.append(f"- Gênero: {', '.join(data['genre'])}")
        
        existing_text = "\n".join(existing_info) if existing_info else "Nenhuma informação ainda"
        
        # 获取自定义提示词模板
        system_template = await PromptService.get_template("INSPIRATION_QUICK_COMPLETE", user_id, db)
        
        # 格式化提示词
        prompts = {
            "system": PromptService.format_prompt(system_template, existing=existing_text),
            "user": "Complete as informações do romance"
        }
        
        # 调用AI - 流式生成并累积文本
        accumulated_text = ""
        async for chunk in ai_service.generate_text_stream(
            prompt=prompts["user"],
            system_prompt=prompts["system"],
            temperature=0.7
        ):
            accumulated_text += chunk
        
        response = {"content": accumulated_text}
        content = accumulated_text
        
        # 解析JSON（使用统一的JSON清洗方法）
        try:
            # 使用统一的JSON清洗方法
            cleaned_content = ai_service._clean_json_response(content)
            
            result = loads_json(cleaned_content)
            
            # 合并用户已提供的信息（用户输入优先）
            final_result = {
                "title": data.get("title") or result.get("title", ""),
                "description": data.get("description") or result.get("description", ""),
                "theme": data.get("theme") or result.get("theme", ""),
                "genre": data.get("genre") or result.get("genre", [])
            }
            
            logger.info(f"✅ 智能补全成功")
            return final_result
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            raise Exception("Formato de resposta da IA inválido, tente novamente")
    
    except Exception as e:
        logger.error(f"智能补全失败: {e}", exc_info=True)
        return {
            "error": str(e)
        }
