from fastapi import APIRouter,HTTPException ,Header
from pydantic import BaseModel
from app.db import get_conn 
from app.security import verify_password,create_token,decode_token
from fastapi import APIRouter,HTTPException,Header,Depends

# 账号模块：负责登录、退出、当前登录人、管理员建账号和账号列表
# 登录流程：查账号 -> 校验密码 -> 检查账号状态 -> 签发登录凭证

router = APIRouter(prefix="/api/auth",tags=["账号"])

class LoginIn(BaseModel):
    username:str
    password:str

@router.post("/login")
def login(data:LoginIn):
    conn = get_conn()
    try:
        user = conn.execute(
            "SELECT id,username,password,real_name,role,status FROM users WHERE username = ?",
            (data.username,),
        ).fetchone()
    finally:
        conn.close()

    if not user or not verify_password(data.password,user["password"]):
        raise HTTPException(status_code=400,detail="账号或密码错误")

    if user["status"] !="正常":
        raise HTTPException(status_code=403,detail="该账号已被禁用，请联系管理员")

    token = create_token(user["id"],user["role"])
    return{
        "token":token,
        "user":{
            "id":user["id"],
            "username":user["username"],
            "real_name":user["real_name"],
            "role":user["role"]
        }
    }

def get_current_user(authorization:str = Header(default=""))->dict:
    # 从请求头取出登录凭证，校验通过后返回当前登录人信息
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401,detail="未登录或登录已过期")

    token = authorization[7:]

    payload = decode_token(token)

    if not payload:
        raise HTTPException(status_code=401,detail="未登录或登录已过期")
    
    conn = get_conn()

    try:
        user = conn.execute(
            "SELECT id,username,real_name,role,status FROM users WHERE id = ?",
            (payload["user_id"],),
        ).fetchone()
    finally:
        conn.close()

    if not user:
        raise HTTPException(status_code=401,detail="账号已失效")
    
    if user["status"]!="正常":
        raise HTTPException(status_code=401,detail="账户已禁用")

    return dict(user)

@router.get("/me")
def me(user:dict = Depends(get_current_user)):
    # 返回当前登录人信息，凭证不合格会被get_current_user拦截
    return user
@router.post("/logout")
def logout():
    # 登录凭证由前端删除，后端只返回确认信息
    return{"message":"已退出登录"}