const API_BASE_URL = 'http://localhost:5001';

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const errorMessage = document.getElementById('errorMessage');
    
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const loginBtn = document.querySelector('.login-btn');
        
        showLoading(loginBtn, true);
        hideError();
        
        login(username, password)
            .then(response => {
                if (response.success) {
                    localStorage.setItem('token', response.access_token);
                    localStorage.setItem('role', response.role);
                    localStorage.setItem('username', username);
                    
                    if (response.role === 'admin') {
                        window.location.href = '/admin';
                    } else {
                        window.location.href = '/home';
                    }
                } else {
                    showError(response.message || '登录失败');
                }
            })
            .catch(error => {
                showError(error.message || '登录失败，请稍后重试');
            })
            .finally(() => {
                showLoading(loginBtn, false);
            });
    });
    
    const quickBtns = document.querySelectorAll('.quick-btn');
    quickBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const user = this.dataset.user;
            const pass = this.dataset.pass;
            document.getElementById('username').value = user;
            document.getElementById('password').value = pass;
        });
    });
});

async function login(username, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            return {
                success: true,
                access_token: data.access_token,
                role: data.role || 'user'
            };
        } else {
            return {
                success: false,
                message: data.detail || '登录失败'
            };
        }
    } catch (error) {
        throw new Error('网络连接失败，请检查后端服务是否启动');
    }
}

function showLoading(btn, loading) {
    if (loading) {
        btn.classList.add('loading');
        btn.disabled = true;
    } else {
        btn.classList.remove('loading');
        btn.disabled = false;
    }
}

function showError(message) {
    const errorElement = document.getElementById('errorMessage');
    errorElement.textContent = message;
    errorElement.classList.add('show');
}

function hideError() {
    const errorElement = document.getElementById('errorMessage');
    errorElement.classList.remove('show');
}