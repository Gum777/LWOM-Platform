from fastapi import Depends,Header,HTTPException

from app.db import get_conn
from app.security import decode_token

# 依赖模块：接口执行业务代码之前的公共校验
# get_current_user 从请求头取出登录凭证，校验通过后查出当前登录人；
# require_admin 在其基础上要求角色为管理员；
# fail 统一抛出带状态码的错误。各路由通过 Depends 复用，避免重复实现校验。

def fail(code:int,msg:str):
    # 统一抛业务错误
    raise HTTPException(status_code=code,detail=msg)

def get_current_user(
    authorization:str = Header(default="")
)->dict:
    # 获取请求头凭证，校验后返回当前登录人
    if not authorization.startswith("Bearer "):
        fail(401,"登录已过期")
    payload = decode_token(authorization[7:])
    if not payload:
        fail(401,"登录已过期")
    conn = get_conn()
    try:
        user = conn.execute(
            "SELECT id,username,real_name,role,status "
            "FROM users WHERE id = ?",
            (payload["user_id"],),
        ).fetchone()
    finally:
        conn.close()
    if not user:
        fail(401,"账号已失效")
    if user["status"]!="正常":
        fail(401,"账号已禁用")
    return dict(user)

def require_admin(
    user:dict = Depends(get_current_user)
)->dict:
    if user["role"]!="管理员":
        fail(403,"只有管理员可以执行此操作")
    return user