"""MCP插件测试服务 - 专门处理插件测试逻辑

重构后使用统一的MCPClientFacade门面来管理所有MCP操作。
"""

import time
import json
from typing import Dict, Any, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.mcp_plugin import MCPPlugin
from app.models.settings import Settings as UserSettings
from app.mcp import mcp_client, MCPPluginConfig  # 使用新的统一门面
from app.services.ai_service import create_user_ai_service
from app.schemas.mcp_plugin import MCPTestResult
from app.services.prompt_service import prompt_service
from app.logger import get_logger, summarize_log_value
from app.user_manager import User

logger = get_logger(__name__)


class MCPTestService:
    """MCP插件测试服务（使用统一门面重构）"""

    def _check_plugin_registered(self, plugin: MCPPlugin, user_id: str) -> bool:
        """
        检查插件是否已注册（同步方法，不触发新的连接）

        Args:
            plugin: 插件配置
            user_id: 用户ID

        Returns:
            是否已注册
        """
        return mcp_client.is_registered(user_id, plugin.plugin_name)

    async def test_plugin_connection(
        self,
        plugin: MCPPlugin,
        user_id: str
    ) -> MCPTestResult:
        """
        简单连接测试

        注意：调用此方法前，需要确保插件已通过后台任务注册。

        Args:
            plugin: 插件配置
            user_id: 用户ID

        Returns:
            测试结果
        """
        start_time = time.time()

        try:
            # 检查插件是否已注册（不触发新连接）
            if not self._check_plugin_registered(plugin, user_id):
                return MCPTestResult(
                    success=False,
                    message="Plugin não registrado",
                    error="Sessão MCP não encontrada; habilite o plugin primeiro",
                    suggestions=["Habilite o plugin primeiro", "Se já estiver habilitado, aguarde um instante e tente novamente"]
                )

            # 使用统一门面测试连接
            test_result = await mcp_client.test_connection(user_id, plugin.plugin_name)
            
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            
            if test_result["success"]:
                return MCPTestResult(
                    success=True,
                    message=f"✅ Teste de conexão bem-sucedido",
                    response_time_ms=response_time,
                    tools_count=test_result.get("tools_count", 0),
                    suggestions=[
                        f"Tempo de resposta: {response_time}ms",
                        f"Ferramentas disponíveis: {test_result.get('tools_count', 0)}"
                    ]
                )
            else:
                return MCPTestResult(
                    success=False,
                    message="❌ Falha no teste de conexão",
                    response_time_ms=response_time,
                    error=test_result.get("message", "Erro desconhecido"),
                    error_type=test_result.get("error_type"),
                    suggestions=[
                        "Verifique se o servidor está online",
                        "Confirme se a configuração está correta",
                        "Verifique se a API Key é válida"
                    ]
                )
                
        except Exception as e:
            end_time = time.time()
            response_time = round((end_time - start_time) * 1000, 2)
            
            logger.error(f"测试插件失败: {plugin.plugin_name}, 错误: {e}")
            
            return MCPTestResult(
                success=False,
                message="❌ Falha no teste",
                response_time_ms=response_time,
                error=str(e),
                error_type=type(e).__name__,
                suggestions=[
                    "Verifique se o servidor está online",
                    "Confirme se a configuração está correta",
                    "Verifique se a API Key é válida"
                ]
            )
    
    async def test_plugin_with_ai(
        self,
        plugin: MCPPlugin,
        user: User,
        db_session: AsyncSession
    ) -> MCPTestResult:
        """
        使用AI进行智能工具调用测试
        
        Args:
            plugin: 插件配置
            user: 用户对象
            db_session: 数据库会话
            
        Returns:
            测试结果
        """
        start_time = time.time()
        
        try:
            # 1. 先进行连接测试
            connection_result = await self.test_plugin_connection(plugin, user.user_id)
            
            if not connection_result.success:
                return connection_result
            
            # 2. 使用统一门面获取工具列表
            tools = await mcp_client.get_tools(user.user_id, plugin.plugin_name)
            
            if not tools:
                return MCPTestResult(
                    success=False,
                    message="O plugin não fornece nenhuma ferramenta",
                    error="A lista de ferramentas está vazia",
                    response_time_ms=connection_result.response_time_ms,
                    suggestions=["Verifique a configuração do plugin", "Confirme se o servidor MCP está funcionando normalmente"]
                )
            
            # 3. 获取用户的AI设置
            settings_result = await db_session.execute(
                select(UserSettings).where(UserSettings.user_id == user.user_id)
            )
            user_settings = settings_result.scalar_one_or_none()
            
            if not user_settings or (
                not user_settings.api_key
                and (user_settings.api_provider or "").lower().strip() != "codex"
            ):
                # 没有AI配置，返回简单测试结果
                logger.warning("用户未配置AI服务，跳过智能测试")
                return MCPTestResult(
                    success=True,
                    message=f"✅ Teste de conexão bem-sucedido (IA não configurada; teste de chamada de ferramentas ignorado)",
                    response_time_ms=connection_result.response_time_ms,
                    tools_count=len(tools),
                    suggestions=[
                        f"Teste de conexão: sucesso",
                        f"Ferramentas disponíveis: {len(tools)}",
                        "Dica: configure o serviço de IA para testar a chamada inteligente de ferramentas"
                    ]
                )
            
            # 4. 使用AI选择工具并生成测试参数
            logger.info(f"使用AI分析工具并生成测试计划...")
            
            from app.api.settings import build_fallback_config

            ai_service = create_user_ai_service(
                api_provider=user_settings.api_provider,
                api_key=user_settings.api_key,
                api_base_url=user_settings.api_base_url,
                model_name=user_settings.llm_model,
                temperature=0.3,
                max_tokens=1000,
                fallback=build_fallback_config(user_settings),
            )
            
            # 使用统一门面转换为OpenAI Function Calling格式
            openai_tools = mcp_client.format_tools_for_openai(tools, plugin.plugin_name)
            
            logger.info(f"📋 转换后的OpenAI工具数量: {len(openai_tools)}")
            logger.debug(f"📋 OpenAI工具列表: {[t['function']['name'] for t in openai_tools]}")
            
            # 调用AI选择工具（使用自定义模板系统）
            prompts = await prompt_service.get_mcp_tool_test_prompts(
                plugin_name=plugin.plugin_name,
                user_id=user.user_id,
                db=db_session
            )
            
            # 使用 generate_text 进行 Function Calling（非流式）
            ai_response = await ai_service.generate_text(
                prompt=prompts["user"],
                system_prompt=prompts["system"],
                tools=openai_tools,
                tool_choice="auto"
            )
            
            accumulated_text = ai_response.get("content", "")
            tool_calls = ai_response.get("tool_calls")
            
            # 5. 检查AI是否返回工具调用
            if not tool_calls:
                logger.error(f"❌ AI未返回工具调用")
                return MCPTestResult(
                    success=False,
                    message="❌ Falha no Function Calling da IA",
                    error=f"A IA não retornou uma solicitação de chamada de ferramenta. Resposta: {accumulated_text[:200] if accumulated_text else 'N/A'}",
                    tools_count=len(tools),
                    suggestions=[
                        "Confirme se o modelo de IA usado suporta Function Calling",
                        f"Provider atual: {user_settings.api_provider}",
                        f"Modelo atual: {user_settings.llm_model}"
                    ]
                )
            
            # 6. 解析工具调用
            tool_call = tool_calls[0]
            function = tool_call["function"]
            tool_name_with_prefix = function["name"]
            test_arguments = function["arguments"]
            
            if isinstance(test_arguments, str):
                try:
                    # 使用统一的JSON清洗方法
                    cleaned_args = ai_service._clean_json_response(test_arguments)
                    test_arguments = json.loads(cleaned_args)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ 解析AI参数失败: {e}")
                    return MCPTestResult(
                        success=False,
                        message="❌ Formato de parâmetros retornado pela IA inválido",
                        error=f"Não foi possível interpretar o JSON dos parâmetros: {str(e)}",
                        tools_count=len(tools)
                    )
            
            # 解析插件名和工具名
            try:
                _, tool_name = mcp_client.parse_function_name(tool_name_with_prefix)
            except ValueError:
                tool_name = tool_name_with_prefix
            
            logger.info(f"🤖 AI选择的工具: {tool_name}")
            logger.info(f"📝 AI生成的参数摘要: {summarize_log_value(test_arguments)}")
            
            # 7. 使用统一门面调用MCP工具
            call_start = time.time()
            try:
                tool_result = await mcp_client.call_tool(
                    user_id=user.user_id,
                    plugin_name=plugin.plugin_name,
                    tool_name=tool_name,
                    arguments=test_arguments
                )
                
                call_end = time.time()
                call_time = round((call_end - call_start) * 1000, 2)
                total_time = round((call_end - start_time) * 1000, 2)
                
                # 格式化结果
                result_str = str(tool_result)
                if len(result_str) > 800:
                    result_preview = result_str[:800] + "\n...(resultado truncado)"
                else:
                    result_preview = result_str
                
                return MCPTestResult(
                    success=True,
                    message=f"✅ Teste de Function Calling bem-sucedido! A ferramenta '{tool_name}' foi chamada normalmente",
                    response_time_ms=total_time,
                    tools_count=len(tools),
                    suggestions=[
                        f"🤖 Escolha da IA: {tool_name}",
                        f"📝 Parâmetros: {json.dumps(test_arguments, ensure_ascii=False)}",
                        f"⏱️ Duração: {call_time}ms",
                        f"📊 Resultado:\n{result_preview}"
                    ]
                )
                
            except Exception as call_error:
                call_end = time.time()
                total_time = round((call_end - start_time) * 1000, 2)
                
                logger.warning(f"工具调用失败: {tool_name}, 错误: {call_error}")
                
                return MCPTestResult(
                    success=True,  # 连接成功就算测试通过
                    message=f"⚠️ Conexão bem-sucedida, mas a chamada da ferramenta falhou",
                    response_time_ms=total_time,
                    tools_count=len(tools),
                    error=f"Ferramenta '{tool_name}' falhou na chamada: {str(call_error)}",
                    suggestions=[
                        f"✅ Teste de conexão: sucesso",
                        f"❌ Teste de chamada de ferramenta: falha",
                        f"🤖 Escolha da IA: {tool_name}",
                        f"❌ Erro: {str(call_error)}",
                        "💡 Causas possíveis: API Key inválida, parâmetros incorretos ou limitação do serviço"
                    ]
                )
                
        except Exception as e:
            end_time = time.time()
            total_time = round((end_time - start_time) * 1000, 2)
            
            logger.error(f"测试插件失败: {plugin.plugin_name}, 错误: {e}")
            
            return MCPTestResult(
                success=False,
                message="❌ Falha no teste",
                response_time_ms=total_time,
                error=str(e),
                error_type=type(e).__name__,
                suggestions=[
                    "Verifique se o servidor está online",
                    "Confirme se a configuração está correta",
                    "Verifique se a API Key é válida"
                ]
            )


# 全局单例
mcp_test_service = MCPTestService()
