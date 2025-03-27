// Token handling
function getToken() {
    return localStorage.getItem('token');
}

function setToken(token) {
    localStorage.setItem('token', token);
}

function clearToken() {
    localStorage.removeItem('token');
}

// Authentication check
function checkAuth() {
    const token = getToken();
    if (!token && !window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
        window.location.href = '/pages/login';
        return false;
    }
    return true;
}

// Add token to all HTMX requests
document.addEventListener('htmx:configRequest', function(event) {
    const token = getToken();
    if (token) {
        event.detail.headers['Authorization'] = 'Bearer ' + token;
    }
});

// Handle authentication errors
document.addEventListener('htmx:responseError', function(event) {
    if (event.detail.xhr.status === 401) {
        clearToken();
        window.location.href = '/pages/login';
    }
});

// Logout function
function logout() {
    clearToken();
    window.location.href = '/pages/login';
}

// Run on page load
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
});