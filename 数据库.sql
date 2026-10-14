DROP TABLE IF EXISTS attachments;
DROP TABLE IF EXISTS ticket_logs;
DROP TABLE IF EXISTS tickets;
DROP TABLE IF EXISTS users;

-- 用户表
CREATE TABLE user(
	id serial PRIMARY KET,
	username varchar(50) NOT NULL UNIQUE,
	password varchar(255) NOT NULL,
	real_name varchar(50) NOT NULL,
	role varchar(20) NOT NULL CHECK(role IN('管理员','运维人员','普通用户')),
	status varchar(10) NOT NULL DEFAULT '正常' CHECK(status IN('正常','已禁用'))，
	created_at timestamp NOT NULL DEFAULT now()
);

-- 工单表
CREATE TABLE tickets(
	id serial PRIMARY KEY,
	ticket_no varchar(20) NOT NULL UNIQUE,
	title varchar(200) NOT NULL,
	type varchar(20) NOT NULL CHECK(type I)
);