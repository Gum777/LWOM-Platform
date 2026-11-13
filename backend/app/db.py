import sqlite3

from app.config import DATA_DIR,DB_FILE
from app.security import hash_password

# 数据库模块：负责连接数据库、启动时建好四张表、首次运行创建默认管理员

def get_conn()-> sqlite3.Connection:
    # 打开数据库连接，每次请求用完即关
    DATA_DIR.mkdir(parents=True,exist_ok=True)
    conn = sqlite3.connect(DB_FILE,check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db() -> None:
    # 建好四张表，存在则跳过
    conn = get_conn()
    try:
        conn.executescript(
            """
CREATE TABLE IF NOT EXISTS users(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	username varchar(50) NOT NULL UNIQUE,
	password varchar(255) NOT NULL,
	real_name varchar(50) NOT NULL,
	role varchar(20) NOT NULL CHECK(role IN('管理员','运维人员','普通用户')),
	status varchar(10) NOT NULL DEFAULT '正常' CHECK(status IN('正常','已禁用')),
	created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tickets(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	ticket_no varchar(20) NOT NULL UNIQUE,
	title varchar(200) NOT NULL,
	type varchar(20) NOT NULL CHECK(type IN('保修','咨询','其它')),
	priority varchar(10) NOT NULL DEFAULT '中' CHECK(priority IN('高','中','低')), -- 优先级
	status varchar(20) NOT NULL DEFAULT '新建' CHECK(status IN('新建','处理中','待确认','已关闭')),
	submitter_id int NOT NULL REFERENCES users(id), -- 提交人
	handler_id int REFERENCES users(id), -- 处理人
	description text,
	created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
	updated_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ticket_logs(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	ticket_id int NOT NULL REFERENCES tickets(id),
	operator_id int NOT NULL REFERENCES users(id),
	action varchar(20) NOT NULL CHECK(action IN('提交','分配','改派','处理完成','直接关闭','确认关闭','退回','添加备注')),
	content text,
	created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS attachments(
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	ticket_id int NOT NULL REFERENCES tickets(id),
	file_name varchar(255) NOT NULL,
	file_path varchar(500) NOT NULL,
	file_size INTEGER NOT NULL,
	uploader_id int NOT NULL REFERENCES users(id),
	created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);
            """
        )
        conn.commit()
    finally:
        conn.close()

# 首次启动如没有任何账号，自动创建管理员，方便登录
def ensure_admin()->None:
	conn = get_conn()
	try:
		user = conn.execute("SELECT id FROM users LIMIT 1").fetchone()
		if user:
			return
		conn.execute(
			"INSERT INTO users(username,password,real_name,role,status) VALUES(?,?,?,?,?)",
			("admin",hash_password("admin123"),"系统管理员","管理员","正常"),
		)
		conn.commit()
	finally:
		conn.close()