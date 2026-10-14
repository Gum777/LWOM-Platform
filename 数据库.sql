DROP TABLE IF EXISTS attachments;
DROP TABLE IF EXISTS ticket_logs;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS users;

-- 用户表
CREATE TABLE users(
	id serial PRIMARY KEY,
	username varchar(50) NOT NULL UNIQUE,
	password varchar(255) NOT NULL,
	real_name varchar(50) NOT NULL,
	role varchar(20) NOT NULL CHECK(role IN('管理员','运维人员','普通用户')),
	status varchar(10) NOT NULL DEFAULT '正常' CHECK(status IN('正常','已禁用')),
	created_at timestamp NOT NULL DEFAULT now()
);

-- 工单表
CREATE TABLE tickets(
	id serial PRIMARY KEY,
	ticket_no varchar(20) NOT NULL UNIQUE,
	title varchar(200) NOT NULL,
	type varchar(20) NOT NULL CHECK(type IN('保修','咨询','其它'))
);

-- 操作记录表
CREATE TABLE ticket_logs(
	id serial PRIMARY KEY,
	ticket_id int NOT NULL REFERENCES tickets(id),
	operator_id int NOT NULL REFERENCES users(id),
	action varchar(20) NOT NULL CHECK(action IN('提交','分配','改派','处理完成','直接关闭','确认关闭','退回','添加备注')),
	content text,
	created_at timestamp NOT NULL DEFAULT now()
);

-- 附件表
CREATE TABLE attachments(
	id serial PRIMARY KEY,
	ticked_id int NOT NULL REFERENCES tickets(id),
	file_name varchar(255) NOT NULL,
	file_path varchar(500) NOT NULL,
	file_size bigint NOT NULL,
	uploader_id int NOT NULL REFERENCES users(id),
	created_at timestamp NOT NULL DEFAULT now()
)