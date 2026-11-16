const userInfo = document.getElementById("userInfo");
const logoutBtn = document.getElementById("logoutBtn");

const token = localStorage.getItem("token");
const userText = localStorage.getItem("user");

// 没有登录凭证就直接拒绝并回登录页
if(!token || !userText) {
    window.location.href = "login.html";
}

let user = null;
try {
    user = JSON.parse(userText);
} catch (error) {
    // 内容报错也算未登录
    window.location.href = "login.html";
}

if (user) {
    userInfo.textContent = user.real_name || user.username;
}

logoutBtn.addEventListener("click",function() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "login.html";
});