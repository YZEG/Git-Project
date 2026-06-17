const API_BASE_URL = 'http://localhost:5001';

let currentBookPage = 1;
let currentUserPage = 1;
let editingBook = null;
let editingUser = null;

document.addEventListener('DOMContentLoaded', function() {
    checkLogin();
    
    document.getElementById('adminName').textContent = localStorage.getItem('username') || '管理员';
    
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', function() {
            switchPage(this.dataset.page);
        });
    });
    
    document.getElementById('bookForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveBook();
    });
    
    document.getElementById('userForm').addEventListener('submit', function(e) {
        e.preventDefault();
        saveUser();
    });
    
    document.getElementById('detailModal').addEventListener('click', function(e) {
        if (e.target === this) {
            closeDetailModal();
        }
    });
    
    document.getElementById('bookTagsInput').addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            addTag();
        }
    });
    
    loadBooks();
});

function checkLogin() {
    const token = localStorage.getItem('token');
    const role = localStorage.getItem('role');
    
    if (!token || role !== 'admin') {
        window.location.href = 'index.html';
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    localStorage.removeItem('username');
    window.location.href = 'index.html';
}

function switchPage(pageName) {
    const pages = document.querySelectorAll('.page');
    const navItems = document.querySelectorAll('.nav-item');
    
    pages.forEach(page => page.classList.remove('active'));
    navItems.forEach(item => item.classList.remove('active'));
    
    document.getElementById(pageName).classList.add('active');
    document.querySelector(`[data-page="${pageName}"]`).classList.add('active');
    
    document.getElementById('pageTitle').textContent = {
        books: '书籍管理',
        users: '用户管理',
        statistics: '数据统计',
        spider: '爬虫工具'
    }[pageName];

    const addBtn = document.getElementById('addBtn');
    if (pageName === 'books') {
        addBtn.style.display = 'flex';
        addBtn.onclick = openAddModal;
        loadBooks();
    } else if (pageName === 'users') {
        addBtn.style.display = 'flex';
        addBtn.onclick = openAddUserModal;
        loadUsers();
    } else if (pageName === 'spider') {
        addBtn.style.display = 'none';
    } else {
        addBtn.style.display = 'none';
        loadStatistics();
    }
}

async function loadBooks(page = 1) {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/api/books?page=${page}&page_size=10`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            renderBooks(data.books);
            renderPagination(data.total_pages, data.current_page, 'books');
            currentBookPage = page;
        }
    } catch (error) {
        console.error('加载书籍失败:', error);
    }
}

function renderBooks(books) {
    const tbody = document.getElementById('booksTableBody');
    tbody.innerHTML = '';
    
    if (books.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#999;padding:30px;">暂无书籍</td></tr>';
        return;
    }
    
    books.forEach(book => {
        const tags = book.tags ? book.tags.split(',').map(tag => `<span class="table-tag">${tag.trim()}</span>`).join('') : '-';
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${book.id}</td>
            <td><span class="book-name-link" onclick="showBookDetail(${book.id})">${book.name}</span></td>
            <td>${book.author}</td>
            <td><span class="status-badge ${book.status === '连载' ? 'serializing' : 'completed'}">${book.status}</span></td>
            <td style="display: flex; flex-wrap: wrap; gap: 6px;">${tags}</td>
            <td>
                <div class="action-btns">
                    <button class="action-btn edit-btn" onclick="editBook(${book.id})">编辑</button>
                    <button class="action-btn delete-btn" onclick="deleteBook(${book.id})">删除</button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

async function showBookDetail(bookId) {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/api/books/${bookId}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const book = await response.json();
            document.getElementById('detailModalTitle').textContent = book.name;
            document.getElementById('detailAuthor').textContent = book.author;
            document.getElementById('detailStatus').textContent = book.status;
            document.getElementById('detailStatus').className = `status ${book.status === '连载' ? 'serializing' : 'completed'}`;
            document.getElementById('detailTags').innerHTML = book.tags ? 
                book.tags.split(',').map(tag => `<span class="detail-tag">${tag.trim()}</span>`).join('') : '<span style="color:#999;">无</span>';
            document.getElementById('detailIntro').textContent = book.intro || '暂无简介';
            document.getElementById('detailModal').classList.add('show');
        }
    } catch (error) {
        console.error('加载书籍详情失败:', error);
    }
}

function closeDetailModal() {
    document.getElementById('detailModal').classList.remove('show');
}

function renderPagination(totalPages, currentPage, type) {
    const container = document.getElementById(`${type}Pagination`);
    container.innerHTML = '';
    
    const maxVisible = 5;
    let start = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let end = Math.min(totalPages, start + maxVisible - 1);
    
    if (end - start + 1 < maxVisible) {
        start = Math.max(1, end - maxVisible + 1);
    }
    
    const prevBtn = document.createElement('button');
    prevBtn.textContent = '上一页';
    prevBtn.disabled = currentPage <= 1;
    prevBtn.onclick = () => type === 'books' ? loadBooks(currentPage - 1) : loadUsers(currentPage - 1);
    container.appendChild(prevBtn);
    
    for (let i = start; i <= end; i++) {
        const btn = document.createElement('button');
        btn.textContent = i;
        btn.className = i === currentPage ? 'active' : '';
        btn.onclick = () => type === 'books' ? loadBooks(i) : loadUsers(i);
        container.appendChild(btn);
    }
    
    const nextBtn = document.createElement('button');
    nextBtn.textContent = '下一页';
    nextBtn.disabled = currentPage >= totalPages;
    nextBtn.onclick = () => type === 'books' ? loadBooks(currentPage + 1) : loadUsers(currentPage + 1);
    container.appendChild(nextBtn);
}

function openAddModal() {
    editingBook = null;
    document.getElementById('modalTitle').textContent = '新增书籍';
    document.getElementById('bookName').value = '';
    document.getElementById('bookAuthor').value = '';
    document.getElementById('bookStatus').value = '连载';
    document.getElementById('bookTagsInput').value = '';
    document.getElementById('bookIntro').value = '';
    clearTags();
    document.getElementById('bookModal').classList.add('show');
}

function editBook(bookId) {
    fetchBook(bookId).then(book => {
        editingBook = book;
        document.getElementById('modalTitle').textContent = '编辑书籍';
        document.getElementById('bookName').value = book.name;
        document.getElementById('bookAuthor').value = book.author;
        document.getElementById('bookStatus').value = book.status;
        document.getElementById('bookTagsInput').value = '';
        document.getElementById('bookIntro').value = book.intro || '';
        clearTags();
        if (book.tags) {
            book.tags.split(',').forEach(tag => {
                addTagToContainer(tag.trim());
            });
        }
        document.getElementById('bookModal').classList.add('show');
    });
}

function clearTags() {
    document.getElementById('tagsContainer').innerHTML = '';
}

function addTag() {
    const input = document.getElementById('bookTagsInput');
    const tag = input.value.trim();
    if (tag && !isTagExists(tag)) {
        addTagToContainer(tag);
        input.value = '';
    }
}

function addTagToContainer(tag) {
    const container = document.getElementById('tagsContainer');
    const tagElement = document.createElement('span');
    tagElement.className = 'edit-tag';
    tagElement.innerHTML = `${tag} <span class="remove-tag" onclick="removeTag(this)">×</span>`;
    container.appendChild(tagElement);
}

function isTagExists(tag) {
    const tags = document.querySelectorAll('.edit-tag');
    for (const t of tags) {
        if (t.textContent.trim().replace('×', '').trim() === tag) {
            return true;
        }
    }
    return false;
}

function removeTag(element) {
    element.parentElement.remove();
}

function getTagsValue() {
    const tags = document.querySelectorAll('.edit-tag');
    const tagList = [];
    tags.forEach(tag => {
        tagList.push(tag.textContent.trim().replace('×', '').trim());
    });
    return tagList.join(',');
}

async function fetchBook(bookId) {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE_URL}/api/books/${bookId}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    return response.json();
}

async function saveBook() {
    const bookData = {
        name: document.getElementById('bookName').value,
        author: document.getElementById('bookAuthor').value,
        status: document.getElementById('bookStatus').value,
        tags: getTagsValue() || null,
        intro: document.getElementById('bookIntro').value || null
    };
    
    try {
        const token = localStorage.getItem('token');
        let response;
        
        if (editingBook) {
            response = await fetch(`${API_BASE_URL}/api/books/${editingBook.id}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(bookData)
            });
        } else {
            response = await fetch(`${API_BASE_URL}/api/books`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(bookData)
            });
        }
        
        if (response.ok) {
            closeModal();
            loadBooks(currentBookPage);
        } else {
            const data = await response.json();
            alert(data.detail || '保存失败');
        }
    } catch (error) {
        alert('保存失败，请稍后重试');
    }
}

function closeModal() {
    document.getElementById('bookModal').classList.remove('show');
    editingBook = null;
}

async function deleteBook(bookId) {
    if (!confirm('确定要删除这本书籍吗？')) return;
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/api/books/${bookId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            loadBooks(currentBookPage);
        } else {
            const data = await response.json();
            alert(data.detail || '删除失败');
        }
    } catch (error) {
        alert('删除失败，请稍后重试');
    }
}

function searchBooks() {
    const keyword = document.getElementById('bookSearch').value;
    const status = document.getElementById('bookStatusFilter').value;
    
    if (!keyword && !status) {
        loadBooks(1);
        return;
    }
    
    fetchBooks(keyword, status);
}

async function fetchBooks(keyword = '', status = '') {
    try {
        const token = localStorage.getItem('token');
        let url = `${API_BASE_URL}/api/books/search?page=1&page_size=10`;
        
        if (keyword) url += `&keyword=${encodeURIComponent(keyword)}`;
        if (status) url += `&status=${encodeURIComponent(status)}`;
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            renderBooks(data.books);
            renderPagination(data.total_pages, data.current_page, 'books');
            currentBookPage = data.current_page;
        }
    } catch (error) {
        console.error('搜索失败:', error);
    }
}

async function loadUsers(page = 1) {
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/api/users?page=${page}&page_size=10`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            renderUsers(data.users);
            renderPagination(data.total_pages, data.current_page, 'users');
            currentUserPage = page;
        }
    } catch (error) {
        console.error('加载用户失败:', error);
    }
}

function renderUsers(users) {
    const tbody = document.getElementById('usersTableBody');
    tbody.innerHTML = '';
    
    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#999;padding:30px;">暂无用户</td></tr>';
        return;
    }
    
    users.forEach(user => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${user.id}</td>
            <td>${user.username}</td>
            <td>${user.phone || '-'}</td>
            <td><span class="role-badge ${user.role}">${user.role === 'admin' ? '管理员' : '普通用户'}</span></td>
            <td>${formatDate(user.created_at)}</td>
            <td>
                <div class="action-btns">
                    <button class="action-btn edit-btn" onclick="editUser(${user.id})">编辑</button>
                    <button class="action-btn delete-btn" onclick="deleteUser(${user.id})">删除</button>
                </div>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN');
}

function openAddUserModal() {
    editingUser = null;
    document.getElementById('userModalTitle').textContent = '新增用户';
    document.getElementById('userId').value = '';
    document.getElementById('userName').value = '';
    document.getElementById('userPhone').value = '';
    document.getElementById('userPassword').value = '';
    document.getElementById('userRole').value = 'user';
    document.getElementById('userModal').classList.add('show');
}

function editUser(userId) {
    fetchUser(userId).then(user => {
        editingUser = user;
        document.getElementById('userModalTitle').textContent = '编辑用户';
        document.getElementById('userId').value = user.id;
        document.getElementById('userName').value = user.username;
        document.getElementById('userPhone').value = user.phone || '';
        document.getElementById('userPassword').value = '';
        document.getElementById('userRole').value = user.role;
        document.getElementById('userModal').classList.add('show');
    });
}

async function fetchUser(userId) {
    const token = localStorage.getItem('token');
    const response = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    });
    return response.json();
}

async function saveUser() {
    const userId = document.getElementById('userId').value;
    const userData = {
        username: document.getElementById('userName').value,
        phone: document.getElementById('userPhone').value || null,
        role: document.getElementById('userRole').value
    };
    
    const password = document.getElementById('userPassword').value;
    if (password) {
        userData.password = password;
    }
    
    try {
        const token = localStorage.getItem('token');
        let response;
        
        if (userId) {
            response = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });
        } else {
            response = await fetch(`${API_BASE_URL}/api/users`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });
        }
        
        if (response.ok) {
            closeUserModal();
            loadUsers(currentUserPage);
        } else {
            const data = await response.json();
            alert(data.detail || '保存失败');
        }
    } catch (error) {
        alert('保存失败，请稍后重试');
    }
}

function closeUserModal() {
    document.getElementById('userModal').classList.remove('show');
    editingUser = null;
}

async function deleteUser(userId) {
    if (!confirm('确定要删除这个用户吗？')) return;
    
    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/api/users/${userId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            loadUsers(currentUserPage);
        } else {
            const data = await response.json();
            alert(data.detail || '删除失败');
        }
    } catch (error) {
        alert('删除失败，请稍后重试');
    }
}

function searchUsers() {
    const keyword = document.getElementById('userSearch').value;
    const role = document.getElementById('userRoleFilter').value;
    
    if (!keyword && !role) {
        loadUsers(1);
        return;
    }
    
    fetchUsers(keyword, role);
}

async function fetchUsers(keyword = '', role = '') {
    try {
        const token = localStorage.getItem('token');
        let url = `${API_BASE_URL}/api/users/search?page=1&page_size=10`;
        
        if (keyword) url += `&keyword=${encodeURIComponent(keyword)}`;
        if (role) url += `&role=${encodeURIComponent(role)}`;
        
        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            renderUsers(data.users);
            renderPagination(data.total_pages, data.current_page, 'users');
            currentUserPage = data.current_page;
        }
    } catch (error) {
        console.error('搜索失败:', error);
    }
}

async function loadStatistics() {
    try {
        const token = localStorage.getItem('token');
        
        const booksResponse = await fetch(`${API_BASE_URL}/api/books`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const booksData = await booksResponse.json();
        
        const usersResponse = await fetch(`${API_BASE_URL}/api/users`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const usersData = await usersResponse.json();
        
        const searchResponse = await fetch(`${API_BASE_URL}/api/books/search?status=连载`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const serializingData = await searchResponse.json();
        
        document.getElementById('statBooks').textContent = booksData.total;
        document.getElementById('statUsers').textContent = usersData.total;
        document.getElementById('statSerializing').textContent = serializingData.total;
    } catch (error) {
        console.error('加载统计数据失败:', error);
    }
}

// ========== 爬虫工具 ==========
document.addEventListener('DOMContentLoaded', function() {
    const startInput = document.getElementById('spiderPageStart');
    const endInput = document.getElementById('spiderPageEnd');
    if (startInput && endInput) {
        const updateEstimate = () => {
            const s = Math.max(1, parseInt(startInput.value) || 1);
            const e = Math.max(s, parseInt(endInput.value) || s);
            document.getElementById('spiderEstimate').textContent = (e - s + 1) * 20;
        };
        startInput.addEventListener('input', updateEstimate);
        endInput.addEventListener('input', updateEstimate);
    }
});

async function runQidianSpider() {
    const startPage = parseInt(document.getElementById('spiderPageStart').value) || 1;
    const endPage = parseInt(document.getElementById('spiderPageEnd').value) || startPage;
    const autoSave = document.getElementById('spiderAutoSave').checked;

    if (startPage < 1 || endPage < startPage || endPage > 50) {
        alert('页码范围错误：起始页≥1，结束页≤50，且结束页≥起始页');
        return;
    }

    const pages = startPage === endPage ? `${startPage}` : `${startPage}-${endPage}`;
    const statusEl = document.getElementById('spiderStatus');
    const statusText = document.getElementById('spiderStatusText');
    statusEl.style.display = 'flex';
    statusEl.className = 'spider-status loading';
    statusText.textContent = `正在爬取起点月票榜第 ${pages} 页，请稍候（含状态检测可能需要较长时间）...`;
    document.getElementById('spiderResults').style.display = 'none';

    try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${API_BASE_URL}/api/spider/qidian`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ pages, save: autoSave })
        });

        const data = await response.json();

        if (response.ok && data.success) {
            let msg = `爬取成功！共 ${data.total} 本书`;
            if (data.saved > 0) msg += `，已保存 ${data.saved} 本新书到数据库`;
            if (autoSave && data.saved === 0) msg += '（所有书籍已存在，无需重复保存）';
            statusEl.className = 'spider-status success';
            statusText.textContent = msg;
            renderQidianResults(data.books);
            document.getElementById('spiderResults').style.display = 'flex';
        } else {
            statusEl.className = 'spider-status error';
            statusText.textContent = data.detail || '爬取失败';
        }
    } catch (error) {
        statusEl.className = 'spider-status error';
        statusText.textContent = '请求失败: ' + error.message;
    }
}

function renderQidianResults(books) {
    const tbody = document.getElementById('spiderTableBody');
    tbody.innerHTML = '';
    document.getElementById('spiderCount').textContent = books.length;

    if (books.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#999;padding:30px;">无数据</td></tr>';
        return;
    }

    books.forEach(book => {
        const row = document.createElement('tr');
        const tags = book.tags ? book.tags.split(',').map(t => `<span class="table-tag">${escapeHtml(t.trim())}</span>`).join('') : '-';
        const intro = book.intro ? (book.intro.length > 40 ? escapeHtml(book.intro.substring(0, 40)) + '...' : escapeHtml(book.intro)) : '-';
        row.innerHTML = `
            <td>${book.rank}</td>
            <td><b>${escapeHtml(book.name)}</b></td>
            <td>${escapeHtml(book.author)}</td>
            <td><span class="status-badge ${book.status === '连载' ? 'serializing' : 'completed'}">${book.status}</span></td>
            <td>${tags}</td>
            <td title="${escapeHtml(book.intro || '')}">${intro}</td>
        `;
        tbody.appendChild(row);
    });
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function clearSpider() {
    document.getElementById('spiderStatus').style.display = 'none';
    document.getElementById('spiderResults').style.display = 'none';
}