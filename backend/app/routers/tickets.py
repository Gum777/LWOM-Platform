from datetime import datetime

from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel

from app.db import get_conn
from app.deps import get_current_user,require_admin

# 工单模块：负责提交、列表、详情、分配、改派、处理完成、关闭、退回、备注

router = APIRouter(prefix="/api/tickets",tags=["工单"])

class TicketIn(BaseModel):
    title:str
    type:str
    priority:str = "中"
    description:str =""

@router.post("")
def create_ticket(data:TicketIn,user:dict = Depends(get_current_user)):
    # 提交工单：编号按 日期-当日序号 生成，同时写一条提交记录
    if data.type not in("保修","咨询","其它"):
        raise HTTPException(status_code=400,detail="工单类型只能为保修、咨询、其它")

    if data.priority not in("高","中","低"):
        raise HTTPException(status_code=400,detail="优先级只能为高、中、低")
    
    today = datetime.now().strftime("%Y%m%d")
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM tickets WHERE ticket_no LIKE ?",
            (today + "-%",),
        ).fetchone()
        ticket_no = f"{today}-{row['n'] + 1:03d}"

        cur = conn.execute(
            "INSERT INTO tickets(ticket_no,title,type,priority,status,submitter_id,description)"
            " VALUES(?,?,?,?,?,?,?)",
            (ticket_no,data.title,data.type,data.priority,"新建",user["id"],data.description),
        )
        ticket_id = cur.lastrowid
        
        cur = conn.execute(
            "INSERT INTO ticket_logs(ticket_id,operator_id,action,content) VALUES(?,?,?,?)",
            (ticket_id,user['id'],"提交","提交工单"),
        )
        conn.commit()
    finally:
        conn.close()

    return{"message":"提交成功","ticket_no":ticket_no}

@router.get("")
def list_tickets(
    status:str = "",
    type:str = "",
    keyword:str = "",
    user:dict = Depends(get_current_user),
):
    # 工单列表：按角色隔离数据，支持状态、类型、关键字筛选
    conn = get_conn()
    try:
        sql = (
            "SELECT t.id,t.ticket_no,t.title,t.type,t.priority,t.status,t.created_at,"
            "s.real_name AS submitter_name,h.real_name AS handler_name "
            "FROM tickets t "
            "JOIN users s ON s.id = t.submitter_id "
            "LEFT JOIN users h ON h.id = t.handler_id "
            "WHERE 1=1"
        )
        params = []

        # 数据隔离：普通用户只看自己提交的
        if user["role"] == "普通用户":
            sql += " AND t.submitter_id = ?"
            params.append(user["id"])
        
        # 数据隔离：运维人员只看分给自己的
        elif user["role"] == "运维人员":
            sql += " AND t.handler_id = ?"
            params.append(user["id"])
        
        # 管理员不加条件，能看到全部
        if status:
            sql += " AND t.status = ?"
            params.append(status)

        if type:
            sql += " AND t.type = ?"
            params.append(type)
        
        if keyword:
            sql += " AND (t.title LIKE ? OR t.ticket_no LIKE ?)"
            params.append("%"+keyword+"%")
            params.append("%"+keyword+"%")

        sql += " ORDER BY t.id DESC"
        rows = conn.execute(sql,params).fetchall()
    finally:
        conn.close()

    return [dict(r) for r in rows]

@router.get("/{ticket_id}")
def get_ticket(
    ticket_id:int,
    user:dict = Depends(get_current_user),
):
    # 工单详情：校验权限并带出操作记录
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT t.id,t.ticket_no,t.title,t.type,t.priority,t.status,t.description,t.submitter_id,t.handler_id,t.created_at,t.updated_at,"
            "s.real_name AS submitter_name,"
            "h.real_name AS handler_name "
            "FROM tickets t JOIN users s ON s.id = t.submitter_id "
            "LEFT JOIN users h ON h.id = t.handler_id WHERE t.id = ?",
            (ticket_id,),
        ).fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="工单不存在",
            )

        if user["role"] == "普通用户":
            if row["submitter_id"] != user["id"]:
                raise HTTPException(
                    status_code=403,
                    detail="无权查看该工单",
                )
        
        if user["role"] == "运维人员":
            if row["handler_id"] != user["id"]:
                raise HTTPException(
                    status_code=403,
                    detail="无权查看该工单"
                )
            
        logs = conn.execute(
            "SELECT l.action,l.content,l.created_at,"
            "u.real_name AS operator_name "
            "FROM ticket_logs l JOIN users u ON u.id = l.operator_id WHERE l.ticket_id = ? ORDER BY l.id",
            (ticket_id,)
        ).fetchall()
    finally:
        conn.close()
    
    detail = dict(row)
    detail["logs"] = [dict(x) for x in logs]
    return detail

class AssignIn(BaseModel):
    handler_id:int

@router.post("/{ticket_id}/assign")
def assign_ticket(
    ticket_id:int,
    data:AssignIn,
    user:dict = Depends(require_admin),
):
    # 分配工单：仅新建状态可分配，分配后转为处理中，并写一条操作记录
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id,status FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

        if not row:
            raise HTTPException(status_code=404,detail="工单不存在")
        
        if row["status"] != "新建":
            raise HTTPException(
                status_code=400,
                detail="只有新建状态的工单可以分配"
            )
        
        handler = conn.execute(
            "SELECT id,real_name,role,status FROM users WHERE id = ?",
            (data.handler_id,),
        ).fetchone()

        if not handler:
            raise HTTPException(status_code=400,detail="处理人不存在")

        if handler["role"] != "运维人员":
            raise HTTPException(status_code=400,detail="只能分配给运维人员")
        
        if handler["status"] != "正常":
            raise HTTPException(status_code=400,detail="该账号已禁用")
        
        conn.execute(
            "UPDATE tickets SET handler_id = ?,status='处理中',"
            "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (data.handler_id,ticket_id),
        )
        conn.execute(
            "INSERT INTO ticket_logs(ticket_id,operator_id,action,content) VALUES(?,?,?,?)",
            (ticket_id,user["id"],"分配","分配给"+handler["real_name"]),
        )
        conn.commit()
    finally:
        conn.close()
    
    return {"message":"分配成功"}

class ReassignIn(BaseModel):
    handler_id:int

@router.post("/{ticket_id}/reassign")
def reassign_ticket(
    ticket_id:int,
    data:ReassignIn,
    user:dict = Depends(require_admin),
):
    # 改派：处理中的工单换处理人
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id,status,handler_id FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="工单不存在",
            )
        
        if row["status"] != "处理中":
            raise HTTPException(
                status_code=400,
                detail="只有处理中的工单可以改派"
            )

        handler = conn.execute(
            "SELECT id,real_name,role,status FROM users WHERE id = ?",
            (data.handler_id,),
        ).fetchone()

        if not handler:
            raise HTTPException(
                status_code=400,
                detail="处理人不存在",
            )

        if handler["role"] != "运维人员":
            raise HTTPException(
                status_code=400,
                detail="只能改派给运维人员",
            )

        if handler["status"] != "正常":
            raise HTTPException(
                status_code=400,
                detail="该账号已禁用",
            )
        
        if handler["id"] == row["handler_id"]:
            raise HTTPException(
                status_code=400,
                detail="已经是处理人",
            )

        conn.execute(
            "UPDATE tickets SET handler_id = ?,updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (data.handler_id,ticket_id),
        )

        conn.execute(
            "INSERT INTO ticket_logs(ticket_id,operator_id,action,content) VALUES(?,?,?,?)",
            (ticket_id,user["id"],"改派","改派给"+handler["real_name"]),
        )

        conn.commit()
    finally:
        conn.close()

    return{"message":"改派成功"}

@router.post("/{ticket_id}/complete")
def complete_ticket(
    ticket_id:int,
    user:dict=Depends(get_current_user),
):
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id,status,handler_id FROM tickets WHERE id = ?",
            (ticket_id,),
        ).fetchone()

        if not row:
            raise HTTPException(
                404,"工单不存在",
            )

        if row["status"] != "处理中":
            raise HTTPException(
                400,"只有处理中的工单可以完成",
            )
        
        if row["handler_id"] != user["id"]:
            raise HTTPException(
                403,"只有处理人可以完成工单",
            )

        conn.execute(
            "UPDATE tickets SET status='待确认',updated_at=CURRENT_TIMESTAMP WHERE id = ?",
            (ticket_id,),
        )

        conn.execute(
            "INSERT INTO ticket_logs(ticket_id,operator_id,action,content) VALUES(?,?,?,?)",
            (ticket_id,user["id"],"处理完成","处理完成"),
        )

        conn.commit()
    finally:
        conn.close()

    return{"message":"已提交待确认"}

@router.post("/{ticket_id}/close")
def close_ticket(
    ticket_id:int,
    user=Depends(get_current_user),
):
    # 处理人或管理员直接关闭
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id,status,handler_id FROM tickets WHERE id=?",
            (ticket_id,),
        ).fetchone()

        if not row:
            raise HTTPException(
                404,"工单不存在",
            )

        st = row["status"]
        if st != "处理中":
            raise HTTPException(
                400,"状态不是处理中",
            )

        is_admin = user["role"] =="管理员"
        is_handler = row["handler_id"] ==user["id"]
        if not is_admin and not is_handler:
            raise HTTPException(
                403,"只有提交人能确定",
            )

        conn.execute(
            "UPDATE tickets SET status='已关闭', updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (ticket_id,),
        )
        conn.execute(
            "INSERT INTO ticket_logs(ticket_id,operator_id,action,content) VALUES(?,?,?,?)",
            (ticket_id,user["id"],"确认关闭","提交人确认关闭"),
        )
        conn.commit()
    finally:
        conn.close()

    return{"message":"工单已关闭"}

@router.post("/{ticket_id}/reject")
def reject_ticket(
    ticket_id:int,
    user=Depends(get_current_user),
):
    # 提交人退回重做
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id,status,submitter_id FROM tickets WHERE id=?",
            (ticket_id,),
        ).fetchone()

        if not row:
            raise HTTPException(
                404,"工单不存在",
            )

        st = row["status"]
        if st != "待确认":
            raise HTTPException(
                400,"状态不是待确定",
            )

        sid = row["submitter_id"]
        if sid != user["id"]:
            raise HTTPException(
                403,"只有提交人能撤回",
            )
        
        conn.execute(
            "INSERT INTO ticket_logs(ticket_id,operator_id,action,content) VALUES(?,?,?,?)",
            (ticket_id,user["id"],"退回","提交人退回重做"),
        )
        conn.commit()
    finally:
        conn.close()
    return{"message":"已退回处理中"}