from datetime import datetime

from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel

from app.db import get_conn
from app.deps import get_current_user

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