import secrets
from datetime import datetime,timedelta,timezone
import bcrypt
import jwt
from app.config import DATA_DIR,TOKEN_HOURS

# 安全模块：负责生成密钥、密码加密与校验、登录凭证的签发与校验

def get_secret_key()-> str:
    # 首次运行时自动生成密钥，存到data文件夹，之后每次读取同一个
    key_file = DATA_DIR / "secret.key"
    if not key_file.exists():
        DATA_DIR.mkdir(parents=True,exist_ok=True)
        key_file.write_text(secrets.token_hex(32),encoding="utf-8")
    return key_file.read_text(encoding="utf-8").strip()

SECRET_KEY = get_secret_key()

def hash_password(plain:str) -> str:
    # 明文密码加密存库，数据库看不到原密码
    return bcrypt.hashpw(plain.encode("utf-8"),bcrypt.gensalt()).decode("utf-8")

def verify_password(plain:str,hashed:str)->bool:
    # 登录校验：把输入的密码和库里的密文比对
    try:
        return bcrypt.checkpw(plain.encode("utf-8"),hashed.encode("utf-8"))
    except ValueError:
        return False

def create_token(user_id:int,role:str)->str:
    # 签发登录凭证，写明是谁，什么角色、什么时候过期
    payload = {
        "user_id":user_id,
        "role":role,
        "exp":datetime.now(timezone.utc) + timedelta(hours=TOKEN_HOURS), 
    }
    return jwt.encode(payload,SECRET_KEY,algorithm="HS256")

def decode_token(token:str) -> dict | None:
    # 校验凭证：过期的、伪造的都返回空
    try:
        return jwt.decode(token,SECRET_KEY,algorithms=["HS256"])
    except jwt.PyJWTError:
        return None