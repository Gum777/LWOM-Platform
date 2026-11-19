from fastapi import APIRouter,HTTPException,Depends
from pydantic import BaseModel
from app.db import get_conn 
from app.security import verify_password,create_token,hash_password
from app.deps import get_current_user,require_admin


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

@router.get("/me")
def me(user:dict = Depends(get_current_user)):
    # 返回当前登录人信息，凭证不合格会被get_current_user拦截
    return user
@router.post("/logout")
def logout():
    # 登录凭证由前端删除，后端只返回确认信息
    return{"message":"已退出登录"}

class UserIn(BaseModel):
    username:str
    password:str
    real_name:str
    role:str

@router.post("/users")
def create_user(data:UserIn,admin:dict = Depends(require_admin)):
    # 管理员创建账号，角色只能是数据库的三种
    if data.role not in("管理员","运维人员","普通用户"):
        raise HTTPException(status_code=400,detail="角色只能为管理员、运维人员、普通用户")

    conn = get_conn()
    try:
        exists = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (data.username,),
        ).fetchone()

        if exists:
            raise HTTPException(status_code=400,detail="用户名已存在")

        conn.execute(
            "INSERT INTO users(username,password,real_name,role,status) VALUES(?,?,?,?,?)",
            (data.username,hash_password(data.password),data.real_name,data.role,"正常"),
        )
        conn.commit()
    finally:
        conn.close()

    return{"message":"创建成功"}

@router.get("/users")
def list_users(admin:dict = Depends(require_admin)):
    # 管理员查看全部账号，不返回密码
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT id,username,real_name,role,status,created_at FROM users ORDER BY id",
        ).fetchall()
    finally:
        conn.close()

    return [dict(row) for row in rows]