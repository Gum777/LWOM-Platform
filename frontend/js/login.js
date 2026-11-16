const loginForm = document.querySelector(".loginForm");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password")
const loginBtn = document.getElementById("loginBtn")
const loginTip = document.getElementById("loginTip")

function showTip(message,type) {
    loginTip.textContent = message;
    loginTip.className = "login-tip show " + type;
}

function clearTip(){
    loginTip.textContent = "";
    loginTip.className="login-tip";
}

loginForm.addEventListener("submit",async function (event){
    event.preventDefault();

    clearTip();

    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    if(!username) {
        showTip("请输入用户名","error");
        usernameInput.focus();
        return;
    }
    if(!password) {
        showTip("请输入密码","error");
        passwordInput.focus();
        return;
    }

    loginBtn.disabled = true;
    loginBtn.textContent = "登录中...";

    try {
        const response = await fetch("/api/auth/login",{
            method:"POST",
            headers: {
                "Content-Type":"application/json"
            },
            body:JSON.stringify({
                username:username,
                password:password
            })
        });

        const data = await response.json();

        if(!response.ok) {
            let message = "登录失败，请稍后重试";

            if(typeof data.detail === "string") {
                message = data.detail;
            }

            showTip(message,"error");
            return;
        }

        localStorage.setItem("token",data.token);
        localStorage.setItem("user",JSON.stringify(data.user));

        showTip("登录成功","success");

        setTimeout(function(){
            window.location.href = "index.html"
        },600)
        
        // 跳转
    } catch (error) {
        showTip("无法连接服务器，请启动后端","error");
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = "登录";
    }
});