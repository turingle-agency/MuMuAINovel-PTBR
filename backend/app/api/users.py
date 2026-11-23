"""
用户管理 API
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.user_manager import user_manager, User
from app.user_password import password_manager

router = APIRouter(prefix="/users", tags=["Gerenciamento de usuários"])


def require_login(request: Request):
    """依赖：要求用户已登录"""
    if not hasattr(request.state, "user") or not request.state.user:
        raise HTTPException(status_code=401, detail="É necessário fazer login")
    return request.state.user


def require_admin(request: Request):
    """依赖：要求用户为管理员"""
    user = require_login(request)
    if not request.state.is_admin:
        raise HTTPException(status_code=403, detail="É necessária permissão de administrador")
    return user


class SetAdminRequest(BaseModel):
    user_id: str
    is_admin: bool


class ResetPasswordRequest(BaseModel):
    user_id: str
    new_password: Optional[str] = None  # 如果为空则由系统生成临时密码


@router.get("/current")
async def get_current_user(user: User = Depends(require_login)):
    """获取当前登录用户信息"""
    return user.dict()


@router.get("", response_model=List[dict])
async def list_users(admin_user: User = Depends(require_admin)):
    """
    获取所有用户列表（仅管理员）
    """
    users = await user_manager.get_all_users()
    return [user.dict() for user in users]


@router.post("/set-admin")
async def set_admin(
    data: SetAdminRequest,
    request: Request,
    admin_user: User = Depends(require_admin)
):
    """
    设置用户的管理员权限（仅管理员）
    
    限制：
    - 不能撤销自己的管理员权限
    - 至少保留一个管理员
    """
    # 检查是否尝试撤销自己的权限
    if data.user_id == admin_user.user_id and not data.is_admin:
        raise HTTPException(
            status_code=400,
            detail="Você não pode revogar sua própria permissão de administrador"
        )
    
    # 尝试设置管理员权限
    success = await user_manager.set_admin(data.user_id, data.is_admin)
    
    if not success:
        if not data.is_admin:
            raise HTTPException(
                status_code=400,
                detail="Não é possível revogar a permissão: é preciso manter pelo menos um administrador"
            )
        else:
            raise HTTPException(
                status_code=404,
                detail="Usuário não encontrado"
            )
    
    return {
        "message": f"Permissão de administrador {'concedida' if data.is_admin else 'revogada'}",
        "user_id": data.user_id,
        "is_admin": data.is_admin
    }


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    admin_user: User = Depends(require_admin)
):
    """
    删除用户（仅管理员）
    
    限制：
    - 不能删除管理员用户
    """
    success = await user_manager.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Não é possível excluir este usuário (não existe ou é administrador)"
        )
    
    return {
        "message": "Usuário excluído",
        "user_id": user_id
    }


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    admin_user: User = Depends(require_admin)
):
    """获取指定用户信息（仅管理员）"""
    user = await user_manager.get_user(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return user.dict()


@router.post("/reset-password")
async def reset_user_password(
    data: ResetPasswordRequest,
    admin_user: User = Depends(require_admin)
):
    """
    重置用户密码（仅管理员）
    
    如果提供了 new_password，则设置为指定密码
    如果未提供 new_password，则由系统生成临时密码
    
    限制：
    - 不能重置自己的密码（应该使用修改密码功能）
    """
    # 检查是否尝试重置自己的密码
    if data.user_id == admin_user.user_id:
        raise HTTPException(
            status_code=400,
            detail="Você não pode redefinir a própria senha, use a função de alterar senha"
        )
    
    # 检查目标用户是否存在
    target_user = await user_manager.get_user(data.user_id)
    if not target_user:
        raise HTTPException(
            status_code=404,
            detail="Usuário de destino não encontrado"
        )
    
    # 重置密码
    try:
        generated_password = data.new_password
        if not generated_password:
            import secrets
            generated_password = secrets.token_urlsafe(12)

        await password_manager.set_password(
            target_user.user_id,
            target_user.username,
            generated_password
        )
        
        # 如果使用了默认密码，返回密码供管理员告知用户
        message = "Senha redefinida com sucesso"
        response_data = {
            "message": message,
            "user_id": data.user_id,
            "username": target_user.username
        }
        
        if not data.new_password:
            response_data["temporary_password"] = generated_password
            response_data["message"] = "A senha foi redefinida para uma senha temporária gerada pelo sistema, avise o usuário para alterá-la o quanto antes"
        
        return response_data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Falha ao redefinir a senha: {str(e)}"
        )
