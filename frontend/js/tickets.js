function loadTickets(){
    let p=new URLSearchParams();
    let s=document.getElementById("statusFilter").value;
    let t=document.getElementById("typeFilter").value;
    let k=document.getElementById("keywordInput").value;

    if(s) p.append("status",s);
    if(t) p.append("type",t);
    if(k) p.append("keyword",k);

    fetch("/api/tickets?"+p.toString(),{
        headers:{"Authorization":"Bearer "+token}
    }).then(function(r){return r.json()}).then(function(list){
        renderRows(list);
    });
}

function renderRows(list){
    let tb=document.getElementById("ticketBody");
    let total=document.getElementById("totalCount");
    total.textContent="(共"+list.length+"条)";

    if(list.length==0){
        tb.innerHTML='<tr><td colspan="8" class="page-empty">'+'暂无工单</td></tr>';
        return;
    }

    let html="";
    for(let i=0;i<list.length;i++){
        let x=list[i];
        let h=x.handler_name || "-";
        html+='<tr>';
        html+='<td>'+x.ticket_no+'</td>';
        html+='<td>'+x.title+'</td>';
        html+='<td>'+x.type+'</td>';
        html+='<td>'+x.priority+'</td>';
        html+='<td>'+x.status+'</td>';
        html+='<td>'+h+'</td>';
        html+='<td>'+x.created_at+'</td>';
        html+='<td>-</td>';
        html+='</tr>';
    }
    tb.innerHTML=html;
}
loadTickets();