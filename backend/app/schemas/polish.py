"""AI去味相关的Pydantic模型"""
from pydantic import BaseModel, Field
from typing import Optional


class PolishRequest(BaseModel):
    """AI去味请求模型"""
    original_text: str = Field(..., description="Texto original (gerado por IA)")
    project_id: Optional[int] = Field(None, description="ID do projeto (opcional, para registrar histórico)")
    provider: Optional[str] = Field(None, description="Provedor de IA")
    model: Optional[str] = Field(None, description="Modelo de IA")
    temperature: Optional[float] = Field(0.8, description="Parâmetro de temperatura, recomendado 0.7-0.9")


class PolishResponse(BaseModel):
    """AI去味响应模型"""
    original_text: str = Field(..., description="Texto original")
    polished_text: str = Field(..., description="Texto após remoção de marcas de IA")
    word_count_before: int = Field(..., description="Palavras antes do processamento")
    word_count_after: int = Field(..., description="Palavras após o processamento")